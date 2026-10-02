"""Dashboard ligero de monitoreo operativo.

La aplicación genera sus propios datos sintéticos en memoria y no depende de
archivos externos. Está pensada para ejecutarse con Streamlit y Plotly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


SEMILLA = 42
N_CLIENTES = 60
N_MESES = 14


@dataclass(frozen=True)
class Periodos:
    """Fechas de referencia utilizadas por el tablero."""

    actual: pd.Timestamp
    anterior: pd.Timestamp
    visibles: list[pd.Timestamp]


# -----------------------------------------------------------------------------
# CONFIGURACIÓN Y ESTILO
# -----------------------------------------------------------------------------

def configurar_pagina() -> None:
    """Configura la página y aplica un estilo ejecutivo y limpio."""
    st.set_page_config(
        page_title="Monitoreo Operativo",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """
        <style>
        .stApp { background: #F4F7FB; }
        .block-container { padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1500px; }
        [data-testid="stSidebar"] { background: #0F172A; }
        [data-testid="stSidebar"] * { color: #E2E8F0; }
        [data-testid="stSidebar"] label { color: #CBD5E1 !important; }
        [data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
            background: #172033;
            border-color: #334155;
        }
        .hero {
            background: linear-gradient(120deg, #0F172A 0%, #1E3A8A 58%, #2563EB 100%);
            border-radius: 22px;
            padding: 25px 28px;
            color: white;
            margin-bottom: 18px;
            box-shadow: 0 12px 35px rgba(15, 23, 42, 0.14);
        }
        .hero h1 { margin: 0; font-size: 2rem; font-weight: 750; letter-spacing: -0.02em; }
        .hero p { margin: 7px 0 0 0; color: #DBEAFE; font-size: 0.98rem; }
        .kpi-card {
            background: white;
            border: 1px solid #E2E8F0;
            border-radius: 18px;
            padding: 18px 20px 16px 20px;
            min-height: 132px;
            box-shadow: 0 7px 22px rgba(15, 23, 42, 0.055);
        }
        .kpi-label { color: #64748B; font-size: 0.82rem; font-weight: 700; text-transform: uppercase; letter-spacing: .055em; }
        .kpi-value { color: #0F172A; font-size: 2.0rem; font-weight: 780; line-height: 1.2; margin-top: 8px; }
        .kpi-delta-up { color: #B91C1C; font-size: .86rem; font-weight: 650; margin-top: 7px; }
        .kpi-delta-down { color: #047857; font-size: .86rem; font-weight: 650; margin-top: 7px; }
        .kpi-delta-flat { color: #475569; font-size: .86rem; font-weight: 650; margin-top: 7px; }
        .section-title { color: #0F172A; font-size: 1.12rem; font-weight: 760; margin: 4px 0 0 0; }
        .section-subtitle { color: #64748B; font-size: .88rem; margin-bottom: 8px; }
        .insight-box {
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-left: 5px solid #2563EB;
            border-radius: 14px;
            padding: 16px 18px;
            color: #1E293B;
            margin: 7px 0 17px 0;
        }
        .insight-title { font-weight: 760; color: #1E3A8A; margin-bottom: 5px; }
        .small-note { color: #64748B; font-size: .78rem; }
        div[data-testid="stDataFrame"] { border: 1px solid #E2E8F0; border-radius: 14px; overflow: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# DATOS SINTÉTICOS
# -----------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def generar_datos() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Genera clientes, trabajadores mensuales y casos de forma reproducible."""
    rng = np.random.default_rng(SEMILLA)

    sectores = np.array(["Servicios", "Industria", "Comercio", "Logística", "Tecnología"])
    nombres_base = [
        "Andina", "Horizonte", "Nexo", "Orion", "Vértice", "Nova", "Integral", "Sigma",
        "Punto", "Alianza", "Central", "Dinámica", "Avanza", "Atlas", "Soluciones",
    ]

    clientes = []
    for i in range(1, N_CLIENTES + 1):
        riesgo = int(rng.choice([1, 2, 3, 4, 5], p=[0.14, 0.20, 0.28, 0.23, 0.15]))
        sector = str(rng.choice(sectores))
        nombre = f"{nombres_base[(i - 1) % len(nombres_base)]} {i:02d}"
        clientes.append(
            {
                "id_cliente": f"CLI-{i:03d}",
                "nombre": nombre,
                "sector": sector,
                "clase_riesgo": riesgo,
                "estado": "activo",
            }
        )
    df_clientes = pd.DataFrame(clientes)

    # Fecha de corte fija para que la prueba sea totalmente reproducible.
    mes_actual = pd.Timestamp("2026-09-01")
    meses = list(pd.date_range(end=mes_actual, periods=N_MESES, freq="MS"))

    trabajadores = []
    casos = []
    id_caso = 1

    for _, cliente in df_clientes.iterrows():
        base_trabajadores = int(rng.integers(55, 900))
        crecimiento = rng.normal(0.003, 0.012)

        for idx_mes, periodo in enumerate(meses):
            estacionalidad = 1 + 0.025 * np.sin(idx_mes / 2.1)
            ruido_trab = rng.normal(0, 0.025)
            activos = max(
                10,
                int(base_trabajadores * ((1 + crecimiento) ** idx_mes) * estacionalidad * (1 + ruido_trab)),
            )
            trabajadores.append(
                {
                    "id_cliente": cliente["id_cliente"],
                    "periodo": periodo,
                    "trabajadores_activos": activos,
                }
            )

            # La frecuencia de casos depende del tamaño y la clase de riesgo.
            factor_riesgo = {1: 0.45, 2: 0.62, 3: 0.82, 4: 1.12, 5: 1.45}[int(cliente["clase_riesgo"])]
            lambda_casos = max(0.12, activos / 150 * factor_riesgo)
            n_casos = int(rng.poisson(lambda_casos))

            for _ in range(n_casos):
                prob_grave = min(0.08 + 0.045 * int(cliente["clase_riesgo"]), 0.34)
                tipo = "grave" if rng.random() < prob_grave else "leve"
                if tipo == "grave":
                    dias_ausencia = int(rng.integers(8, 41))
                    costo = float(rng.lognormal(mean=15.55, sigma=0.48))
                else:
                    dias_ausencia = int(rng.integers(0, 9))
                    costo = float(rng.lognormal(mean=13.85, sigma=0.52))

                casos.append(
                    {
                        "id_caso": f"CAS-{id_caso:05d}",
                        "id_cliente": cliente["id_cliente"],
                        "fecha_ocurrencia": periodo + pd.Timedelta(days=int(rng.integers(0, 27))),
                        "periodo": periodo,
                        "tipo": tipo,
                        "dias_ausencia": dias_ausencia,
                        "costo": round(costo, 2),
                        "estado": str(rng.choice(["abierto", "cerrado"], p=[0.19, 0.81])),
                    }
                )
                id_caso += 1

    return df_clientes, pd.DataFrame(trabajadores), pd.DataFrame(casos)


def obtener_periodos(df_trabajadores: pd.DataFrame) -> Periodos:
    """Determina mes actual, mes anterior y ventana visible de 12 meses."""
    actual = pd.Timestamp(df_trabajadores["periodo"].max())
    anterior = actual - pd.offsets.MonthBegin(1)
    visibles = list(pd.date_range(end=actual, periods=12, freq="MS"))
    return Periodos(actual=actual, anterior=anterior, visibles=visibles)


# -----------------------------------------------------------------------------
# FILTROS Y CÁLCULOS
# -----------------------------------------------------------------------------

def aplicar_filtros(
    clientes: pd.DataFrame,
    trabajadores: pd.DataFrame,
    casos: pd.DataFrame,
    sectores: Iterable[str],
    riesgos: Iterable[int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Aplica los filtros de negocio a todas las tablas del tablero."""
    sectores = list(sectores)
    riesgos = list(riesgos)

    clientes_f = clientes[
        clientes["sector"].isin(sectores) & clientes["clase_riesgo"].isin(riesgos)
    ].copy()
    ids = clientes_f["id_cliente"]

    trabajadores_f = trabajadores[trabajadores["id_cliente"].isin(ids)].copy()
    casos_f = casos[casos["id_cliente"].isin(ids)].copy()
    return clientes_f, trabajadores_f, casos_f


def resumen_periodo(
    casos: pd.DataFrame,
    trabajadores: pd.DataFrame,
    periodo: pd.Timestamp,
) -> dict[str, float]:
    """Calcula los tres KPI exigidos para un período."""
    casos_mes = casos[casos["periodo"] == periodo]
    trabajadores_mes = trabajadores[trabajadores["periodo"] == periodo]

    total_casos = int(len(casos_mes))
    costo_total = float(casos_mes["costo"].sum()) if total_casos else 0.0
    total_trabajadores = int(trabajadores_mes["trabajadores_activos"].sum())
    tasa = (total_casos / total_trabajadores * 100) if total_trabajadores else 0.0

    return {
        "casos": total_casos,
        "costo": costo_total,
        "trabajadores": total_trabajadores,
        "tasa": tasa,
    }


def variacion(actual: float, anterior: float) -> float | None:
    """Calcula la variación porcentual y evita divisiones entre cero."""
    if anterior == 0:
        return None
    return (actual - anterior) / anterior * 100


def formato_compacto_moneda(valor: float) -> str:
    """Formatea cantidades monetarias sin asumir una moneda específica."""
    if abs(valor) >= 1_000_000_000:
        return f"$ {valor / 1_000_000_000:,.1f} B"
    if abs(valor) >= 1_000_000:
        return f"$ {valor / 1_000_000:,.1f} M"
    if abs(valor) >= 1_000:
        return f"$ {valor / 1_000:,.1f} K"
    return f"$ {valor:,.0f}"


def construir_serie_mensual(
    casos: pd.DataFrame,
    trabajadores: pd.DataFrame,
    periodos: list[pd.Timestamp],
) -> pd.DataFrame:
    """Crea la serie de 12 meses para casos, costo e incidencia."""
    filas = []
    for periodo in periodos:
        kpi = resumen_periodo(casos, trabajadores, periodo)
        filas.append(
            {
                "periodo": periodo,
                "casos": kpi["casos"],
                "costo": kpi["costo"],
                "tasa": kpi["tasa"],
            }
        )
    return pd.DataFrame(filas)


# -----------------------------------------------------------------------------
# COMPONENTES VISUALES
# -----------------------------------------------------------------------------

def tarjeta_kpi(titulo: str, valor: str, delta: float | None, contexto: str) -> None:
    """Dibuja una tarjeta KPI con variación respecto al período anterior."""
    if delta is None:
        clase, texto_delta = "kpi-delta-flat", "Sin base comparable"
    elif abs(delta) < 0.05:
        clase, texto_delta = "kpi-delta-flat", "≈ 0,0 % vs mes anterior"
    elif delta > 0:
        clase, texto_delta = "kpi-delta-up", f"▲ {abs(delta):.1f} % vs mes anterior"
    else:
        clase, texto_delta = "kpi-delta-down", f"▼ {abs(delta):.1f} % vs mes anterior"

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="{clase}">{texto_delta}</div>
            <div class="small-note">{contexto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def estilo_figura(fig: go.Figure, altura: int = 340) -> go.Figure:
    """Aplica una apariencia homogénea a los gráficos."""
    fig.update_layout(
        height=altura,
        margin=dict(l=14, r=14, t=45, b=15),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", color="#334155", size=12),
        legend_title_text="",
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E2E8F0")
    fig.update_yaxes(gridcolor="#E8EEF6", zeroline=False)
    return fig


def grafico_tendencia(serie: pd.DataFrame) -> go.Figure:
    """Gráfico de tendencia mensual con referencia del promedio histórico."""
    promedio = float(serie["casos"].mean()) if not serie.empty else 0.0

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=serie["periodo"],
            y=serie["casos"],
            mode="lines+markers",
            name="Casos",
            line=dict(color="#2563EB", width=3),
            marker=dict(size=7, color="#2563EB"),
            hovertemplate="%{x|%b %Y}<br><b>%{y} casos</b><extra></extra>",
        )
    )
    fig.add_hline(
        y=promedio,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Promedio 12 meses: {promedio:.1f}",
        annotation_position="top left",
        annotation_font_color="#92400E",
    )
    fig.update_layout(title=dict(text="Evolución mensual de casos", font=dict(size=16, color="#0F172A")))
    fig.update_yaxes(title="Casos", rangemode="tozero")
    fig.update_xaxes(title=None, tickformat="%b\n%Y")
    return estilo_figura(fig, 365)


def grafico_tipo(casos_mes: pd.DataFrame) -> go.Figure:
    """Distribución de casos leves y graves."""
    dist = (
        casos_mes.groupby("tipo", as_index=False)
        .size()
        .rename(columns={"size": "casos"})
    )
    fig = px.pie(
        dist,
        names="tipo",
        values="casos",
        hole=0.62,
        color="tipo",
        color_discrete_map={"leve": "#38BDF8", "grave": "#F97316"},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}: %{value} casos<extra></extra>")
    fig.update_layout(title=dict(text="Casos por tipo", font=dict(size=16, color="#0F172A")))
    return estilo_figura(fig, 330)


def grafico_riesgo(casos_mes: pd.DataFrame, clientes: pd.DataFrame) -> go.Figure:
    """Distribución del volumen de casos por clase de riesgo."""
    base = casos_mes.merge(clientes[["id_cliente", "clase_riesgo"]], on="id_cliente", how="left")
    dist = base.groupby("clase_riesgo", as_index=False).size().rename(columns={"size": "casos"})
    niveles = sorted(clientes["clase_riesgo"].dropna().astype(int).unique().tolist())
    universo = pd.DataFrame({"clase_riesgo": niveles})
    dist = universo.merge(dist, on="clase_riesgo", how="left").fillna({"casos": 0})

    fig = px.bar(
        dist,
        x="clase_riesgo",
        y="casos",
        text="casos",
        color="clase_riesgo",
        color_continuous_scale=["#BAE6FD", "#60A5FA", "#2563EB", "#F59E0B", "#EF4444"],
    )
    fig.update_traces(textposition="outside", hovertemplate="Riesgo %{x}<br><b>%{y} casos</b><extra></extra>")
    fig.update_coloraxes(showscale=False)
    fig.update_layout(title=dict(text="Casos por clase de riesgo", font=dict(size=16, color="#0F172A")))
    fig.update_xaxes(title="Clase de riesgo", dtick=1)
    fig.update_yaxes(title="Casos", rangemode="tozero")
    return estilo_figura(fig, 330)


def top_clientes(casos_mes: pd.DataFrame, clientes: pd.DataFrame) -> pd.DataFrame:
    """Construye el ranking mensual de los 10 clientes con más casos."""
    resumen = (
        casos_mes.groupby("id_cliente", as_index=False)
        .agg(casos=("id_caso", "count"), costo=("costo", "sum"))
        .merge(clientes[["id_cliente", "nombre", "sector", "clase_riesgo"]], on="id_cliente", how="left")
        .sort_values(["casos", "costo"], ascending=[False, False])
        .head(10)
    )
    resumen.insert(0, "posición", range(1, len(resumen) + 1))
    return resumen[["posición", "nombre", "sector", "clase_riesgo", "casos", "costo"]]


def lectura_ejecutiva(
    casos_mes: pd.DataFrame,
    clientes: pd.DataFrame,
    actual: dict[str, float],
    anterior: dict[str, float],
) -> str:
    """Genera una lectura corta para orientar la decisión del usuario."""
    if casos_mes.empty:
        return "No hay casos para la selección actual. Revise o amplíe los filtros para analizar otro segmento."

    ranking = top_clientes(casos_mes, clientes)
    lider = ranking.iloc[0]
    total = max(int(actual["casos"]), 1)
    concentracion_lider = float(lider["casos"] / total * 100)
    graves = int((casos_mes["tipo"] == "grave").sum())
    pct_graves = graves / total * 100
    var_tasa = variacion(actual["tasa"], anterior["tasa"])

    if var_tasa is None:
        tendencia = "no tiene una base comparable"
    elif var_tasa > 1:
        tendencia = f"subió {var_tasa:.1f}% frente al mes anterior"
    elif var_tasa < -1:
        tendencia = f"bajó {abs(var_tasa):.1f}% frente al mes anterior"
    else:
        tendencia = "se mantuvo estable frente al mes anterior"

    return (
        f"La tasa de incidencia {tendencia}. "
        f"{lider['nombre']} concentra {concentracion_lider:.1f}% de los casos del mes "
        f"y los casos graves representan {pct_graves:.1f}% del total. "
        "La prioridad operativa debe contrastar concentración, gravedad y clase de riesgo antes de programar acciones."
    )


# -----------------------------------------------------------------------------
# APLICACIÓN
# -----------------------------------------------------------------------------

def main() -> None:
    """Construye el dashboard completo."""
    configurar_pagina()
    clientes, trabajadores, casos = generar_datos()
    periodos = obtener_periodos(trabajadores)

    # Barra lateral
    st.sidebar.markdown("### Filtros de análisis")
    st.sidebar.caption("Todos los componentes del tablero responden a estos filtros.")

    opciones_sector = sorted(clientes["sector"].unique().tolist())
    sectores = st.sidebar.multiselect(
        "Sector",
        opciones_sector,
        default=opciones_sector,
    )
    riesgos = st.sidebar.multiselect(
        "Clase de riesgo",
        [1, 2, 3, 4, 5],
        default=[1, 2, 3, 4, 5],
    )

    if not sectores or not riesgos:
        st.warning("Seleccione al menos un sector y una clase de riesgo para visualizar resultados.")
        st.stop()

    clientes_f, trabajadores_f, casos_f = aplicar_filtros(clientes, trabajadores, casos, sectores, riesgos)
    actual = resumen_periodo(casos_f, trabajadores_f, periodos.actual)
    anterior = resumen_periodo(casos_f, trabajadores_f, periodos.anterior)
    casos_mes = casos_f[casos_f["periodo"] == periodos.actual].copy()

    meses_es = {1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril', 5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto', 9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'}
    etiqueta_corte = f"{meses_es[periodos.actual.month]} {periodos.actual.year}"

    st.markdown(
        f"""
        <div class="hero">
            <h1>Monitoreo Operativo</h1>
            <p>Vista ejecutiva para priorizar atención a clientes · Corte {etiqueta_corte}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPI principales
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        tarjeta_kpi(
            "Casos del mes",
            f"{int(actual['casos']):,}",
            variacion(actual["casos"], anterior["casos"]),
            f"{len(clientes_f):,} clientes en el alcance",
        )
    with c2:
        tarjeta_kpi(
            "Costo total",
            formato_compacto_moneda(actual["costo"]),
            variacion(actual["costo"], anterior["costo"]),
            "Costo asociado a los casos del período",
        )
    with c3:
        tarjeta_kpi(
            "Tasa de incidencia",
            f"{actual['tasa']:.2f}",
            variacion(actual["tasa"], anterior["tasa"]),
            "Casos por cada 100 trabajadores activos",
        )

    st.markdown(
        f"""
        <div class="insight-box">
            <div class="insight-title">Lectura ejecutiva</div>
            {lectura_ejecutiva(casos_mes, clientes_f, actual, anterior)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tendencia
    st.markdown('<div class="section-title">¿Cómo viene evolucionando la operación?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Tendencia de los últimos 12 meses y referencia del promedio histórico del período.</div>', unsafe_allow_html=True)
    serie = construir_serie_mensual(casos_f, trabajadores_f, periodos.visibles)
    st.plotly_chart(grafico_tendencia(serie), use_container_width=True, config={"displayModeBar": False})

    # Distribuciones
    st.markdown('<div class="section-title">¿Dónde está concentrado el riesgo?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Composición de los casos del mes por severidad y clase de riesgo.</div>', unsafe_allow_html=True)
    g1, g2 = st.columns(2, gap="medium")
    with g1:
        st.plotly_chart(grafico_tipo(casos_mes), use_container_width=True, config={"displayModeBar": False})
    with g2:
        st.plotly_chart(grafico_riesgo(casos_mes, clientes_f), use_container_width=True, config={"displayModeBar": False})

    # Top 10
    st.markdown('<div class="section-title">¿Qué clientes requieren revisión primero?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Top 10 del mes ordenado por número de casos; el costo se usa como desempate.</div>', unsafe_allow_html=True)
    ranking = top_clientes(casos_mes, clientes_f)

    if ranking.empty:
        st.info("No hay clientes con casos para la selección actual.")
    else:
        tabla = ranking.rename(
            columns={
                "posición": "#",
                "nombre": "Cliente",
                "sector": "Sector",
                "clase_riesgo": "Riesgo",
                "casos": "Casos",
                "costo": "Costo ($M)",
            }
        ).copy()

        # Mostrar el costo en millones permite que las seis columnas quepan
        # cómodamente sin obligar al usuario a desplazarse horizontalmente.
        tabla["Costo ($M)"] = tabla["Costo ($M)"] / 1_000_000

        # El alto se calcula para mostrar las 10 filas completas más el encabezado,
        # evitando un scroll vertical innecesario en la vista ejecutiva.
        alto_tabla = 39 * (len(tabla) + 1)

        st.dataframe(
            tabla,
            hide_index=True,
            use_container_width=True,
            height=alto_tabla,
            row_height=34,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
                "Sector": st.column_config.TextColumn("Sector", width="medium"),
                "Riesgo": st.column_config.NumberColumn("Riesgo", width="small"),
                "Casos": st.column_config.NumberColumn("Casos", width="small"),
                "Costo ($M)": st.column_config.NumberColumn(
                    "Costo ($M)",
                    format="$ %.1f M",
                    width="small",
                ),
            },
        )

    st.caption(
        "Datos sintéticos generados dentro de la aplicación. "
        "El tablero no depende de archivos externos y usa una semilla fija para facilitar la reproducibilidad."
    )


if __name__ == "__main__":
    main()
