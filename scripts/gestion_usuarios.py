# -*- coding: utf-8 -*-
"""
Herramienta de Línea de Comandos para la Gestión de Usuarios

Permite al administrador crear, modificar y habilitar/deshabilitar usuarios.
"""

import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import Usuario
from core.db_manager import cargar_todos_los_usuarios, guardar_usuario, toggle_usuario_status, log_user_action

# --- CONFIGURACIÓN ---
BD_PATH = "data/riesgo_patrimonial.db"
engine = create_engine(f"sqlite:///{BD_PATH}")
Session = sessionmaker(bind=engine)

def crear_usuario():
    """Función para registrar un nuevo usuario en el sistema."""
    print("\n--- Creación de Nuevo Usuario ---")
    try:
        nombre = input("Nombre completo: ")
        rut = input("RUT (sin puntos, con guión): ")
        email = input("Correo electrónico: ")
        rol = input("Rol (Administrador/Analista) [Analista]: ") or "Analista"

        password = getpass.getpass("Contraseña: ")
        password_confirm = getpass.getpass("Confirmar contraseña: ")

        if password != password_confirm:
            print("❌ Error: Las contraseñas no coinciden.")
            return

        user_data = {"id": None, "nombre": nombre, "rut": rut, "email": email, "rol": rol, "estado": "Activo", "password": password}
        
        # Usamos la lógica centralizada de db_manager
        # Para la creación inicial, no hay un "editor" como tal, pero podemos registrarlo como una acción del sistema o del primer admin.
        # Pasamos None para que la lógica de db_manager se encargue de asignar el ID del propio usuario creado.
        success, message = guardar_usuario(user_data, editor_usuario_id=None) 
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

def listar_usuarios():
    """Muestra una lista de todos los usuarios en el sistema."""
    print("\n--- Lista de Usuarios ---")
    users = cargar_todos_los_usuarios()
    if not users:
        print("No hay usuarios registrados.")
        return

    print(f"{'ID':<5} {'Nombre':<30} {'RUT':<15} {'Rol':<15} {'Estado':<10}")
    print("-" * 80)
    for user in users:
        print(f"{user.id:<5} {user.nombre:<30} {user.rut:<15} {user.rol:<15} {user.estado:<10}")

def modificar_usuario():
    """Permite modificar los datos de un usuario existente."""
    listar_usuarios()
    try:
        user_id = int(input("\nIntroduce el ID del usuario a modificar: "))
        users = cargar_todos_los_usuarios()
        user_to_edit = next((u for u in users if u.id == user_id), None)

        if not user_to_edit:
            print("❌ ID de usuario no encontrado.")
            return

        print("\n--- Modificando Usuario ---")
        print("Deja el campo en blanco para no modificar el valor.")

        nombre = input(f"Nombre [{user_to_edit.nombre}]: ") or user_to_edit.nombre
        email = input(f"Email [{user_to_edit.email}]: ") or user_to_edit.email
        rol = input(f"Rol (Administrador/Analista) [{user_to_edit.rol}]: ") or user_to_edit.rol
        
        cambiar_pass = input("¿Deseas cambiar la contraseña? (s/n): ").lower()
        password = ""
        if cambiar_pass == 's':
            password = getpass.getpass("Nueva Contraseña: ")
            password_confirm = getpass.getpass("Confirmar Nueva Contraseña: ")
            if password != password_confirm:
                print("❌ Las contraseñas no coinciden. No se guardarán los cambios.")
                return

        user_data = {
            "id": user_to_edit.id,
            "nombre": nombre,
            "rut": user_to_edit.rut, # El RUT no se puede cambiar
            "email": email,
            "rol": rol,
            "estado": user_to_edit.estado,
            "password": password
        }

        success, message = guardar_usuario(user_data, editor_usuario_id=1) # Asumimos que el admin (ID 1) ejecuta esto
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")

    except ValueError:
        print("❌ ID no válido. Debe ser un número.")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

def cambiar_estado_usuario():
    """Habilita o deshabilita un usuario."""
    listar_usuarios()
    try:
        user_id = int(input("\nIntroduce el ID del usuario para cambiar su estado: "))
        success, message = toggle_usuario_status(user_id, editor_usuario_id=1)
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")
    except ValueError:
        print("❌ ID no válido. Debe ser un número.")
    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")

def menu_principal():
    """Muestra el menú de opciones al administrador."""
    while True:
        print("\n--- Panel de Administración de Usuarios ---")
        print("1. Crear nuevo usuario")
        print("2. Modificar usuario")
        print("3. Habilitar/Deshabilitar usuario")
        print("4. Listar todos los usuarios")
        print("5. Salir")
        
        opcion = input("Selecciona una opción: ")

        if opcion == '1':
            crear_usuario()
        elif opcion == '2':
            modificar_usuario()
        elif opcion == '3':
            cambiar_estado_usuario()
        elif opcion == '4':
            listar_usuarios()
        elif opcion == '5':
            print("Saliendo del panel de administración.")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")

if __name__ == "__main__":
    # Aquí podrías añadir un login para el administrador del script
    print("Bienvenido al sistema de gestión de usuarios.")
    menu_principal()