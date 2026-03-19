# -*- coding: utf-8 -*-
"""
Punto de Entrada Principal de la Aplicación

Este script lanza la aplicación, gestionando el flujo de login
y la apertura de la ventana principal.
"""

from ui.login_window import LoginWindow
from ui.main_window import MainWindow

def main():
    # 1. Iniciar la ventana de login y esperar a que se cierre
    login_app = LoginWindow()
    logged_user = login_app.start()

    # 2. Si el login fue exitoso, lanzar la app principal
    if logged_user:
        print("Lanzando aplicación principal...")
        main_app = MainWindow(logged_user)
        main_app.mainloop()
    else:
        print("Login cancelado o fallido. Saliendo de la aplicación.")

if __name__ == "__main__":
    main()