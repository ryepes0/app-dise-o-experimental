# App de Diseño Experimental

Aplicación educativa desarrollada en Python y Streamlit para el curso de Diseño Experimental de Ingeniería Agrícola de la Universidad de Sucre. Permite organizar datos de ensayos agrícolas y apoyar el aprendizaje de los diseños experimentales y su análisis.

## Módulos

| Módulo | Diseño | Estado |
| --- | --- | --- |
| DCA | Diseño completamente al azar | Disponible |
| DBCA | Diseño de bloques completos al azar | En construcción |
| DCL | Diseño de cuadrado latino | En construcción |
| DPD | Diseño de parcelas divididas | En construcción |
| Factoriales | Diseños factoriales | En construcción |
| RSM | Metodología de superficie de respuesta | En construcción |

## Estructura

```text
.
├── app.py                         # Portada de la aplicación
├── pages/                         # Una página por diseño experimental
├── utils/                         # Funciones reutilizables para análisis y gráficos
├── data/                          # Datos de ejemplo y archivos de entrada
│   └── dca_secadores.csv          # Ejemplo usado por el módulo DCA
├── verificacion/                  # Scripts para contrastar análisis con R
│   └── verificacion_dca.R         # Lee data/dca_mi_variante.csv
└── requirements.txt               # Dependencias de Python
```

El script de verificación espera que el usuario coloque su archivo `dca_mi_variante.csv` en `data/`; ese archivo no forma parte del repositorio.

## Instalación y ejecución

### Local en Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

### GitHub Codespaces

```bash
pip install -r requirements.txt
streamlit run app.py --server.headless true
```

Codespaces mostrará la aplicación en el puerto reenviado `8501`.

### Verificación con R

Después de guardar `data/dca_mi_variante.csv`, desde la carpeta `verificacion/` ejecute:

```bash
Rscript verificacion_dca.R
```

Este script contrasta el análisis del DCA con `aov`, muestra las medias por secador, calcula el coeficiente de variación y aplica Tukey.

## Autoría y uso de inteligencia artificial

- **Autor:** pendiente de completar; reemplazar `Escribe aquí tu nombre` en `app.py` por el nombre del estudiante o equipo.
- **Uso de IA:** se utilizó GitHub Copilot como asistencia para crear y revisar estructura, documentación y código. El autor debe verificar el contenido, comprender los análisis y asumir la responsabilidad académica de los resultados.