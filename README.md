# ⚖️ Sistema de Inteligencia de Datos: Análisis y Asignación de Programas (Adultos Mayores)
**Memoria de Título - Ingeniería Civil en Informática y Telecomunicaciones** *Universidad Finis Terrae, 2025*

## 🚀 Visión General
Este proyecto resuelve un problema crítico de gestión pública: la transformación de datos no estructurados provenientes de **causas judiciales (PDFs)** en activos de datos accionables. Desarrollé un **Data Pipeline (ETL)** robusto que utiliza OCR y técnicas de **NLP (Natural Language Processing)** para automatizar la evaluación de riesgo patrimonial y la asignación eficiente de recursos estatales.

## 🛠️ Ingeniería de Datos y Backend (Core)
* **Ingesta de Datos No Estructurados:** Implementación de un motor de extracción híbrido (**PyMuPDF + Tesseract OCR**) para la digitalización y parsing de documentos legales complejos.
* **Procesamiento y Limpieza (Regex Engine):** Diseño de un motor de expresiones regulares avanzado para la normalización de metadatos (RIT, fechas, comunas) y detección de patrones de riesgo.
* **Capa de Persistencia (ORM):** Arquitectura de base de datos relacional gestionada mediante **SQLAlchemy**, garantizando la integridad referencial y escalabilidad del modelo de datos.

## 🤖 Analítica Avanzada y Machine Learning
El sistema integra un pipeline de ciencia de datos para la toma de decisiones:
* **Feature Engineering:** Extracción de variables clave desde el texto procesado.
* **Modelado Predictivo:** Implementación y evaluación de modelos (**Random Forest, Redes Neuronales y K-Means**) utilizando **Scikit-Learn** para clasificar niveles de vulnerabilidad.
* **Matching Engine:** Algoritmo de cruce geoespacial para la asignación automática basada en perfiles sociodemográficos.

## 📦 Stack Tecnológico
* **Lenguaje:** Python 3.x
* **Data Stack:** Pandas, Scikit-Learn, SQLAlchemy
* **OCR/Document Analysis:** Tesseract, PyMuPDF, pdf2image
* **UI:** Tkinter (Desktop Interface)
