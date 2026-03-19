# -*- coding: utf-8 -*-
import os
# Solución para el problema de "congelamiento" de KMeans en Windows
# Se debe colocar ANTES de importar numpy o scikit-learn
os.environ["OMP_NUM_THREADS"] = "1"

import sys
import pandas as pd
import joblib
import matplotlib.pyplot as plt
import warnings
import numpy as np

from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, RocCurveDisplay, accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import KMeans
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Importar configuraciones
from core.config import PESOS_VARIABLES, UMBRALES_RIESGO, NOMBRES_VARIABLES

warnings.filterwarnings("ignore")

# === CONFIGURACIÓN ===
BD_PATH = "data/riesgo_patrimonial.db"
OUTPUT_DIR = "model_outputs"
TARGET_COLUMN = "riesgo_nivel" # 'riesgo_nivel' (0, 1, 2) o 'riesgo_binario' (0, 1)

# Crear carpeta de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === 1. CARGA Y PREPARACIÓN DE DATOS ===

def cargar_datos_desde_bd(db_path):
    """
    Carga los datos desde la base de datos SQLite y los transforma en un DataFrame de features.
    """
    engine = create_engine(f"sqlite:///{db_path}")
    
    # --- Verificación de datos ---
    if pd.read_sql("SELECT COUNT(*) FROM evaluacion_riesgo", engine).iloc[0,0] == 0:
        print("❌ Error: La tabla 'evaluacion_riesgo' está vacía.")
        print("Asegúrate de ejecutar 'poblar_bd.py' antes de entrenar los modelos.")
        return None, None

    # Cargar las tablas principales
    causas = pd.read_sql("SELECT id, RIT, adulto_id FROM causa_judicial", engine)
    evaluaciones = pd.read_sql("SELECT id, causa_id FROM evaluacion_riesgo", engine)
    eval_vars = pd.read_sql("SELECT evaluacion_id, variable_id FROM evaluacion_variable", engine)
    variables = pd.read_sql("SELECT id, nombre FROM variable_riesgo", engine)
    
    # Unir las tablas para obtener las variables por causa
    df = pd.merge(evaluaciones, eval_vars, left_on='id', right_on='evaluacion_id')
    df = pd.merge(df, variables, left_on='variable_id', right_on='id', suffixes=('_eval', '_var')) # id -> id_eval, id_var
    causas.rename(columns={'id': 'id_causa'}, inplace=True) # Renombrar explícitamente
    df = pd.merge(causas, df, left_on='id_causa', right_on='causa_id')
    
    # Pivotar para crear un feature por cada variable de riesgo (one-hot encoding)
    features_df = pd.pivot_table(df, index='id_causa', columns='nombre', aggfunc='size', fill_value=0).reset_index()
    features_df.rename(columns={'id_causa': 'causa_id'}, inplace=True)
    
    # Asegurar que todas las variables definidas en config.py (NOMBRES_VARIABLES) estén como columnas en features_df
    # y en el orden definido en NOMBRES_VARIABLES.
    for var_name in NOMBRES_VARIABLES: 
        if var_name not in features_df.columns:
            features_df[var_name] = 0

    # Calcular puntaje ponderado
    features_df['puntaje_riesgo'] = 0
    for var_name, peso in PESOS_VARIABLES.items():
        if var_name in features_df.columns:
            # Suma el peso solo si la variable está presente (valor 1)
            features_df['puntaje_riesgo'] += features_df[var_name] * peso

    
    labels = [0, 1, 2]
    bins = UMBRALES_RIESGO
    # Usamos right=False para que el intervalo sea [inicio, fin) y coincida con la lógica de umbrales
    features_df['riesgo_nivel'] = pd.cut(features_df['puntaje_riesgo'], bins=bins, labels=labels, right=False)
    
    # Crear riesgo binario (Alto vs. No Alto)
    features_df['riesgo_binario'] = (features_df['riesgo_nivel'] == 2).astype(int)
    
    print(f"Dataset creado con {len(features_df)} causas y {len(NOMBRES_VARIABLES)} variables de riesgo.")
    print("\nDistribución de niveles de riesgo:")
    print(features_df['riesgo_nivel'].value_counts())
    
    return features_df, NOMBRES_VARIABLES # Retornar NOMBRES_VARIABLES como la lista de features para consistencia


# === 2. ENTRENAMIENTO Y EVALUACIÓN DE MODELOS ===

def evaluar_modelo(nombre, pipeline, X, y, X_test, y_test, labels, target_names):
    """
    Evalúa un modelo entrenado y guarda sus métricas y artefactos.
    """
    print(f"\n--- Evaluando Modelo: {nombre} ---")
    
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)
    
    # Reporte de clasificación
    report = classification_report(y_test, y_pred, labels=labels, target_names=target_names)
    # Usar zero_division=0 para evitar warnings si una clase no tiene predicciones
    report_dict = classification_report(y_test, y_pred, labels=labels, target_names=target_names, output_dict=True, zero_division=0)
    report_str = classification_report(y_test, y_pred, labels=labels, target_names=target_names, zero_division=0)
    
    print(report_str)

    
    # Añadir Validación Cruzada para robustez académica
    try:
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy')
        print(f"\nValidación Cruzada (Accuracy): {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}")
    except Exception as e:
        print(f"\nNo se pudo realizar la validación cruzada: {e}")

    # Guardar reporte
    with open(os.path.join(OUTPUT_DIR, f"report_{nombre}.txt"), "w") as f:
        f.write(report_str)
        f.write("\nMatriz de Confusión:\n")
        f.write(str(confusion_matrix(y_test, y_pred)))

    # Curva ROC (para clasificación multiclase con One-vs-Rest)
    try:
        fig, ax = plt.subplots(figsize=(8, 6))
        y_test_binarized = pd.get_dummies(y_test, columns=labels).reindex(columns=labels, fill_value=0)

        for i, class_name in enumerate(target_names):
            if i < y_proba.shape[1]:
                display = RocCurveDisplay.from_predictions(
                    y_test_binarized.iloc[:, i],
                    y_proba[:, i],
                    name=f"ROC para clase '{class_name}'",
                    ax=ax,
                )
        plt.title(f"Curvas ROC (One-vs-Rest) - {nombre}")
        plt.savefig(os.path.join(OUTPUT_DIR, f"roc_{nombre}.png"))
        plt.close()
    except Exception as e:
        print(f"No se pudo generar la curva ROC para {nombre}: {e}")

    # Guardar modelo
    joblib.dump(pipeline, os.path.join(OUTPUT_DIR, f"modelo_{nombre}.joblib"))
    print(f"✅ Modelo '{nombre}' guardado en '{OUTPUT_DIR}/'")
    

# === 3. EJECUCIÓN DEL PIPELINE ===

def main():
    # Cargar y preparar datos
    df, feature_cols = cargar_datos_desde_bd(BD_PATH)
    
    if df is None or df.empty or TARGET_COLUMN not in df.columns:
        # El mensaje de error ya se muestra en cargar_datos_desde_bd
        return
    
    # Asegurar que X contenga las columnas de NOMBRES_VARIABLES en el orden correcto.
    # Esto es crucial para la consistencia entre entrenamiento y predicción.
    X = df[NOMBRES_VARIABLES] 
    y = df[TARGET_COLUMN]

    # Salvaguarda: Verificar si hay al menos 2 clases para entrenar
    if y.nunique() < 2:
        print(f"\n❌ ERROR: El conjunto de datos solo contiene una clase de riesgo ({y.unique()}).")
        print("No se puede entrenar un modelo de clasificación. Revisa los umbrales en 'config.py' o la data de entrada.")
        return

    # Comprobar si la estratificación es posible
    min_class_count = y.value_counts().min()
    stratify_option = y if min_class_count >= 2 else None
    if stratify_option is None:
        print("\n⚠️ Advertencia: La clase menos poblada tiene menos de 2 muestras. No se usará estratificación.")


    # Definir etiquetas y nombres para los reportes
    riesgo_labels = [0, 1, 2]
    riesgo_target_names = ['Bajo', 'Medio', 'Alto']

    # Dividir datos en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=stratify_option
    )

    # --- Modelo 1: Regresión Logística ---
    pipeline_lr = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(random_state=42, multi_class='ovr', solver='liblinear'))
    ])
    pipeline_lr.fit(X_train, y_train)
    evaluar_modelo("RegresionLogistica", pipeline_lr, X, y, X_test, y_test, riesgo_labels, riesgo_target_names)

    # --- Modelo 2: Random Forest ---
    pipeline_rf = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', RandomForestClassifier(random_state=42, n_estimators=100))
    ])
    pipeline_rf.fit(X_train, y_train)
    evaluar_modelo("RandomForest", pipeline_rf, X, y, X_test, y_test, riesgo_labels, riesgo_target_names)

    # Extraer importancia de variables del Random Forest
    importances = pipeline_rf.named_steps['clf'].feature_importances_
    feature_importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values(by='importance', ascending=False)
    print("\n--- Importancia de Variables (Random Forest) ---")
    print(feature_importance_df.head(10))
    feature_importance_df.to_csv(os.path.join(OUTPUT_DIR, "feature_importance_rf.csv"), index=False)

    # --- Modelo 3: Red Neuronal (ANN) ---
    pipeline_ann = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', MLPClassifier(random_state=42, hidden_layer_sizes=(50, 25), max_iter=500, early_stopping=False)) # Se desactiva early_stopping
    ])
    pipeline_ann.fit(X_train, y_train)
    evaluar_modelo("RedNeuronal", pipeline_ann, X, y, X_test, y_test, riesgo_labels, riesgo_target_names)

    # --- Modelo 4: Clustering (K-Means) ---
    print("\n--- Ejecutando Modelo de Clustering (K-Means) ---")
    print(f"Shape of X for KMeans: {X.shape}")
    if X.empty:
        print("❌ Error: El DataFrame de características (X) está vacío. No se puede ejecutar K-Means.")
        return
    if X.isnull().any().any():
        print("⚠️ Advertencia: X contiene valores NaN. K-Means podría fallar o comportarse de forma inesperada.")
        print(X.isnull().sum()[X.isnull().sum() > 0])
    if np.isinf(X).any().any():
        print("⚠️ Advertencia: X contiene valores Inf. K-Means podría fallar o comportarse de forma inesperada.")

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(X)
    print("✅ K-Means completado.")
    
    # Analizar los clusters
    cluster_analysis = df.groupby('cluster')[feature_cols].mean().T
    print("Análisis de centroides de clusters (variables más representativas por cluster):")
    print(cluster_analysis)
    cluster_analysis.to_csv(os.path.join(OUTPUT_DIR, "cluster_analysis_kmeans.csv"))
    
    # Guardar resultados del clustering
    df[['causa_id', 'riesgo_nivel', 'cluster']].to_csv(os.path.join(OUTPUT_DIR, "resultados_clustering.csv"), index=False)
    print("✅ Resultados de clustering guardados.")

    # --- Modelo 5: Híbrido (LogReg -> DecisionTree) ---
    print("\n--- Entrenando Modelo Híbrido ---")
    
    # Paso 1: Entrenar Regresión Logística para obtener probabilidades
    lr_hybrid = LogisticRegression(random_state=42, multi_class='ovr', solver='liblinear')
    X_train_scaled = StandardScaler().fit_transform(X_train)
    X_test_scaled = StandardScaler().fit_transform(X_test)
    lr_hybrid.fit(X_train_scaled, y_train)
    
    # Obtener probabilidades para el nivel de riesgo más alto (2) de forma segura
    proba_train_full = lr_hybrid.predict_proba(X_train_scaled)
    proba_test_full = lr_hybrid.predict_proba(X_test_scaled)
    
    # Encontrar el índice de la clase '2' (Alto Riesgo)
    clases_aprendidas = list(lr_hybrid.classes_) # Obtener las clases que el modelo vio durante el entrenamiento
    try:
        idx_alto_riesgo = clases_aprendidas.index(2)
        proba_train = proba_train_full[:, idx_alto_riesgo].reshape(-1, 1) # Asegurarse de que sea 2D
        proba_test = proba_test_full[:, idx_alto_riesgo].reshape(-1, 1)
    except ValueError:
        # Si la clase 2 no está en los datos de entrenamiento, usar una columna de ceros
        print("⚠️ Advertencia en Modelo Híbrido: La clase de 'Alto Riesgo' (2) no está en los datos de entrenamiento.")
        proba_train = np.zeros((X_train_scaled.shape[0], 1))
        proba_test = np.zeros((X_test_scaled.shape[0], 1))
    
    # Añadir la probabilidad como una nueva feature (asegurando que X_train/test sean DataFrames para hstack)
    X_train_hybrid = np.hstack([X_train.values, proba_train])
    X_test_hybrid = np.hstack([X_test.values, proba_test])
    
    # Paso 2: Entrenar un Árbol de Decisión con la nueva feature
    dt_hybrid = DecisionTreeClassifier(max_depth=5, random_state=42)
    dt_hybrid.fit(X_train_hybrid, y_train)
    
    # Evaluar el modelo híbrido
    y_pred_hybrid = dt_hybrid.predict(X_test_hybrid)
    print("\n--- Evaluación Modelo Híbrido ---")
    report_hybrid = classification_report(y_test, y_pred_hybrid, labels=riesgo_labels, target_names=riesgo_target_names, zero_division=0)
    print(report_hybrid)
    
    with open(os.path.join(OUTPUT_DIR, "report_Hibrido.txt"), "w") as f:
        f.write(report_hybrid)
        f.write("\nMatriz de Confusión:\n")
        f.write(str(confusion_matrix(y_test, y_pred_hybrid)))

    # Guardar los componentes del modelo híbrido
    joblib.dump(lr_hybrid, os.path.join(OUTPUT_DIR, "modelo_Hibrido_paso1_lr.joblib"))
    joblib.dump(dt_hybrid, os.path.join(OUTPUT_DIR, "modelo_Hibrido_paso2_dt.joblib"))
    print("✅ Modelo Híbrido guardado.")

if __name__ == "__main__":
    main()
