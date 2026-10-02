"""Validacion de calidad para el archivo sintetico de facturacion.

Reglas evaluadas:
1. Completitud: campos obligatorios sin nulos.
2. Validez: ID, periodo y valores numericos con formato/rango esperado.
3. Unicidad: sin duplicados por id_cliente + periodo.
4. Consistencia: trabajadores_activos > 0 cuando valor_contrato > 0.
5. Oportunidad: periodo no futuro ni con mas de 60 dias de atraso.

Salidas:
- reporte_calidad.json
- registros_validos.parquet
- registros_rechazados.xlsx
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


CAMPOS_OBLIGATORIOS = [
    "id_cliente",
    "periodo",
    "trabajadores_activos",
    "valor_contrato",
]

PATRON_ID = re.compile(r"^CLI-\d{4}$")
PATRON_PERIODO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ErrorEstructuraArchivo(ValueError):
    """Se lanza cuando el archivo no tiene las columnas requeridas."""


def cargar_datos(ruta: Path) -> pd.DataFrame:
    """Carga el CSV y valida que existan las columnas obligatorias."""
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontro el archivo de entrada: {ruta}")

    try:
        df = pd.read_csv(ruta)
    except Exception as exc:
        raise ValueError(f"No fue posible leer el archivo de facturacion: {exc}") from exc

    faltantes = [col for col in CAMPOS_OBLIGATORIOS if col not in df.columns]
    if faltantes:
        raise ErrorEstructuraArchivo(
            "Faltan columnas obligatorias: " + ", ".join(faltantes)
        )

    return df.copy()


def _es_entero_no_negativo(serie: pd.Series) -> pd.Series:
    """Valida numeros enteros mayores o iguales a cero, ignorando nulos."""
    numerico = pd.to_numeric(serie, errors="coerce")
    return numerico.notna() & (numerico >= 0) & (np.floor(numerico) == numerico)


def _es_numero_no_negativo(serie: pd.Series) -> pd.Series:
    """Valida numeros mayores o iguales a cero, ignorando nulos."""
    numerico = pd.to_numeric(serie, errors="coerce")
    return numerico.notna() & (numerico >= 0)


def _parsear_periodo_iso(serie: pd.Series) -> pd.Series:
    """Convierte exclusivamente fechas con formato YYYY-MM-DD."""
    texto = serie.astype("string")
    cumple_formato = texto.str.fullmatch(r"\d{4}-\d{2}-\d{2}", na=False)
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    if cumple_formato.any():
        resultado.loc[cumple_formato] = pd.to_datetime(
            texto.loc[cumple_formato], format="%Y-%m-%d", errors="coerce"
        )
    return resultado


def validar_datos(
    df: pd.DataFrame, fecha_corte: pd.Timestamp | None = None
) -> Tuple[pd.DataFrame, Dict[str, object]]:
    """Aplica todas las reglas y devuelve detalle por fila y resumen de calidad."""
    if fecha_corte is None:
        fecha_corte = pd.Timestamp.today().normalize()
    else:
        fecha_corte = pd.Timestamp(fecha_corte).normalize()

    trabajo = df.copy()
    total = len(trabajo)

    # --- 1. COMPLETITUD ---
    falla_completitud = trabajo[CAMPOS_OBLIGATORIOS].isna().any(axis=1)

    # --- 2. VALIDEZ ---
    # En Validez solo evaluamos valores presentes. Los nulos pertenecen a la
    # dimension de Completitud y no se penalizan dos veces.
    id_texto = trabajo["id_cliente"].astype("string")
    id_valido_no_nulo = id_texto.str.fullmatch(PATRON_ID.pattern, na=False)
    id_valido = trabajo["id_cliente"].isna() | id_valido_no_nulo

    periodo_texto = trabajo["periodo"].astype("string")
    periodo_formato_valido = periodo_texto.str.fullmatch(PATRON_PERIODO.pattern, na=False)
    periodo_parseado = _parsear_periodo_iso(trabajo["periodo"])
    periodo_valido_no_nulo = periodo_formato_valido & periodo_parseado.notna()
    periodo_valido = trabajo["periodo"].isna() | periodo_valido_no_nulo

    trabajadores_validos_no_nulos = _es_entero_no_negativo(trabajo["trabajadores_activos"])
    trabajadores_validos = trabajo["trabajadores_activos"].isna() | trabajadores_validos_no_nulos

    contrato_valido_no_nulo = _es_numero_no_negativo(trabajo["valor_contrato"])
    contrato_valido = trabajo["valor_contrato"].isna() | contrato_valido_no_nulo

    falla_validez = ~(
        id_valido & periodo_valido & trabajadores_validos & contrato_valido
    )

    # --- 3. UNICIDAD ---
    # Solo evaluamos pares con ambos campos presentes. Marcamos las dos filas del duplicado,
    # no solo la segunda, porque el par deja de ser unico en la base completa.
    par_completo = trabajo["id_cliente"].notna() & trabajo["periodo"].notna()
    duplicado = pd.Series(False, index=trabajo.index)
    duplicado.loc[par_completo] = trabajo.loc[par_completo].duplicated(
        subset=["id_cliente", "periodo"], keep=False
    )
    falla_unicidad = duplicado

    # --- 4. CONSISTENCIA ---
    trabajadores_num = pd.to_numeric(trabajo["trabajadores_activos"], errors="coerce")
    contrato_num = pd.to_numeric(trabajo["valor_contrato"], errors="coerce")
    evaluable_consistencia = trabajadores_num.notna() & contrato_num.notna()
    falla_consistencia = (
        evaluable_consistencia & (contrato_num > 0) & (trabajadores_num <= 0)
    )

    # --- 5. OPORTUNIDAD ---
    # Si el periodo ni siquiera tiene formato valido, el problema se reporta en Validez.
    # Oportunidad se concentra en fechas validas pero fuera de la ventana permitida.
    dias_atraso = (fecha_corte - periodo_parseado).dt.days
    periodo_futuro = periodo_parseado.notna() & (periodo_parseado > fecha_corte)
    periodo_atrasado = periodo_parseado.notna() & (dias_atraso > 60)
    falla_oportunidad = periodo_futuro | periodo_atrasado

    trabajo["falla_completitud"] = falla_completitud
    trabajo["falla_validez"] = falla_validez
    trabajo["falla_unicidad"] = falla_unicidad
    trabajo["falla_consistencia"] = falla_consistencia
    trabajo["falla_oportunidad"] = falla_oportunidad

    columnas_fallas = [
        "falla_completitud",
        "falla_validez",
        "falla_unicidad",
        "falla_consistencia",
        "falla_oportunidad",
    ]
    trabajo["es_valido"] = ~trabajo[columnas_fallas].any(axis=1)

    razones: List[str] = []
    for idx, fila in trabajo.iterrows():
        motivos: List[str] = []

        if fila["falla_completitud"]:
            faltantes = [
                campo for campo in CAMPOS_OBLIGATORIOS if pd.isna(fila[campo])
            ]
            motivos.append("Completitud: faltan " + ", ".join(faltantes))

        if fila["falla_validez"]:
            detalles = []
            if pd.notna(fila["id_cliente"]) and not id_valido_no_nulo.loc[idx]:
                detalles.append("id_cliente debe cumplir CLI-0000")
            if pd.notna(fila["periodo"]) and not periodo_valido_no_nulo.loc[idx]:
                detalles.append("periodo debe ser una fecha valida YYYY-MM-DD")
            if pd.notna(fila["trabajadores_activos"]) and not trabajadores_validos_no_nulos.loc[idx]:
                detalles.append("trabajadores_activos debe ser entero >= 0")
            if pd.notna(fila["valor_contrato"]) and not contrato_valido_no_nulo.loc[idx]:
                detalles.append("valor_contrato debe ser >= 0")
            if detalles:
                motivos.append("Validez: " + "; ".join(detalles))

        if fila["falla_unicidad"]:
            motivos.append("Unicidad: id_cliente + periodo esta duplicado")

        if fila["falla_consistencia"]:
            motivos.append(
                "Consistencia: si valor_contrato > 0, trabajadores_activos debe ser > 0"
            )

        if fila["falla_oportunidad"]:
            if periodo_futuro.loc[idx]:
                motivos.append("Oportunidad: el periodo esta en el futuro")
            elif periodo_atrasado.loc[idx]:
                motivos.append("Oportunidad: el periodo tiene mas de 60 dias de atraso")

        razones.append(" | ".join(motivos))

    trabajo["razon_rechazo"] = razones

    fallas_por_dimension = {
        "completitud": int(falla_completitud.sum()),
        "validez": int(falla_validez.sum()),
        "unicidad": int(falla_unicidad.sum()),
        "consistencia": int(falla_consistencia.sum()),
        "oportunidad": int(falla_oportunidad.sum()),
    }

    def score(fallas: int) -> float:
        if total == 0:
            return 0.0
        return round((1 - fallas / total) * 100, 2)

    validos = int(trabajo["es_valido"].sum())
    rechazados = int((~trabajo["es_valido"]).sum())

    resumen = {
        "fecha_ejecucion": fecha_corte.strftime("%Y-%m-%d"),
        "total_registros": int(total),
        "registros_validos": validos,
        "registros_rechazados": rechazados,
        "porcentaje_validos": round(validos / total * 100, 2) if total else 0.0,
        "score_por_dimension": {
            dimension: {
                "score_pct": score(cantidad),
                "registros_que_fallan": cantidad,
            }
            for dimension, cantidad in fallas_por_dimension.items()
        },
        "rechazados_por_regla": fallas_por_dimension,
        "criterios_aplicados": {
            "completitud": "id_cliente, periodo, trabajadores_activos y valor_contrato son obligatorios",
            "validez": "id_cliente debe cumplir CLI-0000; periodo debe ser YYYY-MM-DD; trabajadores_activos debe ser entero >= 0; valor_contrato debe ser >= 0",
            "unicidad": "no puede repetirse la combinacion id_cliente + periodo",
            "consistencia": "si valor_contrato > 0, trabajadores_activos debe ser > 0",
            "oportunidad": "periodo no puede estar en el futuro ni tener mas de 60 dias de atraso",
        },
        "nota": (
            "Un registro puede fallar mas de una regla; por eso la suma de rechazos "
            "por dimension puede superar el total de registros rechazados."
        ),
    }

    return trabajo, resumen


def _estilizar_excel_rechazados(ruta_excel: Path) -> None:
    """Aplica formato simple y legible al Excel de rechazados."""
    wb = load_workbook(ruta_excel)
    ws = wb["rechazados"]

    encabezado = PatternFill("solid", fgColor="1F4E78")
    error_fill = PatternFill("solid", fgColor="FCE8E6")
    static_fill = PatternFill("solid", fgColor="E7E6E6")

    for celda in ws[1]:
        celda.fill = encabezado
        celda.font = Font(color="FFFFFF", bold=True)
        celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    ws.sheet_view.showGridLines = False

    # Coloreamos banderas y motivo para facilitar la revision visual.
    encabezados = {celda.value: celda.column for celda in ws[1]}
    for nombre in [
        "falla_completitud",
        "falla_validez",
        "falla_unicidad",
        "falla_consistencia",
        "falla_oportunidad",
    ]:
        col = encabezados.get(nombre)
        if col:
            for fila in range(2, ws.max_row + 1):
                celda = ws.cell(fila, col)
                celda.fill = error_fill if celda.value else static_fill
                celda.alignment = Alignment(horizontal="center")

    col_razon = encabezados.get("razon_rechazo")
    if col_razon:
        for fila in range(2, ws.max_row + 1):
            celda = ws.cell(fila, col_razon)
            celda.fill = error_fill
            celda.alignment = Alignment(wrap_text=True, vertical="top")

    # Anchos pensados para lectura inmediata sin hacer la hoja excesivamente ancha.
    anchos = {
        "id_cliente": 16,
        "periodo": 16,
        "trabajadores_activos": 22,
        "valor_contrato": 18,
        "falla_completitud": 20,
        "falla_validez": 16,
        "falla_unicidad": 17,
        "falla_consistencia": 21,
        "falla_oportunidad": 20,
        "es_valido": 12,
        "razon_rechazo": 85,
    }
    for nombre, ancho in anchos.items():
        col = encabezados.get(nombre)
        if col:
            ws.column_dimensions[get_column_letter(col)].width = ancho

    for fila in range(2, ws.max_row + 1):
        ws.row_dimensions[fila].height = 30

    # Formato numerico de valor de contrato.
    col_valor = encabezados.get("valor_contrato")
    if col_valor:
        for fila in range(2, ws.max_row + 1):
            ws.cell(fila, col_valor).number_format = '#,##0.00;[Red](#,##0.00)'

    wb.save(ruta_excel)


def exportar_resultados(
    detalle: pd.DataFrame,
    resumen: Dict[str, object],
    carpeta_salida: Path,
    exportar_parquet: bool = True,
) -> Dict[str, Path]:
    """Exporta JSON, Excel de rechazados y Parquet de validos."""
    carpeta_salida.mkdir(parents=True, exist_ok=True)

    ruta_json = carpeta_salida / "reporte_calidad.json"
    ruta_excel = carpeta_salida / "registros_rechazados.xlsx"
    ruta_parquet = carpeta_salida / "registros_validos.parquet"

    with ruta_json.open("w", encoding="utf-8") as archivo:
        json.dump(resumen, archivo, ensure_ascii=False, indent=2)

    columnas_originales = CAMPOS_OBLIGATORIOS
    columnas_control = [
        "falla_completitud",
        "falla_validez",
        "falla_unicidad",
        "falla_consistencia",
        "falla_oportunidad",
        "es_valido",
        "razon_rechazo",
    ]

    rechazados = detalle.loc[~detalle["es_valido"], columnas_originales + columnas_control].copy()
    rechazados.to_excel(ruta_excel, index=False, sheet_name="rechazados", engine="openpyxl")
    _estilizar_excel_rechazados(ruta_excel)

    if exportar_parquet:
        validos = detalle.loc[detalle["es_valido"], columnas_originales].copy()
        try:
            validos.to_parquet(ruta_parquet, index=False, engine="pyarrow")
        except ImportError as exc:
            raise RuntimeError(
                "No se pudo crear el Parquet porque falta pyarrow. "
                "Ejecute: pip install -r requirements.txt"
            ) from exc

    salidas = {"json": ruta_json, "excel": ruta_excel}
    if exportar_parquet:
        salidas["parquet"] = ruta_parquet
    return salidas


def ejecutar_validacion(
    ruta_entrada: Path,
    carpeta_salida: Path,
    exportar_parquet: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, object], Dict[str, Path]]:
    """Orquesta carga, validacion y exportacion."""
    df = cargar_datos(ruta_entrada)
    detalle, resumen = validar_datos(df)
    salidas = exportar_resultados(
        detalle,
        resumen,
        carpeta_salida,
        exportar_parquet=exportar_parquet,
    )
    return detalle, resumen, salidas
