# -*- coding: utf-8 -*-
"""
Script de Migración de Datos

Este script recorre todas las causas existentes, vuelve a analizar el texto
de sus documentos con los patrones de nombres mejorados y actualiza el nombre
del adulto mayor si encuentra una versión más precisa.
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import CausaJudicial, AdultoMayor, DocumentoPDF
from core.db_manager import identificar_partes # Reutilizamos la función de identificación

BD_PATH = "data/riesgo_patrimonial.db"

def actualizar_nombres():
    """Busca y actualiza los nombres de los adultos mayores basándose en los nuevos patrones."""
    engine = create_engine(f"sqlite:///{BD_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Iniciando actualización de nombres de adultos mayores...")
        
        # Cargar todas las causas con sus documentos y adultos mayores asociados
        causas = session.query(CausaJudicial).options(
            joinedload(CausaJudicial.documentos),
            joinedload(CausaJudicial.adulto_mayor)
        ).all()

        actualizados = 0
        for causa in causas:
            if not causa.documentos or not causa.adulto_mayor:
                continue

            texto = causa.documentos[0].texto_extraido
            if not texto:
                continue

            # 1. Re-analizar el texto con los patrones mejorados
            partes_encontradas = identificar_partes(texto)
            
            # 2. Determinar el nombre del sujeto principal (priorizando 'victima')
            nombre_nuevo = None
            if 'victima' in partes_encontradas:
                nombre_nuevo = partes_encontradas['victima']
            elif 'demandante' in partes_encontradas:
                nombre_nuevo = partes_encontradas['demandante']
            elif partes_encontradas:
                nombre_nuevo = next(iter(partes_encontradas.values()))

            # 3. Comparar y actualizar si es necesario
            nombre_actual = causa.adulto_mayor.nombre
            if nombre_nuevo and nombre_nuevo.lower() != nombre_actual.lower():
                print(f"  -> Actualizando Causa RIT {causa.RIT}: '{nombre_actual}' -> '{nombre_nuevo}'")
                causa.adulto_mayor.nombre = nombre_nuevo
                actualizados += 1

        session.commit()
        print(f"\n✅ Proceso completado. Se actualizaron {actualizados} nombres.")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    actualizar_nombres()