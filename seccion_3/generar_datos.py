"""
Generador de datos sintéticos para la Sección 3 de la prueba técnica.

Objetivo:
- Crear 1.000+ registros de facturación.
- Incluir errores intencionales para probar posteriormente las reglas de calidad.
- Guardar el archivo generado en datos/facturacion_prueba.csv.

El script usa una semilla fija para que el resultado sea reproducible.
"""

from pathlib import Path
import numpy as np
import pandas as pd


SEMILLA = 42
N_REGISTROS_BASE = 1200


def _formatear_periodo(fecha: pd.Timestamp, formato: str) -> str:
    """Devuelve la misma fecha en distintos formatos de texto."""
    if formato == "iso":
        return fecha.strftime("%Y-%m-%d")
    if formato == "latino":
        return fecha.strftime("%d/%m/%Y")
    if formato == "slash":
        return fecha.strftime("%Y/%m/%d")
    if formato == "compacto":
        return fecha.strftime("%Y%m%d")
    return fecha.strftime("%Y-%m-%d")


def generar_facturacion_prueba(n_registros: int = N_REGISTROS_BASE) -> pd.DataFrame:
    """
    Genera una base sintética de facturación con errores controlados.

    Errores incluidos:
    - IDs con formatos inconsistentes.
    - Períodos escritos en distintos formatos.
    - Nulos en campos críticos.
    - Valores negativos.
    - Casos inconsistentes: contrato > 0 con trabajadores = 0.
    - Períodos futuros.
    - Períodos con más de 60 días de atraso.
    - Duplicados por id_cliente + periodo.
    """
    rng = np.random.default_rng(SEMILLA)
    hoy = pd.Timestamp.today().normalize()
    inicio_mes = hoy.replace(day=1)
    mes_anterior = inicio_mes - pd.offsets.MonthBegin(1)

    # Creamos clientes y asignamos principalmente períodos recientes.
    ids = [f"CLI-{i:04d}" for i in range(1, n_registros + 1)]
    periodos_fecha = rng.choice(
        [inicio_mes, mes_anterior],
        size=n_registros,
        replace=True,
        p=[0.55, 0.45],
    )

    # La mayoría queda en ISO, pero algunos períodos se escriben en otros formatos
    # para simular archivos recibidos desde diferentes fuentes.
    formatos = rng.choice(
        ["iso", "latino", "slash", "compacto"],
        size=n_registros,
        replace=True,
        p=[0.82, 0.07, 0.06, 0.05],
    )
    periodos = [
        _formatear_periodo(pd.Timestamp(fecha), formato)
        for fecha, formato in zip(periodos_fecha, formatos)
    ]

    trabajadores = rng.integers(1, 501, size=n_registros).astype(float)
    valor_contrato = rng.integers(500_000, 25_000_001, size=n_registros).astype(float)

    df = pd.DataFrame(
        {
            "id_cliente": ids,
            "periodo": periodos,
            "trabajadores_activos": trabajadores,
            "valor_contrato": valor_contrato,
        }
    )

    # Elegimos grupos de filas diferentes para que cada error sea fácil de rastrear.
    indices = rng.permutation(n_registros)
    cursor = 0

    def tomar(cantidad: int):
        nonlocal cursor
        seleccion = indices[cursor: cursor + cantidad]
        cursor += cantidad
        return seleccion

    # 1) IDs con formato inconsistente.
    idx_ids = tomar(32)
    for pos, idx in enumerate(idx_ids):
        valor = str(df.loc[idx, "id_cliente"])
        variante = pos % 4
        if variante == 0:
            df.loc[idx, "id_cliente"] = valor.lower()
        elif variante == 1:
            df.loc[idx, "id_cliente"] = valor.replace("-", "_")
        elif variante == 2:
            df.loc[idx, "id_cliente"] = valor.replace("CLI-", "")
        else:
            df.loc[idx, "id_cliente"] = f" {valor} "

    # 2) Nulos en campos críticos.
    idx_nulos_id = tomar(12)
    idx_nulos_periodo = tomar(12)
    idx_nulos_trab = tomar(12)
    idx_nulos_valor = tomar(12)
    df.loc[idx_nulos_id, "id_cliente"] = None
    df.loc[idx_nulos_periodo, "periodo"] = None
    df.loc[idx_nulos_trab, "trabajadores_activos"] = np.nan
    df.loc[idx_nulos_valor, "valor_contrato"] = np.nan

    # 3) Valores negativos.
    idx_neg_trab = tomar(18)
    idx_neg_valor = tomar(18)
    df.loc[idx_neg_trab, "trabajadores_activos"] *= -1
    df.loc[idx_neg_valor, "valor_contrato"] *= -1

    # 4) Inconsistencia: hay contrato, pero no hay trabajadores activos.
    idx_inconsistentes = tomar(20)
    df.loc[idx_inconsistentes, "trabajadores_activos"] = 0
    df.loc[idx_inconsistentes, "valor_contrato"] = rng.integers(
        500_000, 10_000_001, size=len(idx_inconsistentes)
    )

    # 5) Períodos futuros.
    idx_futuros = tomar(18)
    fechas_futuras = hoy + pd.to_timedelta(
        rng.integers(1, 91, size=len(idx_futuros)), unit="D"
    )
    for idx, fecha in zip(idx_futuros, fechas_futuras):
        df.loc[idx, "periodo"] = pd.Timestamp(fecha).strftime("%Y-%m-%d")

    # 6) Períodos con más de 60 días de atraso.
    idx_atrasados = tomar(18)
    fechas_atrasadas = hoy - pd.to_timedelta(
        rng.integers(61, 181, size=len(idx_atrasados)), unit="D"
    )
    for idx, fecha in zip(idx_atrasados, fechas_atrasadas):
        df.loc[idx, "periodo"] = pd.Timestamp(fecha).strftime("%Y-%m-%d")

    # 7) Duplicados exactos por id_cliente + periodo.
    # Se agregan al final para superar los 1.200 registros base.
    candidatos = df[
        df["id_cliente"].notna() & df["periodo"].notna()
    ].sample(n=30, random_state=SEMILLA)

    df = pd.concat([df, candidatos.copy()], ignore_index=True)

    return df


def guardar_archivo(df: pd.DataFrame) -> Path:
    """Guarda el archivo generado dentro de la carpeta datos."""
    ruta_salida = Path(__file__).resolve().parent / "datos" / "facturacion_prueba.csv"
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta_salida, index=False, encoding="utf-8-sig")
    return ruta_salida


def main():
    df = generar_facturacion_prueba()
    ruta = guardar_archivo(df)

    print("Archivo de prueba generado correctamente.")
    print(f"Registros generados: {len(df):,}")
    print(f"Columnas: {', '.join(df.columns)}")
    print(f"Ruta: {ruta}")


if __name__ == "__main__":
    main()
