from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from numpy.typing import ArrayLike
from scipy.stats import levene, probplot, shapiro
from statsmodels.regression.linear_model import RegressionResultsWrapper


def residuos_y_ajustados(modelo: RegressionResultsWrapper) -> pd.DataFrame:
    """Extrae los residuos y valores ajustados del modelo DCA.

    Args:
        modelo: Modelo OLS ajustado para el diseño completamente al azar.

    Returns:
        DataFrame con una columna para los valores ajustados y otra para los residuos.
    """
    # Para cada unidad, el residuo es e_i = y_i - y_estimado_i.
    return pd.DataFrame(
        {
            "Ajustado": modelo.fittedvalues,
            "Residuo": modelo.resid,
        }
    )


def prueba_shapiro(
    residuos: ArrayLike, alfa: float = 0.05
) -> tuple[float, float, str]:
    """Evalúa la normalidad de los residuos con Shapiro-Wilk.

    Args:
        residuos: Residuos del modelo que se van a evaluar.
        alfa: Nivel de significancia entre 0 y 1.

    Returns:
        Estadístico W, valor p y conclusión en español.

    Raises:
        ValueError: Si alfa no está entre 0 y 1.
    """
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")

    valores = np.asarray(residuos, dtype=float).ravel()
    valores = valores[np.isfinite(valores)]
    if valores.size < 3:
        return (
            math.nan,
            math.nan,
            "No se puede evaluar la normalidad: se requieren al menos 3 residuos válidos.",
        )

    # Shapiro-Wilk contrasta H0: los residuos provienen de una distribución normal.
    resultado = shapiro(valores)
    estadistico = float(resultado.statistic)
    p_valor = float(resultado.pvalue)
    if p_valor < alfa:
        conclusion = (
            f"Se rechaza la normalidad de los residuos (p = {p_valor:.4g} < alfa = {alfa:g})."
        )
    else:
        conclusion = (
            f"No se rechaza la normalidad de los residuos (p = {p_valor:.4g} >= alfa = {alfa:g})."
        )
    return estadistico, p_valor, conclusion


def prueba_levene(
    df: pd.DataFrame,
    col_trat: str,
    col_resp: str,
    alfa: float = 0.05,
) -> tuple[float, float, str]:
    """Evalúa la homogeneidad de varianzas con Levene centrada en la mediana.

    Args:
        df: Datos del experimento.
        col_trat: Nombre de la columna que identifica los tratamientos.
        col_resp: Nombre de la columna de respuesta numérica.
        alfa: Nivel de significancia entre 0 y 1.

    Returns:
        Estadístico de Levene, valor p y conclusión en español.

    Raises:
        ValueError: Si alfa no está entre 0 y 1, faltan columnas o la respuesta no es numérica.
    """
    if not 0 < alfa < 1:
        raise ValueError("alfa debe estar entre 0 y 1.")
    if not {col_trat, col_resp}.issubset(df.columns):
        raise ValueError("No se encontraron las columnas de tratamiento y respuesta indicadas.")

    # Se agrupan las respuestas válidas para comparar la dispersión de cada tratamiento.
    datos = df[[col_trat, col_resp]].dropna().copy()
    try:
        datos[col_resp] = pd.to_numeric(datos[col_resp], errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("La respuesta debe contener únicamente valores numéricos.") from error

    grupos = [
        grupo[col_resp].to_numpy(dtype=float)
        for _, grupo in datos.groupby(col_trat, dropna=True, sort=False)
    ]
    if len(grupos) < 2 or any(len(grupo) < 2 for grupo in grupos):
        return (
            math.nan,
            math.nan,
            "No se puede evaluar la homogeneidad: cada uno de al menos 2 tratamientos requiere 2 observaciones.",
        )

    # Levene usa desviaciones respecto a la mediana para contrastar H0: todas las varianzas son iguales.
    resultado = levene(*grupos, center="median")
    estadistico = float(resultado.statistic)
    p_valor = float(resultado.pvalue)
    if p_valor < alfa:
        conclusion = (
            f"Se rechaza la igualdad de varianzas (p = {p_valor:.4g} < alfa = {alfa:g})."
        )
    else:
        conclusion = (
            f"No se rechaza la igualdad de varianzas (p = {p_valor:.4g} >= alfa = {alfa:g})."
        )
    return estadistico, p_valor, conclusion


def grafico_residuos_vs_ajustados(resumen: pd.DataFrame) -> go.Figure:
    """Crea un gráfico de residuos frente a valores ajustados.

    Args:
        resumen: DataFrame con las columnas `Ajustado` y `Residuo`.

    Returns:
        Figura Plotly con puntos y una línea horizontal en cero.

    Raises:
        ValueError: Si faltan las columnas requeridas.
    """
    columnas = {"Ajustado", "Residuo"}
    if not columnas.issubset(resumen.columns):
        raise ValueError("El resumen debe incluir las columnas 'Ajustado' y 'Residuo'.")

    # Una nube sin patrón alrededor de cero respalda varianza aproximadamente constante.
    figura = px.scatter(
        resumen,
        x="Ajustado",
        y="Residuo",
        labels={"Ajustado": "Valores ajustados", "Residuo": "Residuos"},
        title="Residuos frente a valores ajustados",
    )
    figura.add_hline(y=0, line_dash="dash", line_color="#6b7280")
    return figura


def grafico_qq(residuos: ArrayLike) -> go.Figure:
    """Crea un gráfico Q-Q normal para los residuos del modelo.

    Args:
        residuos: Residuos del modelo que se van a representar.

    Returns:
        Figura Plotly con cuantiles observados y cuantiles normales teóricos.

    Raises:
        ValueError: Si hay menos de dos residuos finitos.
    """
    valores = np.asarray(residuos, dtype=float).ravel()
    valores = valores[np.isfinite(valores)]
    if valores.size < 2:
        raise ValueError("Se requieren al menos 2 residuos finitos para crear el gráfico Q-Q.")

    # probplot ordena residuos y obtiene cuantiles normales y la recta de referencia ajustada.
    (cuantiles_teoricos, cuantiles_observados), parametros = probplot(
        valores, dist="norm", fit=True
    )
    pendiente, intercepto, _ = parametros
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=cuantiles_teoricos,
            y=cuantiles_observados,
            mode="markers",
            name="Residuos",
        )
    )
    figura.add_trace(
        go.Scatter(
            x=cuantiles_teoricos,
            y=pendiente * np.asarray(cuantiles_teoricos) + intercepto,
            mode="lines",
            name="Referencia normal",
        )
    )
    figura.update_layout(
        title="Gráfico Q-Q de los residuos",
        xaxis_title="Cuantiles normales teóricos",
        yaxis_title="Cuantiles de los residuos",
    )
    return figura