from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.anova_utils import (
	ajustar_dca,
	cargar_datos,
	coeficiente_variacion,
	interpretar_dca,
	resumen_tratamientos,
	tabla_anova,
	tukey,
	validar_dca,
)
from utils.diagnostico_utils import (
	grafico_qq,
	grafico_residuos_vs_ajustados,
	prueba_levene,
	prueba_shapiro,
	residuos_y_ajustados,
)


RUTA_EJEMPLO = Path(__file__).resolve().parents[1] / "data" / "dca_secadores.csv"


@st.cache_data(show_spinner="Cargando datos...")
def cargar_datos_cacheados(
	contenido: bytes | None, nombre_archivo: str | None
) -> pd.DataFrame:
	"""Carga datos subidos o el archivo de ejemplo y conserva el resultado en caché.

	Args:
		contenido: Bytes del archivo cargado; `None` selecciona el ejemplo.
		nombre_archivo: Nombre original del archivo para conservar su extensión.

	Returns:
		Datos cargados mediante la utilidad común del proyecto.
	"""
	if contenido is None:
		return cargar_datos(RUTA_EJEMPLO)
	if nombre_archivo is None:
		raise ValueError("No se pudo identificar el archivo cargado.")

	extension = Path(nombre_archivo).suffix.lower()
	with tempfile.TemporaryDirectory() as directorio_temporal:
		ruta_temporal = Path(directorio_temporal) / f"datos{extension}"
		ruta_temporal.write_bytes(contenido)
		return cargar_datos(ruta_temporal)


st.title("Diseño completamente al azar (DCA)")
st.write(
	"El DCA compara tratamientos asignados al azar cuando las unidades son "
	"relativamente homogéneas. En este ejemplo se evalúa la humedad final de "
	"yuca obtenida con cuatro secadores solares, cada uno con cuatro réplicas."
)

archivo = st.file_uploader(
	"Cargar datos del experimento",
	type=["csv", "xlsx"],
	help="El archivo debe incluir una columna de tratamiento y otra de respuesta.",
)

try:
	if archivo is None:
		datos = cargar_datos_cacheados(None, None)
		st.caption("No se cargó un archivo; se usan los datos de ejemplo de los cuatro secadores solares.")
	else:
		datos = cargar_datos_cacheados(archivo.getvalue(), archivo.name)
except Exception as error:
	st.error(f"No se pudieron cargar los datos: {error}")
	st.stop()

if datos.empty or len(datos.columns) < 2:
	st.error("El archivo debe contener al menos dos columnas y una fila de datos.")
	st.stop()

columnas = datos.columns.tolist()
columnas_numericas = [
	indice
	for indice, columna in enumerate(columnas)
	if pd.api.types.is_numeric_dtype(datos[columna])
]
indice_tratamiento = next(
	(
		indice
		for indice, columna in enumerate(columnas)
		if not pd.api.types.is_numeric_dtype(datos[columna])
	),
	0,
)
indice_respuesta = columnas_numericas[-1] if columnas_numericas else len(columnas) - 1

columna_tratamiento, columna_respuesta = st.columns(2)
with columna_tratamiento:
	col_trat = st.selectbox(
		"Columna de tratamiento", columnas, index=indice_tratamiento
	)
with columna_respuesta:
	col_resp = st.selectbox(
		"Columna de respuesta", columnas, index=indice_respuesta
	)

alfa = st.slider(
	"Nivel de significancia (alfa)",
	min_value=0.01,
	max_value=0.10,
	value=0.05,
	step=0.01,
	format="%.2f",
)

errores = validar_dca(datos, col_trat, col_resp)
if errores:
	for error in errores:
		st.error(error)
	st.stop()

modelo = ajustar_dca(datos, col_trat, col_resp)
tabla = tabla_anova(modelo)
resumen = resumen_tratamientos(datos, col_trat, col_resp)
fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos"].iloc[0]
p_valor = float(fila_tratamientos["p-valor"])

cv = coeficiente_variacion(modelo, datos, col_resp)
resumen_diagnostico = residuos_y_ajustados(modelo)
estadistico_shapiro, p_shapiro, conclusion_shapiro = prueba_shapiro(
	resumen_diagnostico["Residuo"], alfa
)
estadistico_levene, p_levene, conclusion_levene = prueba_levene(
	datos, col_trat, col_resp, alfa
)

pestanas = st.tabs(["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"])

with pestanas[0]:
	st.subheader("Datos del experimento")
	st.dataframe(datos, hide_index=True, width="stretch")
	st.subheader("Resumen por tratamiento")
	st.dataframe(resumen, hide_index=True, width="stretch")

with pestanas[1]:
	st.subheader("Tabla ANOVA")
	columnas_formato = {
		columna: "{:.4f}"
		for columna in ("gl", "SC", "CM", "F", "p-valor")
	}
	st.dataframe(
		tabla.style.format(columnas_formato, na_rep="—"),
		hide_index=True,
		width="stretch",
	)
	st.metric("Coeficiente de variación", f"{cv:.4f}%")
	if p_valor < alfa:
		st.success(interpretar_dca(tabla, alfa))
	else:
		st.info(interpretar_dca(tabla, alfa))

with pestanas[2]:
	st.subheader("Comparaciones múltiples de Tukey")
	if p_valor < alfa:
		comparaciones, dms = tukey(datos, col_trat, col_resp, alfa)
		st.caption(f"DMS (Tukey): {dms:.4f}")
		st.dataframe(comparaciones, hide_index=True, width="stretch")
	else:
		st.info(
			"No se realiza Tukey porque el ANOVA no encontró evidencia suficiente "
			"de diferencias entre tratamientos al nivel de significancia elegido."
		)

with pestanas[3]:
	st.subheader("Distribución de la respuesta")
	grafico_cajas = px.box(
		datos,
		x=col_trat,
		y=col_resp,
		points="all",
		labels={col_trat: "Tratamiento", col_resp: "Respuesta"},
	)
	st.plotly_chart(grafico_cajas, width="stretch")

	st.subheader("Media por tratamiento")
	grafico_medias = px.bar(
		resumen,
		x="Tratamiento",
		y="media",
		error_y="desviación estándar",
		labels={"Tratamiento": "Tratamiento", "media": "Media de la respuesta"},
	)
	st.plotly_chart(grafico_medias, width="stretch")

with pestanas[4]:
	st.subheader("Diagnóstico de supuestos")
	columna_residuos, columna_qq = st.columns(2)
	with columna_residuos:
		st.plotly_chart(
			grafico_residuos_vs_ajustados(resumen_diagnostico),
			width="stretch",
		)
	with columna_qq:
		st.plotly_chart(
			grafico_qq(resumen_diagnostico["Residuo"]),
			width="stretch",
		)

	tabla_supuestos = pd.DataFrame(
		[
			{
				"Prueba": "Shapiro-Wilk",
				"Estadístico": estadistico_shapiro,
				"p-valor": p_shapiro,
				"Conclusión": conclusion_shapiro,
			},
			{
				"Prueba": "Levene (mediana)",
				"Estadístico": estadistico_levene,
				"p-valor": p_levene,
				"Conclusión": conclusion_levene,
			},
		]
	)
	st.dataframe(
		tabla_supuestos.style.format(
			{"Estadístico": "{:.4f}", "p-valor": "{:.4f}"},
			na_rep="No disponible",
		),
		hide_index=True,
		width="stretch",
	)

	st.markdown(
		"- **Normalidad:** Shapiro-Wilk evalúa si los residuos son compatibles con "
		"una distribución normal.\n"
		"- **Homogeneidad de varianzas:** Levene, centrada en la mediana, evalúa si "
		"la variabilidad de la respuesta es similar entre tratamientos.\n"
		"- **Independencia:** no se confirma con estas pruebas; debe sustentarse en "
		"la asignación aleatoria de las unidades experimentales."
	)