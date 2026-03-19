# -*- coding: utf-8 -*-
"""
Script de Preparación de la Base de Datos

1. (Opcional) Limpia todas las tablas de la base de datos.
2. Crea el esquema de tablas si no existe.
3. Carga la lista inicial de variables de riesgo desde el archivo de configuración.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar modelos y configuración desde la nueva estructura
from core.models import Base, VariableRiesgo, Usuario
from core.config import DEFINICION_VARIABLES, PATRONES_VARIABLES

BD_PATH = "data/riesgo_patrimonial.db"

def preparar_base_de_datos(limpiar=False):
    """
    Crea las tablas y carga los datos iniciales.
    """
    # Crear la carpeta 'data' si no existe
    os.makedirs(os.path.dirname(BD_PATH), exist_ok=True)
    
    engine = create_engine(f"sqlite:///{BD_PATH}", echo=False)
    
    # Crear todas las tablas definidas en core/models.py
    print("\nCreando esquema de tablas si no existe...")
    Base.metadata.create_all(engine)
    print("✅ Esquema de tablas verificado/creado.")

    Session = sessionmaker(bind=engine)
    session = Session()

    if limpiar:
        print("\nLimpiando la base de datos...")
        # Limpiar la tabla de variables para asegurar consistencia
        session.query(VariableRiesgo).delete() # Esto se puede hacer más robusto
        # Aquí podrías añadir la limpieza de otras tablas si fuera necesario
        # session.query(Usuario).delete()
        session.commit()
        print("✅ Tablas principales limpiadas.")

    try:
        if session.query(VariableRiesgo).count() == 0:
            print("\nCargando variables de riesgo iniciales...")
            for var_info in DEFINICION_VARIABLES:
                v = VariableRiesgo(
                    nombre=var_info["nombre"], 
                    descripcion=var_info["descripcion"],
                    peso_relativo=var_info["peso"],
                    tipo='Agravante' if var_info["peso"] > 0 else 'Mitigante',
                    patrones="\n".join(PATRONES_VARIABLES.get(var_info["nombre"], []))
                )
                session.add(v)
            session.commit()
            print(f"✅ {len(DEFINICION_VARIABLES)} variables de riesgo cargadas correctamente desde config.py.")
        else:
            print("\nLas variables de riesgo ya existen en la base de datos.")
    except Exception as e:
        print(f"❌ Error al cargar variables: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Preguntar al usuario si desea limpiar la base de datos
    respuesta = input("¿Deseas limpiar y recargar las variables de riesgo? (s/n): ").lower()
    limpiar_bd = respuesta == 's'
    
    preparar_base_de_datos(limpiar=limpiar_bd)
    print("\n🎯 Proceso de preparación de la base de datos completado.")