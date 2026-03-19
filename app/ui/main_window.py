# -*- coding: utf-8 -*-
"""
Ventana Principal de la Aplicación (V2)

Esta es la interfaz principal que se muestra después de un inicio de sesión exitoso.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from datetime import date, timedelta
import warnings

# Integración con Matplotlib para el gráfico de pastel
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.db_manager import (cargar_causas_activas, calcular_sugerencia_derivacion, procesar_y_guardar_causa, finalizar_causa_por_rit, 
                             obtener_ruta_pdf_por_rit, cargar_detalles_causa, cargar_causas_finalizadas, cargar_todas_variables, 
                             guardar_variable, toggle_variable_status, cargar_logs_sistema, resolver_log, reanalizar_todas_las_causas, 
                             generar_patrones_desde_palabras_clave, probar_patrones_en_db, get_dashboard_stats, MAPA_COMUNA_REGION,
                             cargar_registros_auditoria, cargar_programas_sociales, guardar_programa_social, eliminar_todas_las_causas)
from app.ui.detail_window import DetailWindow
from app.ui.variable_editor_window import VariableEditorWindow
from app.ui.program_editor_window import ProgramEditorWindow

class MainWindow(tk.Tk):
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user

        self.title(f"Sistema de Priorización de Riesgo v2.0")
        self.geometry("1200x700")

        self._create_widgets()
        self.on_refresh_list() # Cargar los datos al iniciar la aplicación

        # Configurar tags para colores en el Treeview
        self.tree.tag_configure('impar', background='#ffffff')
        self.tree.tag_configure('par', background='#f0f0f0')

        # Aplicar restricciones de rol
        self._apply_role_restrictions()

        # Vincular evento para actualizar el histórico al cambiar de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def _create_widgets(self):
        # --- Frame Principal ---
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Notebook para Pestañas ---
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- Pestaña 1: Priorización de Causas ---
        self.tab_priorizacion = self._create_priorizacion_tab()
        self.notebook.add(self.tab_priorizacion, text="Priorización de Causas Activas")

        # --- Pestaña 2: Gestión de Variables ---
        self.tab_variables = self._create_variables_tab()
        self.notebook.add(self.tab_variables, text="Gestión de Variables")

        # --- Pestaña 3: Gestión de Programas (NUEVO) ---
        self.tab_programas = self._create_programas_tab()
        self.notebook.add(self.tab_programas, text="Gestión de Programas")

        # --- Pestaña 3: Histórico de Causas ---
        self.tab_historico = self._create_historico_tab()
        self.notebook.add(self.tab_historico, text="Histórico de Causas")

        # --- Pestaña 4: Estado del Sistema ---
        self.tab_estado = self._create_estado_tab()
        self.notebook.add(self.tab_estado, text="Estado del Sistema")

        # --- Barra de Estado ---
        status_bar = ttk.Frame(self, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(status_bar, text=f"Usuario: {self.current_user.nombre} ({self.current_user.rol}) | Listo")
        self.status_label.pack(side=tk.LEFT)

    def _apply_role_restrictions(self):
        """Oculta las pestañas y funcionalidades no disponibles para el rol actual."""
        if self.current_user.rol != 'Administrador':
            print("Aplicando restricciones para el rol 'Analista'.")
            # Ocultar pestañas de administrador
            self.notebook.hide(self.tab_variables)
            self.notebook.hide(self.tab_programas)
            self.notebook.hide(self.tab_estado)

    def _create_priorizacion_tab(self):
        """Crea el contenido de la pestaña de priorización."""
        # Usamos un PanedWindow para dividir la pestaña en dos partes (gráfico y tabla)
        paned_window = ttk.PanedWindow(self.notebook, orient=tk.VERTICAL)

        # --- Frame Superior: Gráfico de Prioridades ---
        chart_frame = ttk.LabelFrame(paned_window, text="Derivaciones Sugeridas (Top)", padding="5")
        paned_window.add(chart_frame, weight=2) # El gráfico ocupa menos espacio

        # Crear la figura y el canvas de Matplotlib para el gráfico de pastel
        self.priority_fig = Figure(figsize=(6, 5), dpi=100)
        self.priority_ax = self.priority_fig.add_subplot(111)
        self.priority_canvas = FigureCanvasTkAgg(self.priority_fig, master=chart_frame)
        self.priority_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.priority_fig.tight_layout()

        # --- Frame Inferior: Lista de Causas ---
        list_frame = ttk.Frame(paned_window, padding="10")
        paned_window.add(list_frame, weight=3) # La lista ocupa más espacio

        # --- Frame de Botones ---
        button_frame = ttk.Frame(list_frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Cargar Nueva Causa (PDF)", command=self.on_load_case).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Marcar Causa como Finalizada", command=self.on_finalize_case).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abrir Causa Seleccionada (PDF)", command=self.on_open_case).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Actualizar Lista", command=self.on_refresh_list).pack(side=tk.RIGHT, padx=5)

        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("rit", "ubicacion", "sugerencia", "ajuste", "fecha_carga")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Definir encabezados
        self.tree.heading("rit", text="RIT")
        self.tree.heading("ubicacion", text="Ubicación (Comuna/Región)")
        self.tree.heading("sugerencia", text="Sugerencia de Derivación")
        self.tree.heading("ajuste", text="Ajuste")
        self.tree.heading("fecha_carga", text="Fecha de Carga")

        # Ajustar columnas
        self.tree.column("rit", width=150)
        self.tree.column("ubicacion", width=200)
        self.tree.column("sugerencia", width=500) # Aumentado para soportar múltiples programas
        self.tree.column("ajuste", width=100, anchor=tk.CENTER) # Aumentado para "95% / 80%"

        # Scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Eventos ---
        self.tree.bind("<Double-1>", self.on_double_click_causa)

        return paned_window

    def _create_variables_tab(self):
        """Crea el contenido de la pestaña de gestión de variables."""
        frame = ttk.Frame(self.notebook, padding="10")

        # --- Frame de Botones ---
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Crear Nueva Variable", command=self.on_create_variable).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Editar Variable Seleccionada", command=self.on_edit_variable).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Activar/Desactivar", command=self.on_toggle_variable_status).pack(side=tk.LEFT, padx=5)

        # --- Tabla de Variables (Treeview) ---
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("nombre", "peso", "tipo", "estado", "descripcion")
        self.variables_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        self.variables_tree.heading("nombre", text="Nombre")
        self.variables_tree.heading("peso", text="Peso")
        self.variables_tree.heading("tipo", text="Tipo")
        self.variables_tree.heading("estado", text="Estado")
        self.variables_tree.heading("descripcion", text="Descripción")

        self.variables_tree.column("peso", width=60, anchor=tk.CENTER)
        self.variables_tree.column("tipo", width=100, anchor=tk.CENTER)
        self.variables_tree.column("estado", width=80, anchor=tk.CENTER)

        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.variables_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.variables_tree.xview)
        self.variables_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.variables_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.variables_tree.bind("<Double-1>", lambda e: self.on_edit_variable())

        return frame

    def _create_programas_tab(self):
        """Crea el contenido de la pestaña de gestión de programas sociales."""
        frame = ttk.Frame(self.notebook, padding="10")

        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Crear Nuevo Programa", command=self.on_create_program).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Editar Programa", command=self.on_edit_program).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Actualizar Lista", command=self.refresh_programs_list).pack(side=tk.RIGHT, padx=5)

        # Tabla
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("nombre", "descripcion")
        self.programs_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")
        self.programs_tree.heading("nombre", text="Nombre del Programa")
        self.programs_tree.heading("descripcion", text="Descripción")
        self.programs_tree.column("nombre", width=200)
        
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.programs_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.programs_tree.xview)
        self.programs_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.programs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return frame

    def _create_historico_tab(self):
        """Crea el contenido de la pestaña de histórico."""
        frame = ttk.Frame(self.notebook, padding="10")

        # --- Frame de Búsqueda ---
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Buscar por RIT o Nombre:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind("<Return>", self.on_search_historico) # Buscar al presionar Enter

        ttk.Button(search_frame, text="Buscar", command=self.on_search_historico).pack(side=tk.LEFT, padx=5)

        # --- Tabla de Causas Históricas (Treeview) ---
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        columns = ("rit", "adulto_mayor", "tribunal", "fecha_ingreso", "fecha_finalizacion")
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        # Definir encabezados
        self.history_tree.heading("rit", text="RIT")
        self.history_tree.heading("adulto_mayor", text="Adulto Mayor")
        self.history_tree.heading("tribunal", text="Tribunal")
        self.history_tree.heading("fecha_ingreso", text="Fecha Ingreso")
        self.history_tree.heading("fecha_finalizacion", text="Fecha Finalización")

        # Ajustar columnas
        self.history_tree.column("rit", width=150)
        self.history_tree.column("adulto_mayor", width=250)

        # Scrollbar
        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.history_tree.xview)
        self.history_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.history_tree.bind("<Double-1>", self.on_double_click_causa) # Reutilizamos la misma función

        return frame

    def _create_estado_tab(self):
        """Crea el contenido de la pestaña de estado del sistema."""
        frame = ttk.Frame(self.notebook, padding="10")

        # --- Frame de Botones ---
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(button_frame, text="Marcar como Resuelto", command=self.on_resolve_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Actualizar Logs", command=self.refresh_logs_list).pack(side=tk.RIGHT, padx=5)
        
        # Botón de limpieza total (Solo Admin)
        if self.current_user.rol == 'Administrador':
            ttk.Button(button_frame, text="⚠️ Borrar Todas las Causas", command=self.on_reset_system).pack(side=tk.RIGHT, padx=20)

        # --- Tabla de Logs (Treeview) ---
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        log_columns = ("id", "fecha", "tipo", "descripcion")
        self.logs_tree = ttk.Treeview(tree_frame, columns=log_columns, show="headings")

        self.logs_tree.heading("id", text="ID"); self.logs_tree.column("id", width=50, anchor=tk.CENTER)
        self.logs_tree.heading("fecha", text="Fecha"); self.logs_tree.column("fecha", width=150)
        self.logs_tree.heading("tipo", text="Tipo"); self.logs_tree.column("tipo", width=80)
        self.logs_tree.heading("descripcion", text="Descripción")

        scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.logs_tree.yview)
        scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.logs_tree.xview)
        self.logs_tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.logs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        return frame

    # --- Funciones de los botones (placeholders) ---
    def on_load_case(self):
        """Abre un diálogo para seleccionar un PDF y lo procesa en un hilo."""
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo PDF de la causa",
            filetypes=[("Archivos PDF", "*.pdf")]
        )
        if not filepath:
            return # El usuario canceló

        self.status_label.config(text=f"Procesando '{os.path.basename(filepath)}'...")
        # Iniciar el procesamiento en un hilo para no congelar la UI
        thread = threading.Thread(target=self._thread_load_case, args=(filepath,))
        thread.start()

    def _thread_load_case(self, filepath):
        """Función ejecutada en un hilo para procesar el PDF."""
        success, message = procesar_y_guardar_causa(filepath, self.current_user.id)
        
        # La actualización de la UI debe hacerse de forma segura desde el hilo principal
        self.after(0, self._update_ui_after_load, success, message)

    def _update_ui_after_load(self, success, message):
        """Actualiza la UI después de que el hilo de carga termina."""
        messagebox.showinfo("Resultado del Análisis", message) if success else messagebox.showerror("Error de Análisis", message)
        self.on_refresh_list() # Actualiza la tabla con la nueva causa si se guardó

    def on_finalize_case(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona al menos una causa de la lista para finalizar.")
            return

        rits_a_finalizar = [self.tree.item(item)['values'][0] for item in selected_items]
        
        confirmacion = messagebox.askyesno(
            "Confirmar Finalización",
            f"¿Estás seguro de que deseas marcar {len(rits_a_finalizar)} causa(s) como 'Finalizada(s)'?\n"
            "Esta acción las quitará de la lista de causas activas."
        )

        if not confirmacion:
            return

        exitos = 0
        errores = 0
        for rit in rits_a_finalizar:
            success, _ = finalizar_causa_por_rit(rit, self.current_user.id)
            if success:
                exitos += 1
            else:
                errores += 1
        
        messagebox.showinfo("Proceso Completado", f"Se finalizaron {exitos} causa(s) exitosamente.\nHubo {errores} error(es).")
        self.on_refresh_list()

    def on_open_case(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona una causa de la lista para abrir.")
            return
        
        if len(selected_items) > 1:
            messagebox.showwarning("Selección Múltiple", "Por favor, selecciona solo una causa para abrir el archivo PDF.")
            return

        selected_item = selected_items[0]
        rit_causa = self.tree.item(selected_item)['values'][0]

        ruta_pdf = obtener_ruta_pdf_por_rit(rit_causa)

        if ruta_pdf and os.path.exists(ruta_pdf):
            try:
                os.startfile(ruta_pdf) # Comando específico de Windows para abrir un archivo con su app predeterminada
                self.status_label.config(text=f"Abriendo archivo para la causa {rit_causa}...")
            except Exception as e:
                messagebox.showerror("Error al Abrir", f"No se pudo abrir el archivo PDF:\n{e}")
        else:
            messagebox.showerror("Archivo no Encontrado", f"No se encontró el archivo PDF para la causa RIT {rit_causa}.")

    def on_double_click_causa(self, event):
        """Maneja el evento de doble clic en una fila de la tabla."""
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            # Si no se hizo clic en la tabla principal, probar con la de histórico
            item_id = self.history_tree.identify_row(event.y)
            if not item_id:
                return
            tree_widget = self.history_tree
        else:
            tree_widget = self.tree

        rit_causa = tree_widget.item(item_id)['values'][0]
        self.status_label.config(text=f"Cargando detalles para la causa {rit_causa}...")
        
        causa_detallada = cargar_detalles_causa(rit_causa)
        if causa_detallada:
            DetailWindow(self, causa_detallada)
        else:
            messagebox.showerror("Error", f"No se pudieron cargar los detalles para la causa RIT {rit_causa}.")
        self.status_label.config(text=f"Usuario: {self.current_user.nombre} ({self.current_user.rol}) | Listo")

    def on_search_historico(self, event=None):
        """Realiza la búsqueda en el histórico y puebla la tabla."""
        search_term = self.search_entry.get()
        self.status_label.config(text=f"Buscando '{search_term}' en el histórico...")

        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        causas_finalizadas = cargar_causas_finalizadas(search_term)
        for causa in causas_finalizadas:
            self.history_tree.insert("", tk.END, values=(
                causa.RIT, causa.adulto_mayor.nombre if causa.adulto_mayor else "N/A", causa.tribunal,
                causa.fecha_ingreso.strftime("%Y-%m-%d") if causa.fecha_ingreso else "N/A",
                causa.fecha_finalizacion.strftime("%Y-%m-%d %H:%M") if causa.fecha_finalizacion else "N/A"
            ))
        self.status_label.config(text=f"Búsqueda completada. Se encontraron {len(causas_finalizadas)} resultados.")

    def on_refresh_list(self):
        """Inicia la actualización de la lista de causas activas en un hilo secundario."""
        self.status_label.config(text="Actualizando lista de causas activas...")
        self._update_priority_chart() # El gráfico se puede actualizar rápido
        thread = threading.Thread(target=self._thread_refresh_list)
        thread.start()

    def _thread_refresh_list(self):
        """(Hilo secundario) Carga las causas y calcula sus prioridades."""
        causas = cargar_causas_activas() # Esta es la operación lenta
        
        # Crear una lista de causas con su información de prioridad pre-calculada
        causas_con_prioridad = []
        for causa in causas:
            info_sugerencia = calcular_sugerencia_derivacion(causa)
            causas_con_prioridad.append((causa, info_sugerencia))

        # Mapear prioridad a un valor numérico para ordenar (0=Alta, 1=Media, 2=Baja)
        urgencia_map = {"Alta": 0, "Media": 1, "Baja": 2}

        # Ordenar la lista: primero por prioridad (Alta primero) y luego por fecha de carga (más antiguas primero)
        causas_con_prioridad.sort(key=lambda item: (urgencia_map.get(item[1]['urgencia'], 99), item[0].fecha_carga))

        self.after(0, self._update_main_tree, causas_con_prioridad)

    def _update_main_tree(self, causas_con_prioridad):
        """(Hilo principal) Limpia y puebla la tabla de causas activas."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, (causa, info_sugerencia) in enumerate(causas_con_prioridad):
            ajuste_str = info_sugerencia.get("ajuste_str", f"{info_sugerencia['ajuste']}%")

            tag = 'par' if i % 2 == 0 else 'impar'

            comuna = causa.comuna or "Desconocida"
            
            # Buscar región insensible a mayúsculas/minúsculas
            region = ""
            for c_key, r_val in MAPA_COMUNA_REGION.items():
                if c_key.lower() == comuna.lower():
                    region = r_val
                    break
            
            ubicacion_str = f"{comuna}, Región {region}" if region else comuna

            # Insertar al principio de la tabla (at=0) para que el orden visual sea descendente por fecha
            self.tree.insert("", 0, values=(
                causa.RIT, ubicacion_str, info_sugerencia["sugerencia"], ajuste_str, causa.fecha_carga.strftime("%Y-%m-%d %H:%M")
            ), tags=(tag,))
        
        self.status_label.config(text=f"Usuario: {self.current_user.nombre} ({self.current_user.rol}) | Lista de causas actualizada.")

    def on_tab_changed(self, event):
        """Se ejecuta cuando el usuario cambia de pestaña."""
        selected_tab_id = self.notebook.select()
        
        if selected_tab_id == str(self.tab_historico):
            # Limpiar el campo de búsqueda y ejecutar la búsqueda para mostrar todos los resultados
            if self.search_entry.get():
                self.search_entry.delete(0, tk.END)
            self.on_search_historico() # Inicia la carga en segundo plano
        elif selected_tab_id == str(self.tab_variables):
            self.refresh_variables_list()
        elif selected_tab_id == str(self.tab_programas):
            self.refresh_programs_list()
        elif selected_tab_id == str(self.tab_estado):
            self._load_logs_into_tree()

    def refresh_variables_list(self):
        """Inicia la carga de la lista de variables en un hilo."""
        self.status_label.config(text="Cargando variables de riesgo...")
        thread = threading.Thread(target=self._thread_refresh_variables)
        thread.start()

    def _thread_refresh_variables(self):
        """(Hilo secundario) Carga las variables desde la BD."""
        variables = cargar_todas_variables()
        self.after(0, self._update_variables_tree, variables)

    def _update_variables_tree(self, variables):
        """(Hilo principal) Limpia y puebla la tabla de variables."""
        for item in self.variables_tree.get_children():
            self.variables_tree.delete(item)
        for var in variables:
            self.variables_tree.insert("", tk.END, iid=var.id, values=(
                var.nombre, var.peso_relativo, var.tipo, var.estado, var.descripcion
            ))
        self.status_label.config(text="Variables cargadas.")

    def on_create_variable(self):
        """Abre la ventana para crear una nueva variable."""
        editor = VariableEditorWindow(self)
        if editor.result:
            success, message = guardar_variable(editor.result, self.current_user.id)
            if success:
                messagebox.showinfo("Éxito", message)
                self.refresh_variables_list()
                self._ask_for_reanalysis()
            else:
                messagebox.showerror("Error", message)

    def on_edit_variable(self):
        """Abre la ventana para editar la variable seleccionada."""
        selected_items = self.variables_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona una variable de la lista para editar.", parent=self)
            return
        
        variable_id = selected_items[0]
        # Necesitamos cargar la variable completa desde la BD para tener todos los datos
        variables = cargar_todas_variables()
        variable_a_editar = next((v for v in variables if v.id == int(variable_id)), None)

        if variable_a_editar:
            editor = VariableEditorWindow(self, variable_a_editar)
            if editor.result:
                success, message = guardar_variable(editor.result, self.current_user.id)
                if success:
                    messagebox.showinfo("Éxito", message)
                    self.refresh_variables_list()
                    self._ask_for_reanalysis()
                else:
                    messagebox.showerror("Error", message)

    # --- Gestión de Programas ---
    def refresh_programs_list(self):
        """Recarga la lista de programas."""
        for item in self.programs_tree.get_children():
            self.programs_tree.delete(item)
        
        programas = cargar_programas_sociales()
        for prog in programas:
            self.programs_tree.insert("", tk.END, iid=prog.id, values=(prog.nombre, prog.descripcion))

    def on_create_program(self):
        """Abre editor para nuevo programa."""
        editor = ProgramEditorWindow(self)
        if editor.result:
            success, msg = guardar_programa_social(editor.result, self.current_user.id)
            if success:
                messagebox.showinfo("Éxito", msg)
                self.refresh_programs_list()
                self._ask_for_reanalysis()
            else:
                messagebox.showerror("Error", msg)

    def on_edit_program(self):
        """Abre editor para programa existente."""
        selected = self.programs_tree.selection()
        if not selected: return
        
        prog_id = int(selected[0])
        programas = cargar_programas_sociales()
        prog = next((p for p in programas if p.id == prog_id), None)
        
        if prog:
            editor = ProgramEditorWindow(self, prog)
            if editor.result:
                success, msg = guardar_programa_social(editor.result, self.current_user.id)
                messagebox.showinfo("Resultado", msg)
                self.refresh_programs_list()
                if success: self._ask_for_reanalysis()

    def refresh_logs_list(self):
        """Limpia y recarga la lista de logs del sistema."""
        self._load_logs_into_tree()

    def _load_logs_into_tree(self): # Esta función también debería usar un hilo
        """Inicia la carga de logs del sistema en un hilo."""
        self.status_label.config(text="Cargando logs del sistema...")
        thread = threading.Thread(target=self._thread_load_logs)
        thread.start()

    def _thread_load_logs(self):
        """(Hilo secundario) Carga los logs desde la BD."""
        logs = cargar_logs_sistema(solo_abiertos=True)
        self.after(0, self._update_logs_tree, logs)

    def _update_logs_tree(self, logs):
        """(Hilo principal) Limpia y puebla la tabla de logs."""
        for item in self.logs_tree.get_children():
            self.logs_tree.delete(item)
        for log in logs:
            self.logs_tree.insert("", tk.END, iid=log.id, values=(
                log.id, log.fecha_evento.strftime("%Y-%m-%d %H:%M"), log.tipo_evento, log.descripcion
            ))
        self.status_label.config(text="Logs del sistema cargados.")

    def on_resolve_log(self):
        """Marca el log seleccionado como resuelto."""
        selected_items = self.logs_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona un log de la lista para resolver.", parent=self)
            return

        log_id = selected_items[0]
        
        confirmacion = messagebox.askyesno(
            "Confirmar Resolución",
            f"¿Estás seguro de que deseas marcar el Log ID {log_id} como resuelto?"
        )
        if not confirmacion:
            return

        success, message = resolver_log(int(log_id), self.current_user.id)
        if success:
            messagebox.showinfo("Éxito", message)
        else:
            messagebox.showerror("Error", message)
        
        self.refresh_logs_list()

    def on_reset_system(self):
        """Maneja la solicitud de limpieza total del sistema."""
        confirmacion = messagebox.askyesno(
            "⚠️ ADVERTENCIA CRÍTICA ⚠️",
            "Estás a punto de ELIMINAR TODAS LAS CAUSAS, documentos y evaluaciones del sistema.\n\n"
            "Esta acción NO SE PUEDE DESHACER.\n"
            "Los archivos PDF también serán borrados del disco.\n\n"
            "¿Estás absolutamente seguro de que quieres continuar?",
            icon='warning',
            parent=self
        )
        if confirmacion:
            confirmacion2 = messagebox.askyesno(
                "Confirmación Final",
                "¿De verdad quieres borrar todo? El sistema quedará vacío de causas.",
                icon='warning',
                parent=self
            )
            if confirmacion2:
                success, msg = eliminar_todas_las_causas(self.current_user.id)
                if success:
                    messagebox.showinfo("Sistema Limpiado", msg)
                    self.on_refresh_list() # Limpiar tabla visualmente
                else:
                    messagebox.showerror("Error", msg)

    def _update_priority_chart(self):
        """Obtiene datos y actualiza el gráfico de pastel con la distribución de programas."""
        success, data = get_dashboard_stats()
        if not success:
            print(f"Error al actualizar el gráfico de prioridades: {data}")
            return

        labels = []
        sizes = []
        colors = []
        
        # Paleta de colores pastel para los programas
        palette = ['#a2d2ff', '#bde0fe', '#ffafcc', '#ffc8dd', '#cdb4db', '#d9ead3', '#fff2cc', '#f4cccc']

        for i, (label, size) in enumerate(data.items()):
            if size > 0: # Solo mostrar secciones con datos
                # Truncar etiquetas muy largas para evitar problemas de layout
                display_label = label if len(label) < 25 else label[:22] + "..."
                labels.append(f"{display_label}\n({size})")
                sizes.append(size)
                colors.append(palette[i % len(palette)])

        self.priority_ax.clear()
        if sizes:
            self.priority_ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'white'})
        self.priority_ax.axis('equal')  # Asegura que el gráfico sea un círculo.
        
        # Capturar advertencias de layout para evitar spam en consola si el gráfico es muy pequeño
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.priority_fig.tight_layout()
            
        self.priority_canvas.draw()

    def on_toggle_variable_status(self):
        """Cambia el estado de la(s) variable(s) seleccionada(s)."""
        selected_items = self.variables_tree.selection()
        if not selected_items:
            messagebox.showwarning("Sin Selección", "Por favor, selecciona al menos una variable de la lista.", parent=self)
            return

        confirmacion = messagebox.askyesno(
            "Confirmar Cambio de Estado",
            f"¿Estás seguro de que deseas cambiar el estado de {len(selected_items)} variable(s)?"
        )
        if not confirmacion:
            return

        for item_id in selected_items:
            # El IID de la fila es el ID de la variable en la BD
            variable_id = int(item_id)
            success, message = toggle_variable_status(variable_id, self.current_user.id)
            if not success:
                messagebox.showerror("Error", message, parent=self)
        
        self.refresh_variables_list()

    def _ask_for_reanalysis(self):
        """Pregunta al usuario si desea re-analizar todas las causas."""
        # Solo los administradores pueden re-analizar
        if self.current_user.rol != 'Administrador':
            self.on_refresh_list() # Un analista solo refresca la lista
            return

        respuesta = messagebox.askyesno(
            "Re-analizar Causas",
            "La configuración de variables ha cambiado.\n\n"
            "¿Deseas re-analizar todas las causas existentes para aplicar estos cambios?\n\n"
            "(Este proceso puede tardar varios minutos y se ejecutará en segundo plano)"
        )
        if respuesta:
            self.status_label.config(text="Iniciando re-análisis de todas las causas en segundo plano...")
            thread = threading.Thread(target=self._thread_reanalyze_cases)
            thread.start()

    def _thread_reanalyze_cases(self):
        """Función ejecutada en un hilo para re-analizar todas las causas."""
        success, message = reanalizar_todas_las_causas()
        self.after(0, self._update_ui_after_reanalysis, success, message)

    def _update_ui_after_reanalysis(self, success, message):
        """Actualiza la UI después de que el hilo de re-análisis termina."""
        if success:
            messagebox.showinfo("Proceso Completado", message)
        else:
            messagebox.showerror("Error en Re-análisis", message)
        self.on_refresh_list() # Actualiza la tabla principal con las nuevas prioridades
        self.status_label.config(text=f"Usuario: {self.current_user.nombre} ({self.current_user.rol}) | Listo")