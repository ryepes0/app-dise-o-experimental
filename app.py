AUTOR = "Escribe aquí tu nombre"

import streamlit as st

st.set_page_config(
    page_title="App de Diseño Experimental",
    page_icon="🌱",
    layout="wide",
)

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")
st.write(
    "El diseño experimental permite comparar tratamientos de forma ordenada, "
    "controlar fuentes de variación y obtener evidencia útil para tomar "
    "decisiones en sistemas agrícolas."
)

st.subheader("Módulos")
st.table(
    [
        {
            "Código": "DCA",
            "Nombre completo": "Diseño completamente al azar",
            "Cuándo se usa": "Cuando las unidades experimentales son relativamente homogéneas.",
            "Ejemplo agrícola": "Comparar secadores de yuca bajo condiciones uniformes.",
            "Estado": "Disponible",
        },
        {
            "Código": "DBCA",
            "Nombre completo": "Diseño de bloques completos al azar",
            "Cuándo se usa": "Cuando se puede agrupar la variación en bloques homogéneos.",
            "Ejemplo agrícola": "Comparar fertilizantes en bloques a lo largo de un gradiente del suelo.",
            "Estado": "En construcción",
        },
        {
            "Código": "DCL",
            "Nombre completo": "Diseño de cuadrado latino",
            "Cuándo se usa": "Cuando se deben controlar dos fuentes de variación ajenas al tratamiento.",
            "Ejemplo agrícola": "Comparar variedades controlando gradientes en dos direcciones del lote.",
            "Estado": "En construcción",
        },
        {
            "Código": "DPD",
            "Nombre completo": "Diseño de parcelas divididas",
            "Cuándo se usa": "Cuando un factor requiere parcelas mayores o es difícil de aplicar.",
            "Ejemplo agrícola": "Evaluar sistemas de riego en parcelas y variedades en subparcelas.",
            "Estado": "En construcción",
        },
        {
            "Código": "Factoriales",
            "Nombre completo": "Diseños factoriales",
            "Cuándo se usa": "Cuando se estudian varios factores y sus posibles interacciones.",
            "Ejemplo agrícola": "Evaluar combinaciones de dosis de nitrógeno y láminas de riego en maíz.",
            "Estado": "En construcción",
        },
        {
            "Código": "RSM",
            "Nombre completo": "Metodología de superficie de respuesta",
            "Cuándo se usa": "Cuando se busca describir y optimizar una respuesta con factores cuantitativos.",
            "Ejemplo agrícola": "Optimizar temperatura y velocidad del aire para secar yuca.",
            "Estado": "En construcción",
        },
    ]
)

st.subheader("Cómo usar la app")
st.markdown(
    """
1. Elige el módulo correspondiente a tu diseño experimental.
2. Carga los datos del ensayo en el formato solicitado por el módulo.
3. Revisa los resultados y las visualizaciones generadas.
4. Verifica los supuestos y compara los resultados con tu cálculo manual.
"""
)

st.warning(
    "Esta app apoya el aprendizaje. El estudiante interpreta los resultados, "
    "verifica supuestos y compara con su cálculo manual."
)

with st.sidebar:
    st.subheader("Información del curso")
    st.write(f"**Autor:** {AUTOR}")
    st.write("**Curso:** Diseño Experimental")
    st.write("**Semestre:** 2026-2")