# -*- coding: utf-8 -*-
"""
Módulo de Autenticación y Autorización

Contiene funciones para verificar usuarios y hashear contraseñas.
"""

import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Usuario

# --- Conexión a la Base de Datos ---
BD_PATH = "data/riesgo_patrimonial.db"
engine = create_engine(f"sqlite:///{BD_PATH}")
Session = sessionmaker(bind=engine)

def hashear_password(password):
    """Genera un hash seguro para la contraseña."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verificar_usuario(rut, password):
    """
    Verifica las credenciales de un usuario.
    Retorna el objeto Usuario si las credenciales son válidas y el usuario está activo,
    de lo contrario, retorna None.
    """
    from core.db_manager import log_user_action # Importación local para romper el ciclo
    session = Session()
    try:
        user = session.query(Usuario).filter_by(rut=rut).first()
        if user and user.estado == 'Activo':
            # Comparar el hash de la contraseña ingresada con el hash almacenado
            if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                log_user_action(user.id, "INICIO_SESION")
                return user
        return None
    except Exception as e:
        print(f"Error al verificar usuario: {e}")
        return None
    finally:
        session.close()