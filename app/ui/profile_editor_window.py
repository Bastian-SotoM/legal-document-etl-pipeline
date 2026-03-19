# -*- coding: utf-8 -*-
"""
Ventana para que un usuario edite su propio perfil.
"""

import tkinter as tk
from tkinter import ttk, messagebox

class ProfileEditorWindow(tk.Toplevel):
    def __init__(self, parent, user):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.result = None

        self.title("Editar Mi Perfil")
        self.geometry("450x300")
        self.resizable(False, False)

        self._create_widgets()
        self._populate_data()

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        parent.wait_window(self)

    def _create_widgets(self):
        frame = ttk.Frame(self, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Nombre
        ttk.Label(frame, text="Nombre Completo:").grid(row=0, column=0, sticky="w", pady=5)
        self.nombre_entry = ttk.Entry(frame, width=40)
        self.nombre_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Email
        ttk.Label(frame, text="Email:").grid(row=2, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(frame, width=40)
        self.email_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Contraseña
        ttk.Label(frame, text="Nueva Contraseña (dejar vacío para no cambiar):").grid(row=4, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, show="*", width=40)
        self.password_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=20)
        ttk.Button(button_frame, text="Guardar Cambios", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT)

        frame.columnconfigure(0, weight=1)

    def _populate_data(self):
        self.nombre_entry.insert(0, self.user.nombre)
        self.email_entry.insert(0, self.user.email)

    def _on_save(self):
        nombre = self.nombre_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()

        if not nombre or not email:
            messagebox.showerror("Error de Validación", "El nombre y el email no pueden estar vacíos.", parent=self)
            return

        self.result = {
            "id": self.user.id,
            "nombre": nombre,
            "rut": self.user.rut, # El RUT no se puede cambiar
            "email": email,
            "rol": self.user.rol, # El Rol no se puede cambiar
            "estado": self.user.estado, # El Estado no se puede cambiar
            "password": password
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()