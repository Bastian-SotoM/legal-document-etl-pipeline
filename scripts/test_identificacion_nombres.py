# -*- coding: utf-8 -*-
"""
Script de Prueba para la Identificación de Nombres

Este script toma la ruta de un archivo PDF como argumento, extrae su texto
y ejecuta la función 'identificar_partes' para mostrar qué nombres y roles
se están detectando con la lógica actual.

Uso:
python scripts/test_identificacion_nombres.py "ruta/a/tu/archivo.pdf"
"""

import os
import sys

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import extraer_texto_pdf_con_ocr, identificar_partes

def probar_identificacion(ruta_pdf):
    """Prueba la lógica de identificación de partes en un solo PDF."""
    if not os.path.exists(ruta_pdf):
        print(f"❌ Error: El archivo no existe en la ruta: {ruta_pdf}")
        return

    print(f"📄 Analizando archivo: {os.path.basename(ruta_pdf)}")
    
    texto = extraer_texto_pdf_con_ocr(ruta_pdf)
    partes_encontradas = identificar_partes(texto)

    print("\n--- Resultados de la Identificación ---")
    if partes_encontradas:
        for rol, nombre in partes_encontradas.items():
            print(f"  - Rol: {rol.title()}, Nombre: '{nombre}'")
    else:
        print("  -> No se identificaron partes con la lógica actual.")
    print("-------------------------------------\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Por favor, proporciona la ruta al archivo PDF que deseas probar.")
        print("Ejemplo: python scripts/test_identificacion_nombres.py \"causas_archivadas/sentencia (1).pdf\"")
    else:
        ruta_del_pdf = sys.argv[1]
        probar_identificacion(ruta_del_pdf)