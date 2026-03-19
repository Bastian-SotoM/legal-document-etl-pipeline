# -*- coding: utf-8 -*-
"""
Ventana para Crear o Editar un Usuario.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import getpass # Para ocultar la entrada de contraseña

class UserEditorWindow(tk.Toplevel):
    def __init__(self, parent, user=None):
        super().__init__(parent)
        self.parent = parent
        self.user = user
        self.result = None

        self.title("Editar Usuario" if user else "Crear Nuevo Usuario")
        self.geometry("450x400")
        self.resizable(False, False)

        self._create_widgets()
        if self.user:
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

        # RUT
        ttk.Label(frame, text="RUT:").grid(row=2, column=0, sticky="w", pady=5)
        self.rut_entry = ttk.Entry(frame, width=40)
        self.rut_entry.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Email
        ttk.Label(frame, text="Email:").grid(row=4, column=0, sticky="w", pady=5)
        self.email_entry = ttk.Entry(frame, width=40)
        self.email_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Rol
        ttk.Label(frame, text="Rol:").grid(row=6, column=0, sticky="w", pady=5)
        self.rol_combobox = ttk.Combobox(frame, values=["Analista", "Administrador"], state="readonly")
        self.rol_combobox.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.rol_combobox.set("Analista") # Valor por defecto

        # Estado (solo para edición, no para creación inicial)
        if self.user:
            ttk.Label(frame, text="Estado:").grid(row=8, column=0, sticky="w", pady=5)
            self.estado_combobox = ttk.Combobox(frame, values=["Activo", "Inactivo"], state="readonly")
            self.estado_combobox.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 10))
            self.estado_combobox.set("Activo") # Valor por defecto

        # Contraseña (opcional para edición, requerido para creación)
        ttk.Label(frame, text="Contraseña (dejar vacío para no cambiar):").grid(row=10 if self.user else 8, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, show="*", width=40)
        self.password_entry.grid(row=11 if self.user else 9, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=12 if self.user else 10, column=0, columnspan=2, sticky="e", pady=10)
        ttk.Button(button_frame, text="Guardar", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _populate_data(self):
        self.nombre_entry.insert(0, self.user.nombre)
        self.rut_entry.insert(0, self.user.rut)
        self.email_entry.insert(0, self.user.email)
        self.rol_combobox.set(self.user.rol)
        if self.user: # Solo si estamos editando un usuario existente
            self.estado_combobox.set(self.user.estado)

    def _on_save(self):
        nombre = self.nombre_entry.get().strip()
        rut = self.rut_entry.get().strip()
        email = self.email_entry.get().strip()
        rol = self.rol_combobox.get()
        estado = self.estado_combobox.get() if self.user else "Activo" # Por defecto Activo al crear
        password = self.password_entry.get()

        if not nombre or not rut or not email or not rol:
            messagebox.showerror("Error de Validación", "Todos los campos (excepto contraseña) son obligatorios.", parent=self)
            return
        
        if not self.user and not password: # Si es un nuevo usuario, la contraseña es obligatoria
            messagebox.showerror("Error de Validación", "Para un nuevo usuario, la contraseña no puede estar vacía.", parent=self)
            return

        self.result = {
            "id": self.user.id if self.user else None,
            "nombre": nombre,
            "rut": rut,
            "email": email,
            "rol": rol,
            "estado": estado,
            "password": password # Se hasheará en db_manager si no está vacío
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()