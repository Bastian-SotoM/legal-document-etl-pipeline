# -*- coding: utf-8 -*-
"""
Ventana para Crear o Editar un Programa Social.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import sys, os
# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.db_manager import cargar_todas_variables

class ProgramEditorWindow(tk.Toplevel):
    def __init__(self, parent, programa=None):
        super().__init__(parent)
        self.parent = parent
        self.programa = programa
        self.result = None

        self.title("Editar Programa" if programa else "Crear Nuevo Programa")
        self.geometry("900x600")

        self.all_variables = cargar_todas_variables()
        self._create_widgets()
        if self.programa:
            self._populate_data()

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Nombre y Descripción
        info_frame = ttk.LabelFrame(main_frame, text="Información General", padding="10")
        info_frame.pack(fill=tk.X, pady=5)

        ttk.Label(info_frame, text="Nombre del Programa:").grid(row=0, column=0, sticky="w")
        self.nombre_entry = ttk.Entry(info_frame, width=50)
        self.nombre_entry.grid(row=0, column=1, sticky="ew", padx=5)

        ttk.Label(info_frame, text="Descripción:").grid(row=1, column=0, sticky="nw", pady=5)
        self.desc_text = tk.Text(info_frame, height=3, width=50)
        self.desc_text.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Selección de Variables
        vars_frame = ttk.Frame(main_frame)
        vars_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Lista de Variables Disponibles
        left_frame = ttk.LabelFrame(vars_frame, text="Variables Disponibles", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.available_list = tk.Listbox(left_frame, selectmode=tk.MULTIPLE)
        sb_y = ttk.Scrollbar(left_frame, orient="vertical", command=self.available_list.yview)
        sb_x = ttk.Scrollbar(left_frame, orient="horizontal", command=self.available_list.xview)
        self.available_list.config(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.available_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Botones de Movimiento
        btn_frame = ttk.Frame(vars_frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(btn_frame, text="Clave >>", command=self._add_clave).pack(pady=5)
        ttk.Button(btn_frame, text="<< Quitar", command=self._remove_clave).pack(pady=5)
        ttk.Separator(btn_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="Contexto >>", command=self._add_contexto).pack(pady=5)
        ttk.Button(btn_frame, text="<< Quitar", command=self._remove_contexto).pack(pady=5)

        # Listas de Variables Seleccionadas
        right_frame = ttk.Frame(vars_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Variables Clave
        clave_frame = ttk.LabelFrame(right_frame, text="Variables Clave (+2 pts)", padding="5")
        clave_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.clave_list = tk.Listbox(clave_frame, selectmode=tk.MULTIPLE, bg="#e6fffa")
        
        sb_clave_y = ttk.Scrollbar(clave_frame, orient="vertical", command=self.clave_list.yview)
        sb_clave_x = ttk.Scrollbar(clave_frame, orient="horizontal", command=self.clave_list.xview)
        self.clave_list.config(yscrollcommand=sb_clave_y.set, xscrollcommand=sb_clave_x.set)
        sb_clave_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_clave_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.clave_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Variables Contexto
        contexto_frame = ttk.LabelFrame(right_frame, text="Variables Contexto (+1 pto)", padding="5")
        contexto_frame.pack(fill=tk.BOTH, expand=True)
        self.contexto_list = tk.Listbox(contexto_frame, selectmode=tk.MULTIPLE, bg="#fffaf0")
        
        sb_contexto_y = ttk.Scrollbar(contexto_frame, orient="vertical", command=self.contexto_list.yview)
        sb_contexto_x = ttk.Scrollbar(contexto_frame, orient="horizontal", command=self.contexto_list.xview)
        self.contexto_list.config(yscrollcommand=sb_contexto_y.set, xscrollcommand=sb_contexto_x.set)
        sb_contexto_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_contexto_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.contexto_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Poblar disponibles
        for var in self.all_variables:
            self.available_list.insert(tk.END, var.nombre)

        # Botones de Acción
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        ttk.Button(action_frame, text="Guardar Programa", command=self._on_save).pack(side=tk.RIGHT, padx=5)
        ttk.Button(action_frame, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT)

    def _populate_data(self):
        self.nombre_entry.insert(0, self.programa.nombre)
        self.desc_text.insert("1.0", self.programa.descripcion or "")
        
        vars_clave = json.loads(self.programa.variables_clave)
        vars_contexto = json.loads(self.programa.variables_contexto)

        for var in vars_clave:
            self.clave_list.insert(tk.END, var)
        for var in vars_contexto:
            self.contexto_list.insert(tk.END, var)

    def _add_clave(self): self._move_items(self.available_list, self.clave_list)
    def _remove_clave(self): self._move_items(self.clave_list, None) # Solo borrar
    def _add_contexto(self): self._move_items(self.available_list, self.contexto_list)
    def _remove_contexto(self): self._move_items(self.contexto_list, None)

    def _move_items(self, source, target):
        selected = source.curselection()
        for i in reversed(selected):
            item = source.get(i)
            if target:
                # Evitar duplicados
                if item not in target.get(0, tk.END):
                    target.insert(tk.END, item)
            elif source != self.available_list:
                # Si estamos borrando de clave/contexto, no hacemos nada especial, solo borrar
                pass
            
            # Si movemos desde available, no borramos (opcional, pero mejor mantenerlas visibles)
            # Si movemos desde clave/contexto hacia "quitar", se borran de la lista origen
            if source != self.available_list:
                source.delete(i)

    def _on_save(self):
        nombre = self.nombre_entry.get().strip()
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio.")
            return

        clave = list(self.clave_list.get(0, tk.END))
        contexto = list(self.contexto_list.get(0, tk.END))

        self.result = {
            "id": self.programa.id if self.programa else None,
            "nombre": nombre,
            "descripcion": self.desc_text.get("1.0", tk.END).strip(),
            "variables_clave": clave,
            "variables_contexto": contexto
        }
        self.destroy()