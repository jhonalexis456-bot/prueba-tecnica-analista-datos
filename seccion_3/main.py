"""Punto de entrada de la Seccion 3.

Con un solo comando:
1. Genera la facturacion sintetica.
2. Valida las cinco dimensiones de calidad.
3. Exporta el reporte JSON, validos en Parquet y rechazados en Excel.
"""

from pathlib import Path

from generar_datos import generar_facturacion_prueba, guardar_archivo
from validar_calidad import ejecutar_validacion


def main() -> None:
    base = Path(__file__).resolve().parent
    carpeta_salida = base / "output"

    df = generar_facturacion_prueba()
    ruta_entrada = guardar_archivo(df)

    _, resumen, salidas = ejecutar_validacion(
        ruta_entrada=ruta_entrada,
        carpeta_salida=carpeta_salida,
        exportar_parquet=True,
    )

    print("\nValidacion terminada correctamente.")
    print(f"Total registros: {resumen['total_registros']:,}")
    print(f"Validos: {resumen['registros_validos']:,}")
    print(f"Rechazados: {resumen['registros_rechazados']:,}")
    print("\nArchivos generados:")
    for nombre, ruta in salidas.items():
        print(f"- {nombre}: {ruta}")


if __name__ == "__main__":
    main()
