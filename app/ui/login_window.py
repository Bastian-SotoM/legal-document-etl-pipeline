# -*- coding: utf-8 -*-
"""
Ventana de Inicio de Sesión (Login)

Esta es la primera ventana que ve el usuario para autenticarse.
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.auth import verificar_usuario, hashear_password # hashear_password no se usa aquí, pero es buena práctica tenerla si se necesitara en el futuro

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.logged_in_user = None
        self.title("Sistema de Riesgo - Inicio de Sesión")
        self.geometry("350x200")
        self.resizable(False, False)

        # Centrar la ventana
        self.eval('tk::PlaceWindow . center')

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # --- RUT ---
        ttk.Label(main_frame, text="RUT:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.rut_entry = ttk.Entry(main_frame, width=30)
        self.rut_entry.grid(row=0, column=1, sticky=tk.EW)
        self.rut_entry.focus()

        # --- Contraseña ---
        ttk.Label(main_frame, text="Contraseña:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(main_frame, show="*", width=30)
        self.password_entry.grid(row=1, column=1, sticky=tk.EW)

        # --- Botón de Login ---
        login_button = ttk.Button(main_frame, text="Ingresar", command=self._on_login)
        login_button.grid(row=2, column=0, columnspan=2, pady=20)

        # Vincular la tecla Enter al login
        self.bind('<Return>', self._on_login)

    def _on_login(self, event=None):
        """Maneja el evento de clic en el botón de login."""
        rut = self.rut_entry.get().strip()
        password = self.password_entry.get()

        if not rut or not password:
            messagebox.showerror("Error", "Debe ingresar RUT y contraseña.")
            return

        user = verificar_usuario(rut, password)

        if user:
            print(f"✅ Inicio de sesión exitoso para el usuario: {user.nombre} (Rol: {user.rol})")
            self.logged_in_user = user
            self.destroy() # Cierra la ventana de login
        else:
            messagebox.showerror("Error de Autenticación", "RUT o contraseña incorrectos, o usuario inactivo.")
            self.password_entry.delete(0, tk.END)

    def start(self):
        """Inicia el bucle principal de la ventana de login."""
        self.mainloop()
        # Después de que la ventana se destruye, devuelve el usuario logueado
        return self.logged_in_user