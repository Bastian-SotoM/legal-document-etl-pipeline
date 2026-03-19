# -*- coding: utf-8 -*-
"""
Ventana de Detalle de Causa

Muestra toda la información recopilada de una causa judicial específica.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Importar el motor de cálculo para mostrar el análisis en tiempo real
from core.db_manager import calcular_sugerencia_derivacion

class DetailWindow(tk.Toplevel):
    def __init__(self, parent, causa):
        super().__init__(parent)
        self.causa = causa

        self.title(f"Detalles de la Causa - RIT: {self.causa.RIT}")
        self.geometry("900x700")

        self._create_widgets()
        self._populate_data()

        # Hacer la ventana modal (bloquea la interacción con la ventana principal)
        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _create_widgets(self):
        # Usar Notebook (Pestañas) para organizar la información
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Pestaña 1: Resumen y Variables ---
        tab_resumen = ttk.Frame(notebook)
        notebook.add(tab_resumen, text="Resumen y Variables")
        self._create_resumen_tab(tab_resumen)

        # --- Pestaña 2: Análisis de Derivación (NUEVO) ---
        tab_analisis = ttk.Frame(notebook)
        notebook.add(tab_analisis, text="Análisis de Derivación")
        self._create_analisis_tab(tab_analisis)

    def _create_resumen_tab(self, parent_frame):
        """Crea el contenido de la pestaña de resumen (Metadatos + Texto)."""
        # --- Panel Izquierdo: Metadatos ---
        left_panel = ttk.Frame(parent_frame, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False) # Evita que el panel se encoja

        # Frame de Metadatos
        metadata_frame = ttk.LabelFrame(left_panel, text="Metadatos de la Causa")
        metadata_frame.pack(fill=tk.X, pady=(0, 10))
        self.metadata_labels = {}
        metadata_fields = ["RIT", "Tribunal", "Materia", "Fecha Ingreso", "Estado Procesal"]
        for i, field in enumerate(metadata_fields):
            ttk.Label(metadata_frame, text=f"{field}:", font=('Helvetica', 9, 'bold')).grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.metadata_labels[field] = ttk.Label(metadata_frame, text="N/A", wraplength=200)
            self.metadata_labels[field].grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # Frame de Variables de Riesgo
        variables_frame = ttk.LabelFrame(left_panel, text="Variables de Riesgo Encontradas")
        variables_frame.pack(fill=tk.BOTH, expand=True)
        
        self.variables_tree = ttk.Treeview(variables_frame, columns=("variable", "peso"), show="headings")
        self.variables_tree.heading("variable", text="Variable")
        self.variables_tree.heading("peso", text="Peso")
        self.variables_tree.column("peso", width=60, anchor=tk.CENTER)
        
        scrollbar_vars_y = ttk.Scrollbar(variables_frame, orient=tk.VERTICAL, command=self.variables_tree.yview)
        scrollbar_vars_x = ttk.Scrollbar(variables_frame, orient=tk.HORIZONTAL, command=self.variables_tree.xview)
        self.variables_tree.configure(yscroll=scrollbar_vars_y.set, xscroll=scrollbar_vars_x.set)
        scrollbar_vars_y.pack(side=tk.RIGHT, fill=tk.Y, pady=5, padx=(0, 5))
        scrollbar_vars_x.pack(side=tk.BOTTOM, fill=tk.X, padx=5)
        self.variables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0), pady=5)

        # --- Panel Derecho: Texto del Documento ---
        right_panel = ttk.Frame(parent_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        text_frame = ttk.LabelFrame(right_panel, text="Texto Extraído del Documento")
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_widget = tk.Text(text_frame, wrap="word", state="disabled", bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_analisis_tab(self, parent_frame):
        """Crea la pestaña que explica por qué se sugirieron los programas."""
        # Calcular el análisis en tiempo real para esta causa
        analisis = calcular_sugerencia_derivacion(self.causa)
        candidatos = analisis.get("detalles", [])

        if not candidatos:
            ttk.Label(parent_frame, text="No hay sugerencias claras para esta causa.", font=("Helvetica", 12)).pack(pady=20)
            return

        # Contenedor con scroll si hay muchos candidatos
        canvas = tk.Canvas(parent_frame)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Crear una tarjeta para cada candidato sugerido
        for i, cand in enumerate(candidatos):
            titulo = f"Opción {i+1}: {cand['programa']} - Ajuste: {int(cand['ajuste'])}% ({cand['puntaje_obtenido']}/{cand['puntaje_ideal']} pts)"
            frame_cand = ttk.LabelFrame(scrollable_frame, text=titulo, padding="10")
            frame_cand.pack(fill=tk.X, expand=True, padx=10, pady=5)

            # Variables Coincidentes (Verde)
            lbl_ok = ttk.Label(frame_cand, text="✅ Criterios Cumplidos:", font=("Helvetica", 9, "bold"), foreground="green")
            lbl_ok.pack(anchor="w")
            if cand['variables_coincidentes']:
                txt_ok = ", ".join(cand['variables_coincidentes'])
                ttk.Label(frame_cand, text=txt_ok, wraplength=700).pack(anchor="w", padx=10)
            else:
                ttk.Label(frame_cand, text="Ninguno", font=("Helvetica", 9, "italic")).pack(anchor="w", padx=10)

            # Variables Faltantes (Rojo/Gris)
            lbl_miss = ttk.Label(frame_cand, text="❌ Criterios Faltantes (Para mejorar el ajuste):", font=("Helvetica", 9, "bold"), foreground="#d9534f")
            lbl_miss.pack(anchor="w", pady=(5, 0))
            if cand['variables_faltantes']:
                txt_miss = ", ".join(cand['variables_faltantes'])
                ttk.Label(frame_cand, text=txt_miss, wraplength=700).pack(anchor="w", padx=10)
            else:
                ttk.Label(frame_cand, text="Ninguno (Ajuste perfecto)", font=("Helvetica", 9, "italic")).pack(anchor="w", padx=10)

    def _populate_data(self):
        """Llena los widgets con la información de la causa."""
        # Poblar metadatos
        self.metadata_labels["RIT"].config(text=self.causa.RIT or "N/A")
        self.metadata_labels["Tribunal"].config(text=self.causa.tribunal or "N/A")
        self.metadata_labels["Materia"].config(text=self.causa.materia or "N/A")
        fecha_ingreso = self.causa.fecha_ingreso.strftime("%d-%m-%Y") if self.causa.fecha_ingreso else "N/A"
        self.metadata_labels["Fecha Ingreso"].config(text=fecha_ingreso)
        self.metadata_labels["Estado Procesal"].config(text=self.causa.estado_procesal or "N/A")

        # Poblar variables de riesgo
        if self.causa.evaluaciones:
            evaluacion = self.causa.evaluaciones[0]
            for var in sorted(evaluacion.variables, key=lambda v: v.nombre):
                self.variables_tree.insert("", tk.END, values=(var.nombre, var.peso_relativo))

        # Poblar texto del documento
        if self.causa.documentos:
            texto = self.causa.documentos[0].texto_extraido
            self.text_widget.config(state="normal")
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert("1.0", texto or "No se pudo extraer texto del documento.")
            self.text_widget.config(state="disabled")