# Lee el archivo de variante preparado por el estudiante desde la carpeta data.
datos <- read.csv("../data/dca_mi_variante.csv", stringsAsFactors = FALSE) # Importa las columnas secador y humedad para contrastar el análisis.
# Ajusta el modelo de un diseño completamente al azar con el secador como factor.
modelo <- aov(humedad ~ factor(secador), data = datos) # Compara las medias de humedad de los secadores mediante ANOVA.
# Imprime el resumen del análisis de varianza para revisar la evidencia estadística.
print(summary(modelo)) # Muestra grados de libertad, cuadrados medios, estadístico F y valor p.
# Calcula la media de humedad observada para cada secador.
medias_secador <- aggregate(humedad ~ secador, data = datos, FUN = mean) # Resume la respuesta promedio de cada tratamiento.
# Imprime las medias calculadas por secador.
print(medias_secador) # Permite comparar descriptivamente los secadores.
# Recupera la tabla ANOVA del modelo para obtener el cuadrado medio del error.
tabla_anova <- summary(modelo)[[1]] # La fila Residual contiene la variación no explicada por el tratamiento.
# Extrae los grados de libertad residuales para documentar el error experimental.
gl_error <- tabla_anova["Residuals", "Df"] # Identifica los grados de libertad usados por el cuadrado medio del error.
# Extrae el cuadrado medio residual, que estima la varianza del error experimental.
cme <- tabla_anova["Residuals", "Mean Sq"] # Usa el CME como estimación de la variabilidad entre réplicas.
# Calcula la media general de humedad ignorando posibles valores faltantes.
media_general <- mean(datos$humedad, na.rm = TRUE) # Expresa la variabilidad residual en relación con el nivel medio de humedad.
# Calcula el coeficiente de variación como raíz del CME dividida por la media general por cien.
cv <- sqrt(cme) / media_general * 100 # CV = sqrt(CME) / media general * 100.
# Imprime el coeficiente de variación con cuatro decimales y su unidad porcentual.
cat(sprintf("Coeficiente de variación: %.4f%%\n", cv)) # Facilita valorar la variación experimental relativa.
# Ejecuta las comparaciones de Tukey para las medias del factor secador.
comparaciones_tukey <- TukeyHSD(modelo) # Ajusta las comparaciones por multiplicidad para controlar el error familiar.
# Imprime las diferencias, intervalos y decisiones de las comparaciones de Tukey.
print(comparaciones_tukey) # Ayuda a identificar qué pares de secadores presentan diferencias.