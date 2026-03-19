import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
file_path = r"C:\Users\bsoto\Downloads\ine_estimaciones-y-proyecciones-de-población-1992-2050_base-2017_tabulados.xlsx"

print("--- INICIANDO PROCESO DEFINITIVO ---")

try:
    # Cargar Excel
    df_pob = pd.read_excel(file_path, sheet_name='Población', header=6)
    
    # Normalizar nombres de columnas
    df_pob.columns = df_pob.columns.astype(str).str.strip()
    col_nombre = df_pob.columns[0]
    
    # ---------------------------------------------------------
    # CORRECCIÓN 1: CORTE DE TABLA (SOLO AMBOS SEXOS)
    # ---------------------------------------------------------
    # Buscamos el índice donde empieza "Hombres" para eliminar todo lo que sigue
    # Convertimos a string y buscamos 'hombres' ignorando mayúsculas
    idx_hombres = df_pob[df_pob[col_nombre].astype(str).str.lower().str.contains('hombres', na=False)].index
    
    if not idx_hombres.empty:
        corte = idx_hombres[0]
        print(f"✅ CORTE EXITOSO: Se detectó el inicio de 'Hombres' en la fila {corte}. Eliminando duplicados...")
        df_pob = df_pob.iloc[:corte].copy()
    else:
        print("⚠️ PRECAUCIÓN: No se encontró la palabra 'Hombres'. Se usará la tabla completa (riesgo de duplicados).")

    # ---------------------------------------------------------
    # CORRECCIÓN 2: RESCATAR "100+"
    # ---------------------------------------------------------
    # Reemplazamos "100+" por 100 para que se pueda sumar
    df_pob[col_nombre] = df_pob[col_nombre].astype(str).replace('100+', '100')

    # ---------------------------------------------------------
    # PROCESAMIENTO
    # ---------------------------------------------------------
    # Buscar Fila TOTAL (que está dentro del bloque cortado)
    fila_total = df_pob[df_pob[col_nombre].astype(str).str.strip() == 'Total']
    
    if fila_total.empty:
        raise ValueError("No se encontró la fila 'Total'.")

    # Convertir edades a números
    df_pob['Edad_Num'] = pd.to_numeric(df_pob[col_nombre], errors='coerce')
    df_edades = df_pob.dropna(subset=['Edad_Num'])

    anios_analisis = ['2017', '2025', '2035', '2050']
    resultados = {}

    print("[PROCESANDO] Calculando cifras...")
    
    for anio in anios_analisis:
        if anio in df_pob.columns:
            # Población Total (Dato oficial INE)
            pop_total_ine = fila_total[anio].values[0]
            
            # Sumas por grupos de edad
            pop_60 = df_edades[df_edades['Edad_Num'] >= 60][anio].sum()
            pop_80 = df_edades[df_edades['Edad_Num'] >= 80][anio].sum()
            
            # Cálculo del resto (Jóvenes) para que la barra sume exactamente el Total
            pop_menor_60 = pop_total_ine - pop_60
            
            resultados[anio] = {
                'Total': pop_total_ine,
                'Menor_60': pop_menor_60, 
                '60_79': pop_60 - pop_80,
                '80+': pop_80,
                '60+': pop_60,
                '% 60+': (pop_60 / pop_total_ine) * 100,
                '% 80+': (pop_80 / pop_total_ine) * 100
            }

    df_resumen = pd.DataFrame(resultados).T
    
    if not df_resumen.empty:
        years = df_resumen.index
        
        # ==========================================
        # GRÁFICO 1: NÚMEROS EXACTOS
        # ==========================================
        plt.figure(figsize=(12, 8))
        
        # Barras Apiladas
        p1 = plt.bar(years, df_resumen['Menor_60'], color='#e0e0e0', label='Menores de 60 años', width=0.5)
        p2 = plt.bar(years, df_resumen['60_79'], bottom=df_resumen['Menor_60'], color='#0275d8', label='Tercera Edad (60-79 años)', width=0.5)
        
        bottom_80 = df_resumen['Menor_60'] + df_resumen['60_79']
        p3 = plt.bar(years, df_resumen['80+'], bottom=bottom_80, color='#d9534f', label='Cuarta Edad (80+ años)', width=0.5)

        plt.title('Proyección Real de Población', fontsize=14, fontweight='bold')
        plt.ylabel('Población Total (Personas)', fontsize=12)
        plt.legend(loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=3)
        
        # Formato Miles en Eje Y
        plt.gca().get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,.0f}".format(x).replace(",", ".")))

        # ETIQUETAS TOTALES
        for i, year in enumerate(years):
            total_val = df_resumen['Total'].iloc[i]
            label = "{:,.0f}".format(total_val).replace(",", ".")
            plt.text(i, total_val + 200000, f"Total:\n{label}", ha='center', va='bottom', fontweight='bold', color='black', fontsize=10)

        # ETIQUETAS 80+
        for i, val in enumerate(df_resumen['80+']):
            if val > 0: 
                label = "{:,.0f}".format(val).replace(",", ".")
                pos = df_resumen['Menor_60'].iloc[i] + df_resumen['60_79'].iloc[i] + (val/2)
                plt.text(i, pos, label, ha='center', va='center', fontweight='bold', color='white', fontsize=9, 
                         path_effects=[path_effects.withStroke(linewidth=2, foreground="black")])

        # ETIQUETAS 60-79
        for i, val in enumerate(df_resumen['60_79']):
            label = "{:,.0f}".format(val).replace(",", ".")
            pos = df_resumen['Menor_60'].iloc[i] + (val/2)
            plt.text(i, pos, label, ha='center', va='center', fontweight='bold', color='white', fontsize=9,
                     path_effects=[path_effects.withStroke(linewidth=2, foreground="black")])

        plt.tight_layout()
        print("Mostrando Gráfico 1 (Corregido)...")
        plt.show()

        # ==========================================
        # GRÁFICO 2: PORCENTAJES
        # ==========================================
        plt.figure(figsize=(10, 6))
        
        pct_60 = df_resumen['% 60+']
        pct_80 = df_resumen['% 80+']

        plt.plot(years, pct_60, marker='o', color='#0275d8', linewidth=4, markersize=10, label='% Adultos Mayores (Total País)')
        plt.plot(years, pct_80, marker='s', color='#d9534f', linewidth=2, linestyle='--', markersize=8, label='% Cuarta Edad (Total País)')

        plt.title('Envejecimiento Relativo (% Real)', fontsize=14, fontweight='bold')
        plt.ylabel('Porcentaje', fontsize=12)
        plt.ylim(0, 40)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.legend()

        for i, v in enumerate(pct_60):
            plt.text(i, v + 1.5, f"{v:.1f}%", ha='center', fontweight='bold', color='#0275d8', 
                     bbox=dict(facecolor='white', edgecolor='#0275d8', boxstyle='round,pad=0.2'))

        for i, v in enumerate(pct_80):
            plt.text(i, v - 3, f"{v:.1f}%", ha='center', fontweight='bold', color='#d9534f')

        plt.tight_layout()
        print("Mostrando Gráfico 2 (Corregido)...")
        plt.show()

    else:
        print("Error: DataFrame vacío.")

except Exception as e:
    print(f"Error Crítico: {e}")