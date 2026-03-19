# -*- coding: utf-8 -*-
"""
Ventana para Crear o Editar una Variable de Riesgo.

Incluye un asistente para generar patrones de búsqueda a partir de palabras clave.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.db_manager import generar_patrones_desde_palabras_clave, probar_patrones_en_db

class VariableEditorWindow(tk.Toplevel):
    def __init__(self, parent, variable=None):
        super().__init__(parent)
        self.parent = parent
        self.variable = variable
        self.result = None

        self.title("Editar Variable" if variable else "Crear Nueva Variable")
        self.geometry("800x700") # Aumentamos el tamaño para el asistente

        self._create_widgets()
        if self.variable:
            self._populate_data()

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        parent.wait_window(self)

    def _create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # --- Panel Izquierdo: Edición de la Variable ---
        left_pane = ttk.Frame(frame)
        left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Nombre
        ttk.Label(left_pane, text="Nombre de la Variable:").grid(row=0, column=0, sticky="w", pady=2)
        self.nombre_entry = ttk.Entry(left_pane, width=60)
        self.nombre_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Descripción
        ttk.Label(left_pane, text="Descripción:").grid(row=2, column=0, sticky="w", pady=2)
        self.desc_text = tk.Text(left_pane, height=4, wrap="word")
        self.desc_text.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Peso Relativo
        ttk.Label(left_pane, text="Peso Relativo:").grid(row=4, column=0, sticky="w", pady=2)
        self.peso_spinbox = ttk.Spinbox(left_pane, from_=-10.0, to=10.0, increment=0.5, width=10)
        self.peso_spinbox.grid(row=5, column=0, sticky="w", pady=(0, 10))

        # Patrones (Regex)
        ttk.Label(left_pane, text="Patrones de Búsqueda (Regex, uno por línea):").grid(row=6, column=0, sticky="w", pady=2)
        self.patrones_text = tk.Text(left_pane, height=15, wrap="word")
        
        sb_patrones = ttk.Scrollbar(left_pane, orient="vertical", command=self.patrones_text.yview)
        self.patrones_text.config(yscrollcommand=sb_patrones.set)
        self.patrones_text.grid(row=7, column=0, sticky="nsew", pady=(0, 10))
        sb_patrones.grid(row=7, column=1, sticky="ns", pady=(0, 10))

        left_pane.rowconfigure(7, weight=1)
        left_pane.columnconfigure(0, weight=1)

        # --- Panel Derecho: Asistente de Creación de Patrones ---
        right_pane = ttk.LabelFrame(frame, text="Asistente de Patrones", padding="10")
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        ttk.Label(right_pane, text="1. Escribe palabras clave (una por línea):").pack(anchor="w")
        self.keywords_text = tk.Text(right_pane, height=8, wrap="word")
        self.keywords_text.pack(fill=tk.X, expand=True, pady=5)

        ttk.Button(right_pane, text="2. Generar y Probar Patrones", command=self._on_generate_and_test).pack(fill=tk.X, pady=5)

        ttk.Label(right_pane, text="3. Patrones generados y sus coincidencias:").pack(anchor="w", pady=(10, 0))
        self.generated_patterns_text = tk.Text(right_pane, height=8, wrap="word", state="disabled")
        self.generated_patterns_text.pack(fill=tk.X, expand=True, pady=5)

        ttk.Button(right_pane, text="4. Añadir Patrones Generados a la Lista", command=self._on_add_generated).pack(fill=tk.X, pady=5)

        # Botones
        button_frame = ttk.Frame(left_pane)
        button_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=10)
        ttk.Button(button_frame, text="Guardar", command=self._on_save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self._on_cancel).pack(side=tk.LEFT)

    def _populate_data(self):
        self.nombre_entry.insert(0, self.variable.nombre)
        self.desc_text.insert("1.0", self.variable.descripcion)
        self.peso_spinbox.set(self.variable.peso_relativo)
        self.patrones_text.insert("1.0", self.variable.patrones or "")

    def _on_save(self):
        nombre = self.nombre_entry.get().strip()
        if not nombre:
            messagebox.showerror("Error de Validación", "El nombre de la variable no puede estar vacío.", parent=self)
            return

        try:
            peso = float(self.peso_spinbox.get())
        except ValueError:
            messagebox.showerror("Error de Validación", "El peso debe ser un número válido.", parent=self)
            return

        self.result = {
            "id": self.variable.id if self.variable else None,
            "nombre": nombre,
            "descripcion": self.desc_text.get("1.0", tk.END).strip(),
            "peso": peso,
            "patrones": self.patrones_text.get("1.0", tk.END).strip()
        }
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()

    def _on_generate_and_test(self):
        """Genera patrones desde las palabras clave y los prueba en la BD."""
        keywords = self.keywords_text.get("1.0", tk.END)
        if not keywords.strip():
            messagebox.showwarning("Asistente", "Por favor, introduce al menos una palabra clave.", parent=self)
            return

        self.generated_patterns = generar_patrones_desde_palabras_clave(keywords)
        
        success, resultados = probar_patrones_en_db(self.generated_patterns)
        if not success:
            messagebox.showerror("Error de Prueba", "Ocurrió un error al probar los patrones en la base de datos.", parent=self)
            return

        # Mostrar resultados en el cuadro de texto
        self.generated_patterns_text.config(state="normal")
        self.generated_patterns_text.delete("1.0", tk.END)
        for patron, hits in resultados.items():
            self.generated_patterns_text.insert(tk.END, f"Coincidencias: {hits} -> {patron}\n")
        self.generated_patterns_text.config(state="disabled")

    def _on_add_generated(self):
        """Añade los patrones generados al cuadro de texto principal."""
        if not hasattr(self, 'generated_patterns') or not self.generated_patterns:
            messagebox.showwarning("Asistente", "Primero debes generar y probar los patrones.", parent=self)
            return
        
        self.patrones_text.insert(tk.END, "\n" + "\n".join(self.generated_patterns))