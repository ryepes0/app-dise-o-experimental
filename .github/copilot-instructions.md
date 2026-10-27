# Instrucciones permanentes del repositorio

## Contexto del proyecto

- Este proyecto es una aplicación de Diseño Experimental desarrollada en Python y Streamlit para el curso de Diseño Experimental de Ingeniería Agrícola de la Universidad de Sucre.
- La estructura prevista es:
  - `app.py`: portada de la aplicación.
  - `pages/`: un archivo por cada diseño experimental.
  - `utils/`: funciones reutilizables; debe incluir `__init__.py`.
  - `data/`: archivos CSV de ejemplo.
  - `verificacion/`: scripts de R para verificar los análisis.

## Idioma y documentación

- Escribe en español todo el código nuevo, los comentarios, los docstrings y los mensajes de la interfaz.
- Añade en cada paso estadístico un comentario que explique qué se calcula y por qué, con lenguaje adecuado para estudiantes de Ingeniería Agrícola.
- Declara anotaciones de tipo (`type hints`) en las funciones.
- Documenta las funciones con docstrings en español que sigan el estilo Google.

## Dependencias

- Las únicas librerías permitidas son `streamlit`, `pandas`, `numpy`, `scipy`, `statsmodels`, `plotly` y `openpyxl`.
- No agregues otras dependencias sin pedir permiso explícito.

## Análisis estadístico

- Ajusta los modelos ANOVA con `statsmodels.formula.api.ols` y calcula la tabla ANOVA con `statsmodels.stats.anova.anova_lm(typ=2)`.
- Realiza las comparaciones de Tukey con `statsmodels.stats.multicomp.pairwise_tukeyhsd`.
- No inventes ni codifiques resultados estadísticos de ejemplo como si fueran resultados del análisis: todos los números presentados deben provenir del cálculo realizado con los datos.

## Validación de cambios

- Antes de terminar una tarea, ejecuta el código pertinente y corrige los errores que aparezcan.
- Si no es posible ejecutar una parte por falta de archivos, dependencias o datos, indícalo claramente y ejecuta las comprobaciones pertinentes que sí estén disponibles.