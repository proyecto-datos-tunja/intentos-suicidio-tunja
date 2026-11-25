from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------------ configuración
st.set_page_config(
    page_title="Intentos de suicidio · Tunja",
    page_icon="📊",
    layout="wide",
)

CSV_POR_DEFECTO = Path(__file__).parent / "Tunja_intentos_datos_limpios.csv"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Paleta sobria (azul pizarra / verde azulado), sin rojos
AZUL, TEAL, AMBAR, GRIS = "#3E5C76", "#2A7F8E", "#D08C2E", "#8A97A6"
COLOR_SEXO = {"FEMENINO": TEAL, "MASCULINO": AZUL}
ESCALA = ["#E3EEF1", "#9CC5CD", TEAL, "#1D4F5A"]

GRUPOS_EDAD = ["Niñez (6-11)", "Adolescencia (12-17)", "Juventud (18-28)", "Adultez (29-59)", "Mayores (60+)"]
ORDEN_ESCOLARIDAD = [
    "NINGUNO", "PREESCOLAR", "BASICA PRIMARIA", "BASICA SECUNDARIA", "MEDIA TECNICA",
    "TECNICA PROFESIONAL", "TECNOLOGICA O TECNICA", "PROFESIONAL", "ESPECIALIZACION", "MAESTRIA",
    "SIN INFORMACION",
]

FACTORES = [
    "PROBLEMAS_FAMILIARES", "CONFLICTO_CON_PAREJA_O_EX_PAREJA", "ESCOLAR_EDUCATIVA",
    "PROBLEMAS_ECONOMICOS", "MALTRATO_FISICO_SICOLOGICO_SEXUAL", "PROBLEMAS_LABORALES",
    "MUERTE_DE_UN_FAMILIAR", "ENFERMEDAD_CRONICA_DOLOROSA_O_DISCAPACITANTE",
    "SUICIDIO_DE_UN_FAMILIAR", "PROBLEMAS_JURIDICOS",
]
ANTECEDENTES = [
    "ANTECEDENTE_TRASTORNO_PSIQUIATRICO", "TRASTORNO_DEPRESIVO", "TRASTORNO_DE_PERSONALIDAD",
    "TRASTORNO_BIPOLAR", "ESQUIZOFRENIA", "CONSUMO_DE_SPA", "ABUSO_DE_ALCOHOL",
    "ANTECEDENTE_VIOLENCIA_O_ABUSO", "ANTECEDENTES_FAMILIARES_DE_CONDUCTA_SUICIDA",
]
MECANISMOS = [
    "INTOXICACIONES", "ARMA_CORTOPUNZANTE", "AHORCAMIENTO", "LANZAMIENTO_A_VEHICULO",
    "LANZAMIENTO_AL_VACIO", "ARMA_DE_FUEGO", "INMOLACION", "LANZAMIENTO_AL_AGUA",
]
REMISIONES = ["REMITIDO_A_PSIQUIATRIA", "REMITIDO_A_PSICOLOGIA", "REMITIDO_A_TRABAJO_SOCIAL"]

ETIQUETAS = {
    "CONFLICTO_CON_PAREJA_O_EX_PAREJA": "Conflicto con pareja o ex pareja",
    "ESCOLAR_EDUCATIVA": "Problemas escolares / educativos",
    "MALTRATO_FISICO_SICOLOGICO_SEXUAL": "Maltrato físico, psicológico o sexual",
    "ENFERMEDAD_CRONICA_DOLOROSA_O_DISCAPACITANTE": "Enfermedad crónica, dolorosa o discapacitante",
    "ANTECEDENTE_TRASTORNO_PSIQUIATRICO": "Antecedente de trastorno psiquiátrico",
    "ANTECEDENTES_FAMILIARES_DE_CONDUCTA_SUICIDA": "Antecedentes familiares de conducta suicida",
    "ANTECEDENTE_VIOLENCIA_O_ABUSO": "Antecedente de violencia o abuso",
    "CONSUMO_DE_SPA": "Consumo de sustancias psicoactivas",
    "ARMA_CORTOPUNZANTE": "Arma cortopunzante",
    "LANZAMIENTO_A_VEHICULO": "Lanzamiento a vehículo",
    "LANZAMIENTO_AL_VACIO": "Lanzamiento al vacío",
    "INMOLACION": "Inmolación",
    "REMITIDO_A_PSIQUIATRIA": "Psiquiatría",
    "REMITIDO_A_PSICOLOGIA": "Psicología",
    "REMITIDO_A_TRABAJO_SOCIAL": "Trabajo social",
    "IDEACION_SUICIDA_PERSISTENTE": "Ideación suicida persistente",
    "PLAN_ORGANIZADO_DE_SUICIDIO": "Plan organizado de suicidio",
    "INTENTOS_PREVIOS": "Intentos previos",
}


def etiqueta(col: str) -> str:
    """Nombre legible de una columna."""
    return ETIQUETAS.get(col, col.replace("_", " ").capitalize())


# ------------------------------------------------------------------ carga de datos
@st.cache_data(show_spinner="Cargando datos…")
def cargar(origen) -> pd.DataFrame:
    df = pd.read_csv(origen, parse_dates=["FECHA_NOTIFICACION", "FECHA_HECHO"])
    df = df.rename(columns={"ANIO": "AÑO"})  # el CSV usa ANIO; en pantalla y en descargas se ve AÑO
    df["MES"] = df["FECHA_NOTIFICACION"].dt.month
    df["PERIODO"] = df["FECHA_NOTIFICACION"].dt.to_period("M").dt.to_timestamp()
    df["GRUPO_EDAD"] = pd.cut(
        df["EDAD"], bins=[-1, 11, 17, 28, 59, 200], labels=GRUPOS_EDAD
    ).astype(str)
    return df


if CSV_POR_DEFECTO.exists():
    df = cargar(CSV_POR_DEFECTO)
else:
    st.title("Intentos de suicidio · Tunja")
    st.info(
        "No encontré `Tunja_intentos_datos_limpios.csv` junto a este archivo. "
        "Cópialo a la misma carpeta o súbelo aquí."
    )
    subido = st.file_uploader("Base limpia (CSV)", type="csv")
    if subido is None:
        st.stop()
    df = cargar(subido)


# ------------------------------------------------------------------ utilidades
def pct_si(datos: pd.DataFrame, columnas: list[str], por: str | None = None) -> pd.DataFrame:
    """Porcentaje de filas con 'SI' en cada columna, opcionalmente por grupo."""
    filas = []
    grupos = [(None, datos)] if por is None else datos.groupby(por, observed=True)
    for nombre, sub in grupos:
        for c in columnas:
            filas.append({
                "Variable": etiqueta(c),
                "Grupo": nombre,
                "Porcentaje": (sub[c] == "SI").mean() * 100 if len(sub) else 0,
                "Casos": int((sub[c] == "SI").sum()),
            })
    return pd.DataFrame(filas)


def como_leerlo(texto: str):
    """Línea corta en lenguaje sencillo debajo de cada gráfico."""
    st.caption(f"**Cómo leerlo:** {texto}")


def barras_pct(datos, columnas, por_sexo=False, alto=380):
    t = pct_si(datos, columnas, "SEXO" if por_sexo else None)
    orden = t.groupby("Variable")["Porcentaje"].max().sort_values().index.tolist()
    fig = px.bar(
        t, x="Porcentaje", y="Variable", orientation="h",
        color="Grupo" if por_sexo else None,
        color_discrete_map=COLOR_SEXO, barmode="group",
        text=t["Porcentaje"].map("{:.1f}%".format),
        category_orders={"Variable": orden},
        hover_data={"Casos": True, "Porcentaje": ":.1f"},
    )
    if not por_sexo:
        fig.update_traces(marker_color=TEAL)
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(
        height=alto, margin=dict(l=0, r=30, t=10, b=0), yaxis_title=None,
        xaxis_title="% de casos", legend_title=None,
    )
    return fig


def barras_cat(datos, col, orden=None, horizontal=True, alto=340):
    t = datos[col].astype(str).value_counts().rename_axis(col).reset_index(name="Casos")
    t["%"] = t["Casos"] / t["Casos"].sum() * 100
    if orden:
        t[col] = pd.Categorical(t[col], categories=[o for o in orden if o in set(t[col])], ordered=True)
        t = t.sort_values(col)
    else:
        t = t.sort_values("Casos")
    x, y = ("Casos", col) if horizontal else (col, "Casos")
    fig = px.bar(t, x=x, y=y, orientation="h" if horizontal else "v",
                 text=t.apply(lambda r: f"{r['Casos']} ({r['%']:.0f}%)", axis=1))
    fig.update_traces(marker_color=AZUL, textposition="outside", cliponaxis=False)
    fig.update_layout(height=alto, margin=dict(l=0, r=40, t=10, b=0),
                      xaxis_title=None if not horizontal else "Casos",
                      yaxis_title=None)
    return fig


def hallazgos(datos: pd.DataFrame) -> list[str]:
    """Resumen automático en lenguaje sencillo de lo más llamativo en la selección actual."""
    por_anio = datos["AÑO"].value_counts()
    grupo = datos["GRUPO_EDAD"].value_counts()
    top_factor = pct_si(datos, FACTORES).sort_values("Porcentaje", ascending=False).iloc[0]
    top_mec = pct_si(datos, MECANISMOS).sort_values("Porcentaje", ascending=False).iloc[0]
    mujeres = (datos["SEXO"] == "FEMENINO").mean() * 100
    return [
        f"**{por_anio.idxmax()}** es el año con más casos notificados ({por_anio.max():,}).",
        f"El grupo de edad más frecuente es **{grupo.idxmax()}**, con el {grupo.max() / len(datos) * 100:.0f}% de los casos.",
        f"Las mujeres son el **{mujeres:.0f}%** de los casos y los hombres el **{100 - mujeres:.0f}%**.",
        f"El factor desencadenante más registrado es **{top_factor['Variable'].lower()}** ({top_factor['Porcentaje']:.0f}% de los casos).",
        f"El mecanismo más registrado es **{top_mec['Variable'].lower()}** ({top_mec['Porcentaje']:.0f}% de los casos).",
    ]


# ------------------------------------------------------------------ filtros (barra lateral)
with st.sidebar:
    st.header("Filtros")
    anios = sorted(df["AÑO"].unique())
    f_anio = st.multiselect("Año", anios, default=anios)
    f_sexo = st.multiselect("Sexo", sorted(df["SEXO"].unique()), default=sorted(df["SEXO"].unique()))
    e_min, e_max = int(df["EDAD"].min()), int(df["EDAD"].max())
    f_edad = st.slider("Edad", e_min, e_max, (e_min, e_max))
    areas = sorted(df["AREA_RESIDENCIA"].unique())
    f_area = st.multiselect("Área de residencia", areas, default=areas)
    estratos = sorted(df["ESTRATO"].unique())
    f_estrato = st.multiselect("Estrato", estratos, default=estratos)
    st.divider()
    excluir_flag = st.checkbox(
        "Excluir registros con fechas inconsistentes",
        value=False,
        help="Registros donde la fecha del hecho es posterior a la de notificación.",
    )

d = df[
    df["AÑO"].isin(f_anio)
    & df["SEXO"].isin(f_sexo)
    & df["EDAD"].between(*f_edad)
    & df["AREA_RESIDENCIA"].isin(f_area)
    & df["ESTRATO"].isin(f_estrato)
]
if excluir_flag:
    d = d[d["FLAG_FECHA_INCONSISTENTE"] == "NO"]

# ------------------------------------------------------------------ encabezado
st.title("Intentos de suicidio notificados en Tunja")
st.caption(
    f"Datos de {df['FECHA_NOTIFICACION'].min():%d/%m/%Y} a {df['FECHA_NOTIFICACION'].max():%d/%m/%Y}. "
    f"Mostrando {len(d):,} de {len(df):,} registros según los filtros."
)

with st.expander("Guía rápida: qué significa cada término"):
    st.markdown(
        """
- **Caso:** cada registro de intento de suicidio notificado al sistema de vigilancia en salud pública.
- **Mediana de edad:** la edad "del medio": la mitad de los casos es más joven y la otra mitad es mayor.
- **Intentos previos:** la persona ya había tenido al menos un intento antes del notificado.
- **Ideación suicida persistente:** pensamientos de suicidio que se repiten o continúan en el tiempo.
- **Plan organizado:** la persona había pensado cómo, cuándo o dónde hacerlo antes del intento.
- **Factor desencadenante:** situación registrada en la ficha (por ejemplo, un conflicto familiar). Es un dato de contexto, **no** una causa comprobada.
- **Fechas inconsistentes:** registros donde la fecha del hecho es posterior a la de notificación (probable error de digitación).
- Los gráficos con porcentajes **no suman 100%** cuando un caso puede tener varios factores o mecanismos a la vez.
        """
    )

if d.empty:
    st.warning("Ningún registro cumple los filtros. Amplía la selección en la barra lateral.")
    st.stop()

# ------------------------------------------------------------------ indicadores
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Casos", f"{len(d):,}", border=True, help="Total de registros con los filtros actuales.")
c2.metric("Edad mediana", f"{d['EDAD'].median():.0f} años", border=True,
          help="La mitad de los casos es más joven que esta edad y la otra mitad es mayor.")
c3.metric("Mujeres", f"{(d['SEXO'] == 'FEMENINO').mean() * 100:.0f}%", border=True,
          help="Porcentaje de casos de sexo femenino.")
c4.metric("Con intentos previos", f"{(d['INTENTOS_PREVIOS'] == 'SI').mean() * 100:.0f}%", border=True,
          help="Porcentaje de personas que ya habían tenido al menos un intento antes.")
c5.metric("Con ideación persistente", f"{(d['IDEACION_SUICIDA_PERSISTENTE'] == 'SI').mean() * 100:.0f}%",
          border=True, help="Porcentaje con pensamientos de suicidio que se repiten en el tiempo.")

with st.container(border=True):
    st.markdown("**Lo más importante con los filtros actuales**")
    for linea in hallazgos(d):
        st.markdown(f"- {linea}")

st.write("")
tab_tiempo, tab_perfil, tab_factores, tab_mecanismo, tab_territorio, tab_datos = st.tabs(
    ["Evolución", "Perfil", "Factores y antecedentes", "Mecanismo y atención", "Territorio", "Datos"]
)

# ------------------------------------------------------------------ evolución
with tab_tiempo:
    izq, der = st.columns([2, 3])
    with izq:
        st.subheader("Casos por año")
        t = d.groupby(["AÑO", "SEXO"]).size().reset_index(name="Casos")
        fig = px.bar(t, x="AÑO", y="Casos", color="SEXO", color_discrete_map=COLOR_SEXO,
                     text="Casos", barmode="stack", labels={"AÑO": "Año"})
        fig.update_xaxes(type="category", title=None)
        fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), legend_title=None)
        st.plotly_chart(fig, width="stretch")
        como_leerlo("cada barra es un año; los colores separan mujeres y hombres.")
    with der:
        st.subheader("Casos por mes de notificación")
        t = d.groupby("PERIODO").size().reset_index(name="Casos")
        fig = px.line(t, x="PERIODO", y="Casos", markers=True)
        fig.update_traces(line_color=TEAL, marker_color=TEAL)
        fig.update_layout(height=360, margin=dict(l=0, r=0, t=10, b=0), xaxis_title=None)
        st.plotly_chart(fig, width="stretch")
        como_leerlo("cada punto es un mes; si la línea sube, ese mes hubo más casos.")

    st.subheader("Estacionalidad: casos por mes y año")
    piv = (d.pivot_table(index="AÑO", columns="MES", values="ID_REGISTRO", aggfunc="count", fill_value=0)
             .reindex(columns=range(1, 13), fill_value=0))
    fig = px.imshow(piv.values, x=MESES, y=piv.index.astype(str), text_auto=True,
                    aspect="auto", color_continuous_scale=ESCALA, labels=dict(color="Casos"))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    como_leerlo("cuanto más oscuro es el cuadro, más casos hubo en ese mes de ese año.")
    st.caption("Los meses sin datos al final de la serie pueden reflejar un año incompleto, no ausencia de casos.")

# ------------------------------------------------------------------ perfil
with tab_perfil:
    a, b = st.columns(2)
    with a:
        st.subheader("Distribución por edad")
        fig = px.histogram(d, x="EDAD", color="SEXO", nbins=40, barmode="overlay",
                           opacity=0.75, color_discrete_map=COLOR_SEXO)
        fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0),
                          xaxis_title="Edad (años)", yaxis_title="Casos", legend_title=None)
        st.plotly_chart(fig, width="stretch")
        como_leerlo("cada barra cuenta cuántas personas hay en ese rango de edad.")
    with b:
        st.subheader("Grupo de edad")
        st.plotly_chart(barras_cat(d, "GRUPO_EDAD", orden=GRUPOS_EDAD, horizontal=False),
                        width="stretch")
        como_leerlo("las mismas edades agrupadas por etapa de vida; entre paréntesis, el % del total.")

    a, b = st.columns(2)
    with a:
        st.subheader("Escolaridad")
        st.plotly_chart(barras_cat(d, "ESCOLARIDAD", orden=ORDEN_ESCOLARIDAD, alto=380),
                        width="stretch")
    with b:
        st.subheader("Estado civil")
        st.plotly_chart(barras_cat(d, "ESTADO_CIVIL", alto=380), width="stretch")

    a, b = st.columns(2)
    with a:
        st.subheader("Estrato socioeconómico")
        t = d.assign(ESTRATO=d["ESTRATO"].astype(str))
        st.plotly_chart(barras_cat(t, "ESTRATO", orden=["1", "2", "3", "4", "5"], horizontal=False),
                        width="stretch")
        como_leerlo("el estrato 1 es el más bajo y el 5 el más alto.")
    with b:
        st.subheader("Afiliación a salud")
        st.plotly_chart(barras_cat(d, "SEGURIDAD_SOCIAL"), width="stretch")

# ------------------------------------------------------------------ factores
with tab_factores:
    por_sexo = st.toggle("Comparar por sexo", value=False)
    a, b = st.columns(2)
    with a:
        st.subheader("Factores desencadenantes")
        st.plotly_chart(barras_pct(d, FACTORES, por_sexo, alto=460), width="stretch")
    with b:
        st.subheader("Antecedentes y salud mental")
        st.plotly_chart(barras_pct(d, ANTECEDENTES, por_sexo, alto=460), width="stretch")
    como_leerlo("cada barra es el porcentaje de casos que tienen ese factor o antecedente. "
                "Un caso puede tener varios a la vez, por eso no suman 100%.")
    st.caption("Son situaciones registradas en la ficha de notificación, no causas comprobadas.")

    st.subheader("Señales de riesgo por grupo de edad")
    senales = ["IDEACION_SUICIDA_PERSISTENTE", "PLAN_ORGANIZADO_DE_SUICIDIO", "INTENTOS_PREVIOS",
               "PROBLEMAS_FAMILIARES", "CONFLICTO_CON_PAREJA_O_EX_PAREJA", "ESCOLAR_EDUCATIVA",
               "CONSUMO_DE_SPA", "ANTECEDENTE_TRASTORNO_PSIQUIATRICO"]
    t = pct_si(d, senales, "GRUPO_EDAD")
    piv = t.pivot(index="Variable", columns="Grupo", values="Porcentaje")
    piv = piv[[g for g in GRUPOS_EDAD if g in piv.columns]]
    fig = px.imshow(piv.values, x=list(piv.columns), y=list(piv.index), text_auto=".0f",
                    aspect="auto", color_continuous_scale=ESCALA, labels=dict(color="% de casos"))
    fig.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    como_leerlo("cada cuadro muestra qué % de las personas de ese grupo de edad presenta esa señal; "
                "más oscuro significa más frecuente.")

# ------------------------------------------------------------------ mecanismo y atención
with tab_mecanismo:
    a, b = st.columns(2)
    with a:
        st.subheader("Mecanismo registrado")
        st.plotly_chart(barras_pct(d, MECANISMOS, alto=380), width="stretch")
        como_leerlo("porcentaje de casos con cada mecanismo. Un mismo evento puede registrar más de uno, "
                    "por eso los porcentajes suman más de 100%.")
    with b:
        st.subheader("Remisión a servicios")
        st.plotly_chart(barras_pct(d, REMISIONES, alto=200), width="stretch")
        como_leerlo("porcentaje de casos que fueron enviados a cada servicio de atención.")
        st.subheader("Remisión por año")
        t = pct_si(d, REMISIONES, "AÑO")
        fig = px.line(t, x="Grupo", y="Porcentaje", color="Variable", markers=True,
                      color_discrete_sequence=[TEAL, AZUL, AMBAR])
        fig.update_xaxes(type="category", title=None)
        fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0),
                          yaxis_title="% remitidos", legend_title=None)
        st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------------------ territorio
with tab_territorio:
    a, b = st.columns([3, 2])
    with a:
        n = st.slider("Barrios a mostrar", 5, 30, 15)
        st.subheader(f"Los {n} barrios con más casos")
        t = d["BARRIO_RESIDENCIA"].value_counts().head(n).sort_values().reset_index()
        t.columns = ["Barrio", "Casos"]
        fig = px.bar(t, x="Casos", y="Barrio", orientation="h", text="Casos")
        fig.update_traces(marker_color=TEAL, textposition="outside", cliponaxis=False)
        fig.update_layout(height=max(360, n * 26), margin=dict(l=0, r=30, t=10, b=0), yaxis_title=None)
        st.plotly_chart(fig, width="stretch")
        como_leerlo("barrio de residencia de la persona, ordenado de mayor a menor número de casos.")
    with b:
        st.subheader("Área de residencia")
        t = d["AREA_RESIDENCIA"].value_counts().reset_index()
        t.columns = ["Área", "Casos"]
        fig = px.pie(t, names="Área", values="Casos", hole=0.55,
                     color_discrete_sequence=[AZUL, AMBAR, GRIS])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), legend_title=None)
        st.plotly_chart(fig, width="stretch")
    st.caption("Los barrios con pocos casos pueden variar por la forma en que se registró el nombre; "
               "la hoja Mapeo_Barrios del Excel documenta cómo se unificaron.")

# ------------------------------------------------------------------ datos
with tab_datos:
    st.subheader("Registros filtrados")
    st.caption("Tabla completa con los filtros aplicados. Puedes ordenar por cualquier columna.")
    st.dataframe(d.drop(columns=["MES", "PERIODO", "GRUPO_EDAD"]), width="stretch", height=480,
                 hide_index=True)
    st.download_button(
        "Descargar datos filtrados (CSV)",
        d.drop(columns=["MES", "PERIODO", "GRUPO_EDAD"]).to_csv(index=False).encode("utf-8-sig"),
        file_name="tunja_datos_filtrados.csv",
        mime="text/csv",
    )