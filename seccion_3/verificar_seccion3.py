"""Pruebas rapidas de coherencia para la Seccion 3.

No reemplaza un framework de testing; permite verificar en segundos que las reglas
principales siguen funcionando despues de cualquier cambio.
"""
from pathlib import Path

from generar_datos import generar_facturacion_prueba, guardar_archivo
from validar_calidad import cargar_datos, validar_datos, exportar_resultados


def main() -> None:
    base = Path(__file__).resolve().parent
    df = generar_facturacion_prueba()
    ruta = guardar_archivo(df)
    cargado = cargar_datos(ruta)
    detalle, resumen = validar_datos(cargado)

    assert len(cargado) >= 1000, "Deben generarse al menos 1.000 registros."
    assert resumen["registros_validos"] + resumen["registros_rechazados"] == len(cargado)
    assert detalle.loc[~detalle["es_valido"], "razon_rechazo"].str.len().gt(0).all()
    assert detalle.loc[detalle["es_valido"], "razon_rechazo"].eq("").all()

    validos = detalle.loc[detalle["es_valido"]]
    assert not validos.duplicated(["id_cliente", "periodo"], keep=False).any()

    # En esta verificacion omitimos Parquet para que las pruebas logicas puedan
    # ejecutarse incluso antes de instalar pyarrow. main.py si exige Parquet.
    exportar_resultados(detalle, resumen, base / "output", exportar_parquet=False)

    print("Verificacion OK")
    print(f"Registros: {len(cargado):,}")
    print(f"Validos: {resumen['registros_validos']:,}")
    print(f"Rechazados: {resumen['registros_rechazados']:,}")
    for dimension, info in resumen["score_por_dimension"].items():
        print(f"- {dimension}: {info['score_pct']:.2f}%")


if __name__ == "__main__":
    main()
