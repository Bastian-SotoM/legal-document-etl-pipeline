# -*- coding: utf-8 -*-
"""
Script de Migración de Datos

Este script corrige los registros existentes en la base de datos que tienen
el campo 'tribunal' vacío, asignándoles el valor por defecto 'Familia'.
"""

import os
import sys
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import CausaJudicial

BD_PATH = "data/riesgo_patrimonial.db"

def corregir_tribunales():
    """Busca y actualiza las causas con tribunal vacío."""
    engine = create_engine(f"sqlite:///{BD_PATH}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("Buscando causas con tribunal vacío para actualizar...")
        # Filtrar causas donde el tribunal es NULO o una cadena vacía
        causas_a_actualizar = session.query(CausaJudicial).filter(
            or_(CausaJudicial.tribunal == None, CausaJudicial.tribunal == '')
        )
        
        num_actualizadas = causas_a_actualizar.update({"tribunal": "Familia"}, synchronize_session=False)
        session.commit()
        
        print(f"✅ Proceso completado. Se actualizaron {num_actualizadas} causas.")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    corregir_tribunales()