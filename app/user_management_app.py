# -*- coding: utf-8 -*-
"""
Aplicación Independiente para la Gestión de Usuarios

Esta es una herramienta gráfica dedicada para que los administradores
puedan crear, editar y gestionar usuarios del sistema.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Asegurarnos de que el script pueda encontrar los módulos de 'core' y 'ui'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_manager import cargar_todos_los_usuarios, guardar_usuario, toggle_usuario_status
from app.ui.user_editor_window import UserEditorWindow

class UserManagementApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Herramienta de Gestión de Usuarios")
        self.geometry("800x500")

        # NOTA: Esta herramienta asume que se ejecuta con privilegios de administrador.
        # Para la auditoría, se registra que el usuario con ID 1 (el primer admin creado)
        # es quien realiza las acciones. En un sistema más complejo, esta app
        # tendría su propio login para identificar al administrador específico.
        self.admin_user_id = 1 

        self._create_widgets()
        self.refresh_users_list()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Frame de Botones ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Crear Nuevo Usuario", command=self.on_create_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Editar Usuario Seleccionado", command=self.on_edit_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Activar/Desactivar Usuario", command=self.on_toggle_user_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Actualizar Lista", command=self.refresh_users_list).pack(side=tk.RIGHT, padx=5)

        # --- Tabla de Usuarios (Treeview) ---
        tree_frame = ttk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("id", "nombre", "rut", "email", "rol", "estado")
        self.users_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.users_tree.heading("id", text="ID"); self.users_tree.column("id", width=50, anchor=tk.CENTER)
        self.users_tree.heading("nombre", text="Nombre")
        self.users_tree.heading("rut", text="RUT")
        self.users_tree.heading("email", text="Email")
        self.users_tree.heading("rol", text="Rol"); self.users_tree.column("rol", width=100, anchor=tk.CENTER)
        self.users_tree.heading("estado", text="Estado"); self.users_tree.column("estado", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.users_tree.bind("<Double-1>", lambda e: self.on_edit_user())

    def refresh_users_list(self):
        """Limpia y recarga la lista de usuarios."""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        users = cargar_todos_los_usuarios()
        for user in users:
            self.users_tree.insert("", tk.END, iid=user.id, values=(
                user.id, user.nombre, user.rut, user.email, user.rol, user.estado
            ))

    def on_create_user(self):
        """Abre la ventana para crear un nuevo usuario."""
        editor = UserEditorWindow(self)
        if editor.result:
            success, message = guardar_usuario(editor.result, self.admin_user_id)
            if success:
                messagebox.showinfo("Éxito", message, parent=self)
                self.refresh_users_list()
            else:
                messagebox.showerror("Error", message, parent=self)

    def on_edit_user(self):
        """Abre la ventana para editar el usuario seleccionado."""
        selected_items = self.users_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un usuario de la lista para editar.", parent=self)
            return
        
        user_id = selected_items[0]
        users = cargar_todos_los_usuarios()
        user_to_edit = next((u for u in users if u.id == int(user_id)), None)

        if user_to_edit:
            editor = UserEditorWindow(self, user_to_edit)
            if editor.result:
                success, message = guardar_usuario(editor.result, self.admin_user_id)
                if success:
                    messagebox.showinfo("Éxito", message, parent=self)
                    self.refresh_users_list()
                else:
                    messagebox.showerror("Error", message, parent=self)

    def on_toggle_user_status(self):
        """Cambia el estado del usuario seleccionado."""
        selected_items = self.users_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un usuario para cambiar su estado.", parent=self)
            return

        user_id = selected_items[0]
        confirmacion = messagebox.askyesno("Confirmar Cambio de Estado", "¿Estás seguro de que deseas cambiar el estado de este usuario?", parent=self)
        if not confirmacion:
            return
        
        success, message = toggle_usuario_status(int(user_id), self.admin_user_id)
        messagebox.showinfo("Resultado", message, parent=self) if success else messagebox.showerror("Error", message, parent=self)
        self.refresh_users_list()

if __name__ == "__main__":
    app = UserManagementApp()
    app.mainloop()