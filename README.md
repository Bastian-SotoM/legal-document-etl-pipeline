# ⚖️ Sistema Inteligente de Análisis y Asignación de Programas (Adultos Mayores)

### **Proyecto de Memoria de Título | Ingeniería Civil en Informática y Telecomunicaciones**
*Universidad Finis Terrae, 2025*

---

## 🚀 La Problemática

El proyecto aborda un desafío crítico en la gestión pública: la transformación de datos **no estructurados** (causas judiciales en formato PDF) en información accionable. Este sistema automatiza la extracción de texto mediante OCR, evalúa el riesgo patrimonial y asigna eficientemente a los adultos mayores a los programas sociales de la red estatal.

---

## 📊 Flujo de Funcionamiento del Sistema (Data Pipeline)

A continuación, se presenta el diagrama de arquitectura del pipeline de datos y el motor analítico desarrollado:

```mermaid
graph TD
    %% Fuentes de Datos
    subgraph Fuentes ["1. Ingesta de Datos (No Estructurados)"]
        PDF[📄 Causas Judiciales en PDF]
    end

    %% Proceso ETL
    subgraph ETL ["2. Pipeline de Datos (ETL & NLP)"]
        OCR[⚙️ Motor OCR <br/>(Tesseract + PyMuPDF)]
        Regex[🔍 Motor de Reglas <br/>(Regex Engine)]
        ORM[🗄️ Capa de Persistencia <br/>(SQLAlchemy ORM)]
        DB[(🗄️ Base de Datos <br/>SQLite)]
    end

    %% Motor Analítico y ML
    subgraph Analisis ["3. Motor Analítico & Machine Learning"]
        FE[🧠 Feature <br/>Engineering]
        ML[🤖 Modelos Predictivos <br/>(Random Forest, RFN, K-Means)]
    end

    %% Salida y Decisiones
    subgraph Salida ["4. Asignación y Salida"]
        Match[⚖️ Matching <br/>Engine (Geoespacial)]
        App[💻 Interfaz de <br/>Usuario (Tkinter)]
        Reporte[📊 Reporte de <br/>Asignación Completo]
    end

    %% Conexiones
    PDF -->|Carga| OCR
    OCR -->|Texto Plano| Regex
    Regex -->|Metadatos Estructurados| ORM
    ORM -->|CRUD Operations| DB
    DB -->|Datos Limpios| FE
    FE -->|Vectores de Características| ML
    ML -->|Nivel de Riesgo Predictivo| Match
    Match -->|Resultados de Cruce| App
    App -->|Visualización| Reporte

    %% Estilos (Opcional para GitHub)
    classDef fuente fill:#f9f,stroke:#333,stroke-width:2px;
    classDef proceso fill:#ccf,stroke:#333,stroke-width:2px;
    classDef analitica fill:#ff9,stroke:#333,stroke-width:2px;
    classDef salida fill:#bbf,stroke:#333,stroke-width:2px;

    class PDF fuente;
    class OCR,Regex,ORM,DB proceso;
    class FE,ML analitica;
    class Match,App,Reporte salida;
