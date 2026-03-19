# Sistema de Análisis y Asignación de Programas para Adultos Mayores

Este proyecto es un **pipeline de datos (ETL) y sistema analítico** desarrollado en Python. Su objetivo principal es extraer, transformar y estructurar datos provenientes de fuentes no estructuradas (causas judiciales en formato PDF) mediante OCR y **Extracción de Información Basada en Reglas (Regex)** para evaluar el riesgo patrimonial y **asignar automáticamente a los adultos mayores a los programas sociales** de la red institucional del Estado.

## Características Destacadas (Data Engineering & Analytics)
- **Procesamiento de Datos No Estructurados (OCR y Parsing):** Extracción automatizada de texto desde documentos legales utilizando `PyMuPDF` y `Tesseract OCR`.
- **Transformación de Datos y Pattern Matching:** Limpieza de texto, extracción de metadatos (fechas, comunas, RIT) y detección de variables de riesgo mediante un motor de expresiones regulares (Regex) avanzado.
- **Modelado Relacional y ORM:** Diseño de una arquitectura de base de datos en SQLite gestionada mediante `SQLAlchemy` para asegurar la integridad referencial entre causas, personas, documentos y evaluaciones.
- **Motor de Reglas (Matching Engine):** Algoritmo de cruce de variables extraídas frente a perfiles de programas sociales con filtrado geoespacial.
- **Machine Learning Pipeline:** Script integrado para la extracción de *features*, entrenamiento, y evaluación de modelos predictivos (Random Forest, Redes Neuronales, K-Means) utilizando `pandas` y `scikit-learn`.

## Stack Tecnológico
- Python 3.x
- **Bases de Datos:** SQLite, SQLAlchemy (ORM)
- **Procesamiento de Datos / ML:** Pandas, Scikit-Learn, Matplotlib
- **Extracción de Texto:** PyMuPDF, Tesseract OCR, pdf2image
- **Interfaz (Frontend):** Tkinter

## Instalación
1. Clonar el repositorio.
2. Instalar las dependencias (ej. `pip install -r requirements.txt`).
3. Asegurar que Tesseract OCR esté instalado y agregado al PATH del sistema.
