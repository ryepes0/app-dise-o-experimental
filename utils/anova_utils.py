from __future__ import annotations

import warnings
from math import sqrt
from pathlib import Path

import pandas as pd
from scipy.stats import studentized_range
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.regression.linear_model import RegressionResultsWrapper


def cargar_datos(archivo: str | Path) -> pd.DataFrame:
    """Carga un archivo CSV o Excel en un DataFrame.

    Args:
        archivo: Ruta del archivo CSV o Excel con extensión `.xlsx`.

    Returns:
        Los datos leídos desde el archivo.

    Raises:
        ValueError: Si la extensión no corresponde a CSV o `.xlsx`.
    """
    ruta = Path(archivo)
    extension = ruta.suffix.lower()

    # Se selecciona el lector según la extensión, sin transformar los datos.
    if extension == ".csv":
        # El motor de Python detecta automáticamente separadores coma o punto y coma.
        return pd.read_csv(ruta, sep=None, engine="python")
    if extension == ".xlsx":
        return pd.read_excel(ruta)

    raise ValueError("El archivo debe tener extensión .csv o .xlsx.")


def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Revisa que los datos cumplan las condiciones básicas para un DCA.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Mensajes de error en español; la lista queda vacía si los datos son válidos.
    """
    errores: list[str] = []
    columnas_faltantes = [
        columna for columna in (col_trat, col_resp) if columna not in df.columns
    ]
    if columnas_faltantes:
        errores.append(
            "Faltan las columnas requeridas: " + ", ".join(columnas_faltantes) + "."
        )
        return errores

    # Se verifica primero la ausencia de datos para no confundirlos con texto no numérico.
    if df[[col_trat, col_resp]].isna().any().any():
        errores.append("Hay datos faltantes en las columnas del análisis.")

    # La conversión de prueba identifica valores no numéricos sin modificar el DataFrame.
    respuesta_numerica = pd.to_numeric(df[col_resp], errors="coerce")
    no_numericos = df[col_resp].notna() & respuesta_numerica.isna()
    if no_numericos.any():
        errores.append(f"La respuesta de la columna '{col_resp}' no es numérica.")

    # k cuenta tratamientos distintos; cada n_j cuenta las réplicas observadas por tratamiento.
    tratamientos = df[col_trat].dropna().unique()
    if len(tratamientos) < 2:
        errores.append("El diseño debe incluir al menos 2 tratamientos.")

    replicas = df.groupby(col_trat, dropna=True).size()
    if (replicas < 2).any():
        errores.append("Cada tratamiento debe tener al menos 2 réplicas.")

    return errores


def ajustar_dca(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> RegressionResultsWrapper:
    """Ajusta el modelo lineal de un diseño completamente al azar.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        El modelo OLS ajustado.

    Raises:
        ValueError: Si los datos no cumplen las validaciones básicas del DCA.
    """
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede ajustar el DCA: " + " ".join(errores))

    datos = df.copy()
    datos[col_resp] = pd.to_numeric(datos[col_resp])

    # El modelo separa la media general del efecto del tratamiento: Y_ij = mu + tau_i + error_ij.
    formula = f"Q({col_resp!r}) ~ C(Q({col_trat!r}))"
    return ols(formula=formula, data=datos).fit()


def tabla_anova(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Construye la tabla ANOVA tipo II para el modelo DCA.

    Args:
        modelo: Modelo OLS ajustado con `ajustar_dca`.

    Returns:
        Tabla con las fuentes, grados de libertad, sumas y cuadrados medios,
        estadístico F y valor p.

    Raises:
        ValueError: Si el modelo no contiene una fuente de tratamientos y residuos.
    """
    # Tipo II compara tratamientos ajustando el modelo al factor del DCA.
    anova = anova_lm(modelo, typ=2)
    filas_tratamiento = anova.loc[anova.index != "Residual"]
    if filas_tratamiento.empty or "Residual" not in anova.index:
        raise ValueError("El modelo debe contener tratamientos y una fila de error residual.")

    fila_tratamiento = filas_tratamiento.iloc[0]
    fila_error = anova.loc["Residual"]
    sc_tratamiento = float(fila_tratamiento["sum_sq"])
    gl_tratamiento = float(fila_tratamiento["df"])
    sc_error = float(fila_error["sum_sq"])
    gl_error = float(fila_error["df"])

    # Cada cuadrado medio usa CM = SC / gl; el total suma tratamientos y error.
    sc_total = sc_tratamiento + sc_error
    gl_total = gl_tratamiento + gl_error
    filas = [
        {
            "Fuente": "Tratamientos",
            "gl": gl_tratamiento,
            "SC": sc_tratamiento,
            "CM": sc_tratamiento / gl_tratamiento,
            "F": float(fila_tratamiento["F"]),
            "p-valor": float(fila_tratamiento["PR(>F)"]),
        },
        {
            "Fuente": "Error",
            "gl": gl_error,
            "SC": sc_error,
            "CM": sc_error / gl_error,
            "F": float("nan"),
            "p-valor": float("nan"),
        },
        {
            "Fuente": "Total",
            "gl": gl_total,
            "SC": sc_total,
            "CM": sc_total / gl_total,
            "F": float("nan"),
            "p-valor": float("nan"),
        },
    ]
    return pd.DataFrame(filas, columns=["Fuente", "gl", "SC", "CM", "F", "p-valor"])


def resumen_tratamientos(
    df: pd.DataFrame, col_trat: str, col_resp: str
) -> pd.DataFrame:
    """Resume el número de réplicas y la respuesta por tratamiento.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.

    Returns:
        Tabla con n, total, media y desviación estándar para cada tratamiento.

    Raises:
        ValueError: Si faltan columnas, hay datos faltantes o la respuesta no es numérica.
    """
    errores = validar_dca(df, col_trat, col_resp)
    errores_bloqueantes = [
        mensaje
        for mensaje in errores
        if "Faltan las columnas" in mensaje
        or "datos faltantes" in mensaje
        or "no es numérica" in mensaje
    ]
    if errores_bloqueantes:
        raise ValueError("No se puede resumir el DCA: " + " ".join(errores_bloqueantes))

    # Para cada tratamiento se calculan n, sum(Y), media(Y) y la desviación estándar muestral.
    datos = pd.DataFrame(
        {
            "Tratamiento": df[col_trat],
            "Respuesta": pd.to_numeric(df[col_resp]),
        }
    )
    resumen = (
        datos.groupby("Tratamiento", dropna=True)["Respuesta"]
        .agg(["count", "sum", "mean", "std"])
        .reset_index()
    )
    return resumen.rename(
        columns={
            "count": "n",
            "sum": "total",
            "mean": "media",
            "std": "desviación estándar",
        }
    )


def coeficiente_variacion(
    modelo: RegressionResultsWrapper, df: pd.DataFrame, col_resp: str
) -> float:
    """Calcula el coeficiente de variación usando el cuadrado medio del error.

    Args:
        modelo: Modelo OLS ajustado para el DCA.
        df: Datos usados en el análisis.
        col_resp: Nombre de la columna con la respuesta.

    Returns:
        Coeficiente de variación porcentual.

    Raises:
        ValueError: Si falta la respuesta, hay datos faltantes o su media es cero.
    """
    if col_resp not in df.columns:
        raise ValueError(f"No existe la columna de respuesta '{col_resp}'.")
    if df[col_resp].isna().any():
        raise ValueError("Hay datos faltantes en la columna de respuesta.")

    # La media general da la escala de la respuesta respecto a la variación residual.
    media_general = float(pd.to_numeric(df[col_resp]).mean())
    if media_general == 0:
        raise ValueError("La media general debe ser distinta de cero para calcular el CV.")

    # CV = sqrt(CME) / media general * 100, donde CME es el CM de la fila Error.
    anova = tabla_anova(modelo)
    cuadrado_medio_error = float(anova.loc[anova["Fuente"] == "Error", "CM"].iloc[0])
    return sqrt(cuadrado_medio_error) / media_general * 100


def tukey(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[pd.DataFrame, float]:
    """Compara tratamientos con Tukey y calcula una diferencia mínima significativa.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna con la respuesta numérica.
        alfa: Nivel de significancia entre 0 y 1.

    Returns:
        Una tabla de comparaciones de Tukey y la DMS calculada.

    Raises:
        ValueError: Si los datos no son válidos o alfa no está entre 0 y 1.
    """
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        raise ValueError("No se puede comparar el DCA: " + " ".join(errores))

    datos = df.copy()
    datos[col_resp] = pd.to_numeric(datos[col_resp])

    # Tukey contrasta cada par de medias controlando el error familiar de comparaciones.
    resultado = pairwise_tukeyhsd(
        endog=datos[col_resp], groups=datos[col_trat], alpha=alfa
    )
    datos_resumen = resultado.summary().data
    comparaciones = pd.DataFrame(datos_resumen[1:], columns=datos_resumen[0])
    comparaciones = comparaciones.rename(
        columns={
            "group1": "Tratamiento 1",
            "group2": "Tratamiento 2",
            "meandiff": "Diferencia de medias",
            "p-adj": "p-valor ajustado",
            "lower": "IC inferior",
            "upper": "IC superior",
            "reject": "Rechaza H0",
        }
    )

    # glE y CME provienen del ANOVA; q usa el cuantil 1-alfa de la distribución studentizada.
    anova = tabla_anova(ajustar_dca(datos, col_trat, col_resp))
    fila_error = anova.loc[anova["Fuente"] == "Error"].iloc[0]
    gl_error = float(fila_error["gl"])
    cuadrado_medio_error = float(fila_error["CM"])
    conteos = datos.groupby(col_trat).size()
    balanceado = conteos.nunique() == 1
    if balanceado:
        replicas = float(conteos.iloc[0])
    else:
        # En datos desbalanceados, la media armónica de n_i aproxima la réplica común r.
        warnings.warn(
            "El diseño no está balanceado; la DMS calculada es aproximada.",
            UserWarning,
            stacklevel=2,
        )
        replicas = float(len(conteos) / (1 / conteos).sum())

    # DMS = q_(1-alfa; t, glE) * sqrt(CME / r); t es el número de tratamientos.
    numero_tratamientos = int(datos[col_trat].nunique())
    cuantil_q = float(
        studentized_range.ppf(1 - alfa, numero_tratamientos, gl_error)
    )
    dms = cuantil_q * sqrt(cuadrado_medio_error / replicas)
    return comparaciones, dms


def interpretar_dca(tabla: pd.DataFrame, alfa: float = 0.05) -> str:
    """Interpreta la prueba global de tratamientos para un DCA.

    Args:
        tabla: Tabla ANOVA con las columnas `Fuente` y `p-valor`.
        alfa: Nivel de significancia entre 0 y 1.

    Returns:
        Explicación sencilla sobre la decisión de la hipótesis nula.

    Raises:
        ValueError: Si la tabla no contiene la fila de tratamientos o alfa es inválido.
    """
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    if not {"Fuente", "p-valor"}.issubset(tabla.columns):
        raise ValueError("La tabla debe incluir las columnas 'Fuente' y 'p-valor'.")

    fila_tratamientos = tabla.loc[tabla["Fuente"] == "Tratamientos", "p-valor"]
    if fila_tratamientos.empty:
        raise ValueError("La tabla no contiene la fila 'Tratamientos'.")

    # H0 establece igualdad de medias; la regla de decisión compara p con alfa.
    valor_p = float(fila_tratamientos.iloc[0])
    if valor_p < alfa:
        return (
            f"Se rechaza H0 (p = {valor_p:.4g} < alfa = {alfa:g}). "
            "Hay evidencia de que al menos dos medias de tratamiento difieren; "
            "la decisión debe considerar también la importancia agronómica."
        )
    return (
        f"No se rechaza H0 (p = {valor_p:.4g} >= alfa = {alfa:g}). "
        "No hay evidencia suficiente para afirmar que las medias difieren; "
        "considere además los objetivos y condiciones del ensayo."
    )