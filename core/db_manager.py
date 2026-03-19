# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Base de Datos para la UI

Centraliza todas las consultas y operaciones con la base de datos
que la interfaz gráfica necesita.
"""

import os
import threading
import re
import shutil
import sys
import json
from sqlalchemy import create_engine, func, cast, Date, text
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract

# Añadir el directorio raíz del proyecto al path para encontrar otros módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import CausaJudicial, EvaluacionRiesgo, AdultoMayor, DocumentoPDF, VariableRiesgo, AuditoriaAccion, LogSistema, Usuario, ProgramaSocial, Base
from core.config import UMBRALES_RIESGO, NOMBRES_VARIABLES, PATRONES_VARIABLES, PATRONES_METADATOS, PATRONES_ROLES, MAPA_COMUNA_REGION, LISTA_COMUNAS
from core.program_profiles import PERFILES_PROGRAMAS

# --- Conexión a la Base de Datos ---
BD_PATH = "data/riesgo_patrimonial.db"
# Aumentar el timeout para evitar errores de "database is locked" durante operaciones largas en hilos.
# 30 segundos es un valor generoso que debería ser suficiente para la mayoría de los casos.
engine = create_engine(f"sqlite:///{BD_PATH}", connect_args={'timeout': 30})
Session = sessionmaker(bind=engine)
# Asegurar que las tablas existan (incluyendo la nueva ProgramaSocial)
Base.metadata.create_all(engine)

def actualizar_esquema_db():
    """
    Verifica y actualiza el esquema de la base de datos si faltan columnas nuevas.
    Esto es una migración manual simple para evitar perder datos.
    """
    with engine.connect() as conn:
        # 1. Verificar tabla causa_judicial
        try:
            conn.execute(text("SELECT comuna FROM causa_judicial LIMIT 1"))
        except Exception:
            print("⚠️ Actualizando esquema: Añadiendo columna 'comuna' a 'causa_judicial'...")
            conn.execute(text("ALTER TABLE causa_judicial ADD COLUMN comuna VARCHAR(100)"))
            conn.commit()

        # 2. Verificar tabla programa_social
        try:
            conn.execute(text("SELECT territorio FROM programa_social LIMIT 1"))
        except Exception:
            print("⚠️ Actualizando esquema: Añadiendo columna 'territorio' a 'programa_social'...")
            conn.execute(text("ALTER TABLE programa_social ADD COLUMN territorio TEXT"))
            conn.commit()

# Ejecutar actualización de esquema al iniciar
actualizar_esquema_db()

# Lock global para prevenir errores de "database is locked" en operaciones de escritura con hilos.
db_lock = threading.RLock() # Usar un RLock para permitir bloqueos anidados desde el mismo hilo.

# Cache simple para programas sociales para no consultar la BD en cada cálculo
_PROGRAMAS_CACHE = None

def inicializar_programas_db():
    """Puebla la tabla ProgramaSocial con los perfiles por defecto si está vacía."""
    session = Session()
    
    # Descripciones enriquecidas basadas en la tesis
    descripciones = {
        "Derivar a ELEAM": "(SENAMA) Residencias protegidas para adultos mayores con dependencia severa y sin red de apoyo.",
        "Derivar a CEDIAM": "(SENAMA) Espacios de atención diurna para estimulación física y cognitiva. Retrasa la institucionalización.",
        "Derivar a SNAC": "(Min. Desarrollo Social) Servicios especializados (kinesiólogo, TENS) en el domicilio para dependencia y apoyo a cuidadores.",
        "Derivar a Plan de Cuidados (SNAC)": "(Min. Desarrollo Social) Servicios especializados (kinesiólogo, TENS) en el domicilio para dependencia y apoyo a cuidadores.",
        "Programa de Atención Domiciliaria para Personas con Dependencia Severa y Cuidadores": "(MINSAL) Visitas domiciliarias integrales de salud (APS) para personas postradas.",
        "Postular a Viviendas Tuteladas (CVT)": "(SENAMA / Minvu) Conjuntos habitacionales con apoyo psicosocial para autovalentes con vulnerabilidad.",
        "Postular a Subsidio de Arriendo": "(Minvu) Aporte estatal para cubrir el arriendo y evitar el empobrecimiento por gastos de vivienda.",
        "Sugerir Programa Vínculos": "(Min. Desarrollo Social) Acompañamiento psicosocial para revincular con la red comunal y combatir la soledad.",
        "Sugerir Vacaciones Tercera Edad": "(SERNATUR) Paquetes turísticos subsidiados para promover el envejecimiento activo.",
        "Sugerir Voluntariado Asesores": "(SENAMA) Iniciativa para que mayores profesionales transmitan experiencia y se mantengan activos.",
        "Activar Defensoría Mayor": "(SENAMA) Representación jurídica gratuita especializada en abusos patrimoniales, VIF o interdicciones.",
        "Programa Buen Trato al Mayor": "(SENAMA) Prevención y asesoría en casos de maltrato complejo y conflictos familiares.",
        "Derivar a Oficina Municipal (OMAM)": "(Municipalidades) Puerta de entrada a la red local y ayudas discrecionales (DIDECO).",
        "Derivar a Salud Mental (COSAM)": "(MINSAL) Atención especializada para trastornos psiquiátricos graves o demencias complejas.",
        "Programa de pago a cuidadores de personas con discapacidad (estipendio)": "(Min. Desarrollo Social / IPS) Aporte monetario al cuidador principal de persona con dependencia severa."
    }

    try:
        print("⚙️ Sincronizando base de datos de programas sociales...")

        # Manejar renombre de programa para compatibilidad con bases de datos antiguas
        old_prog = session.query(ProgramaSocial).filter_by(nombre="Derivar a SNAC (Red Local)").first()
        if old_prog:
            old_prog.nombre = "Derivar a Plan de Cuidados (SNAC)"

        old_prog_minsal = session.query(ProgramaSocial).filter_by(nombre="Derivar a Atención Domiciliaria (MINSAL)").first()
        if old_prog_minsal:
            old_prog_minsal.nombre = "Programa de Atención Domiciliaria para Personas con Dependencia Severa y Cuidadores"

        old_prog_estipendio = session.query(ProgramaSocial).filter_by(nombre="Gestionar Estipendio Cuidador").first()
        if old_prog_estipendio:
            old_prog_estipendio.nombre = "Programa de pago a cuidadores de personas con discapacidad (estipendio)"

        for nombre, perfil in PERFILES_PROGRAMAS.items():
            prog = session.query(ProgramaSocial).filter_by(nombre=nombre).first()
            if not prog:
                prog = ProgramaSocial(nombre=nombre)
                session.add(prog)
            
            prog.variables_clave = json.dumps(perfil["variables_clave"])
            prog.variables_contexto = json.dumps(perfil["variables_contexto"])
            prog.territorio = perfil.get("territorio", "Nacional") # Leer territorio desde el perfil
            prog.descripcion = descripciones.get(nombre, "Programa base del sistema.")
        
        session.commit()
        print("✅ Programas sociales actualizados.")
    except Exception as e:
        print(f"❌ Error al inicializar programas: {e}")
    finally:
        session.close()

# Ejecutar inicialización al importar el módulo
inicializar_programas_db()

def calcular_sugerencia_derivacion(causa):
    """
    Motor de Coincidencia (Matching Engine).
    Calcula el ajuste de una causa contra perfiles de programas sociales y sugiere la mejor derivación.
    """
    variables_encontradas_nombres = []
    if causa.evaluaciones:
        variables_encontradas_nombres = [v.nombre for v in causa.evaluaciones[0].variables]

    if not variables_encontradas_nombres:
        return {"sugerencia": "Sin Sugerencia", "ajuste": 0, "urgencia": "Baja", "variables_faltantes": []}

    candidatos = []

    # Cargar programas (usando cache si está disponible)
    programas = cargar_programas_sociales()

    for prog in programas:
        vars_clave = json.loads(prog.variables_clave) if isinstance(prog.variables_clave, str) else prog.variables_clave
        vars_contexto = json.loads(prog.variables_contexto) if isinstance(prog.variables_contexto, str) else prog.variables_contexto

        # --- FILTRO DE TERRITORIALIDAD ---
        territorio_prog = prog.territorio
        if territorio_prog and territorio_prog != "Nacional":
            comuna_causa = causa.comuna.strip() if causa.comuna else ""
            if not comuna_causa:
                continue # Si la causa no tiene comuna, no puede calzar con un programa territorial
            
            # Normalizar para comparación
            comuna_causa_norm = comuna_causa.lower()
            
            # Obtener región de la causa usando el mapa
            region_causa = ""
            for c, r in MAPA_COMUNA_REGION.items():
                if c.lower() == comuna_causa_norm:
                    region_causa = r
                    break
            region_causa_norm = region_causa.lower()

            territorios_programa = [t.strip().lower() for t in territorio_prog.split(',')]
            
            match_territorio = False
            # 1. Coincidencia directa de Comuna (ej. "Rengo" en lista del programa)
            if comuna_causa_norm in territorios_programa:
                match_territorio = True
            # 2. Coincidencia por Región (ej. "Metropolitana" en lista del programa)
            elif region_causa_norm and region_causa_norm in territorios_programa:
                match_territorio = True
            # 3. Comodines (Legacy)
            elif "regional" in territorios_programa or "comunal" in territorios_programa:
                 match_territorio = True

            if not match_territorio:
                continue # El programa no está disponible ni en la comuna ni en la región

        puntaje_obtenido = 0
        # Calcular puntaje ideal
        puntaje_ideal = len(vars_clave) * 2 + len(vars_contexto) * 1
        
        variables_faltantes = []
        variables_coincidentes = []

        # Calcular puntaje obtenido
        for var_nombre in vars_clave:
            if var_nombre in variables_encontradas_nombres:
                puntaje_obtenido += 2
                variables_coincidentes.append(f"{var_nombre} (Clave: +2 pts)")
            else:
                variables_faltantes.append(f"{var_nombre} (Clave: +2 pts)") # Variable clave faltante
        
        for var_nombre in vars_contexto:
            if var_nombre in variables_encontradas_nombres:
                puntaje_obtenido += 1
                variables_coincidentes.append(f"{var_nombre} (Contexto: +1 pto)")
            else:
                variables_faltantes.append(f"{var_nombre} (Contexto: +1 pto)")

        if puntaje_ideal > 0:
            ajuste = (puntaje_obtenido / puntaje_ideal) * 100
            # Umbral de corte: solo sugerir si hay al menos un 30% de coincidencia para evitar ruido
            if ajuste >= 30:
                candidatos.append({
                    "programa": prog.nombre,
                    "ajuste": ajuste,
                    "puntaje_obtenido": puntaje_obtenido,
                    "puntaje_ideal": puntaje_ideal,
                    "variables_faltantes": variables_faltantes,
                    "variables_coincidentes": variables_coincidentes
                })

    # Ordenar candidatos por ajuste descendente (mayor coincidencia primero)
    candidatos.sort(key=lambda x: x["ajuste"], reverse=True)

    # Determinar Urgencia basada en el puntaje total de pesos
    puntaje_total_pesos = sum(v.peso_relativo for v in causa.evaluaciones[0].variables)
    urgencia = "Baja"
    if puntaje_total_pesos >= UMBRALES_RIESGO[2]:
        urgencia = "Alta"
    elif puntaje_total_pesos >= UMBRALES_RIESGO[1]:
        urgencia = "Media"

    if not candidatos:
        return {
            "sugerencia": "Revisión General",
            "ajuste": 0,
            "ajuste_str": "0%",
            "urgencia": urgencia,
            "num_variables": len(variables_encontradas_nombres),
            "detalles": []
        }

    # Formatear salida: Mostrar los 2 mejores programas si hay competencia
    # Se unen con " / " para que sea legible en la tabla
    top_candidatos = candidatos[:2]
    sugerencia_str = " / ".join([c["programa"] for c in top_candidatos])
    # Generar string de ajustes correspondientes: "95% / 80%"
    ajuste_str = " / ".join([f"{int(c['ajuste'])}%" for c in top_candidatos])
    mejor_ajuste = int(candidatos[0]["ajuste"])

    return {
        "sugerencia": sugerencia_str,
        "ajuste": mejor_ajuste,
        "ajuste_str": ajuste_str,
        "urgencia": urgencia,
        "num_variables": len(variables_encontradas_nombres),
        "detalles": candidatos # Devolvemos TODOS los candidatos para la ventana de detalles
    }

def cargar_causas_activas():
    """Carga todas las causas con estado 'En Proceso' desde la BD."""
    session = Session()
    resultados = []
    try:
        causas_activas = (
            session.query(CausaJudicial)
            .filter(CausaJudicial.estado_causa == 'En Proceso')
            .options(joinedload(CausaJudicial.evaluaciones).joinedload(EvaluacionRiesgo.variables))
            .order_by(CausaJudicial.fecha_carga.desc())
            .all()
        )
        return causas_activas
    finally:
        session.close()

# === LÓGICA DE PROCESAMIENTO Y ESCRITURA (Refactorizada de 2_poblar_bd.py) ===

def extraer_texto_pdf_con_ocr(ruta_pdf):
    texto_extraido = ""
    try:
        with fitz.open(ruta_pdf) as doc:
            texto_extraido = "".join(pagina.get_text("text") for pagina in doc)
    except Exception as e:
        print(f"Error con PyMuPDF en {os.path.basename(ruta_pdf)}: {e}")

    if len(texto_extraido.strip()) < 200:
        print(f"ℹ️  Texto corto detectado. Intentando con OCR...")
        try:
            paginas_img = convert_from_path(ruta_pdf)
            texto_extraido = "".join([pytesseract.image_to_string(pag, lang='spa') for pag in paginas_img])
        except Exception as e:
            print(f"❌ Error de OCR en {os.path.basename(ruta_pdf)}: {e}")
    return texto_extraido

def parse_fecha(fecha_str):
    if not fecha_str: return None
    try:
        # Intenta parsear formatos como "d de mes de yyyy"
        parts = fecha_str.lower().split()
        if len(parts) >= 3 and parts[1] == 'de':
            d = int(parts[0])
            mes_str = parts[2]
            anio = int(parts[3])
            meses = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
            mes = meses.get(mes_str)
            if mes: return datetime(anio, mes, d).date()
    except Exception:
        pass
    return None

def extraer_metadatos_causa(texto):
    metadatos = {"rit": None, "tribunal": None, "comuna": None, "materia": None, "fecha": None, "estado": None}
    texto_lower = texto.lower()

    for key, patterns in PATRONES_METADATOS.items():
        if not isinstance(patterns, list): patterns = [patterns]
        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                # Captura el primer grupo que no sea None
                valor = next((g for g in match.groups() if g is not None), match.group(0))
                # Limpiar puntuación común que puede quedar pegada al nombre (ej. "Puente Alto.")
                valor_limpio = valor.strip(" .,;:\n\t\"'")
                
                if key == 'fecha':
                    metadatos[key] = parse_fecha(valor_limpio)
                    break
                elif key == 'comuna':
                    # Validación estricta: Verificar si lo capturado es realmente una comuna conocida
                    comuna_encontrada = None
                    valor_lower = valor_limpio.lower()
                    # Buscar coincidencia exacta insensible a mayúsculas en el mapa
                    for c in MAPA_COMUNA_REGION:
                        if c.lower() == valor_lower:
                            comuna_encontrada = c
                            break
                    
                    if comuna_encontrada:
                        metadatos[key] = comuna_encontrada.upper()
                        break # Éxito, comuna válida encontrada
                    else:
                        continue # Falso positivo (ej. "Garantía"), probar siguiente patrón
                else:
                    metadatos[key] = valor_limpio.title()
                    break # Pasa a la siguiente clave

    # Fallback: Si no se encontró comuna con regex, buscar directamente en el texto
    if not metadatos.get("comuna"):
        # Normalizar texto: reemplazar saltos de línea y puntuación por espacios para evitar uniones indebidas
        # Ej: "Puente Alto." -> "Puente Alto " (mantenemos comillas simples para nombres como O'Higgins)
        texto_normalizado = re.sub(r'[^\w\s\']', ' ', texto_lower).replace('\n', ' ')
        texto_normalizado = re.sub(r'\s+', ' ', texto_normalizado).strip()
        
        for comuna in LISTA_COMUNAS:
            # Búsqueda simple de subcadena
            if comuna.lower() in texto_normalizado:
                metadatos["comuna"] = comuna.upper()
                break

    return metadatos

def identificar_partes(texto):
    partes = {}
    # Limitar la búsqueda a los primeros 3000 caracteres para mayor precisión
    texto_inicio = texto[:4000] # Aumentamos un poco el rango de búsqueda

    # Estrategia de 2 pasos:
    # 1. Buscar todos los nombres precedidos por "don" o "doña".
    # 2. Buscar todos los roles y asociarlos en orden.

    # Patrón general para encontrar nombres con título
    patron_nombres = r"(?i)(?:don|doña)\s+([A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ\s',.-]+?)(?:\s*,|\s+RUT|\s+cédula|\n)"
    nombres_encontrados = re.findall(patron_nombres, texto_inicio)

    if not nombres_encontrados:
        # Si no se encuentra nada con "don/doña", volvemos a la estrategia anterior como fallback
        for rol, patron in PATRONES_ROLES.items():
            match = re.search(patron, texto_inicio, re.IGNORECASE)
            if match:
                partes[rol] = match.group(1).strip().title()
        return partes

    # 3. Asociar roles a los nombres encontrados
    if re.search(r"\b(?:víctima|afectado|ofendido|causante|adulto\s+mayor)\b", texto_inicio, re.IGNORECASE):
        partes['victima'] = nombres_encontrados[0].strip().title()
    if re.search(r"\b(?:demandante|actora|denunciante|requirente)\b", texto_inicio, re.IGNORECASE) and 'demandante' not in partes and len(nombres_encontrados) > 0:
        partes['demandante'] = nombres_encontrados[0].strip().title()
    if re.search(r"\b(?:demandado|denunciado|requerido|imputado)\b", texto_inicio, re.IGNORECASE) and 'demandado' not in partes and len(nombres_encontrados) > 1:
        partes['demandado'] = nombres_encontrados[1].strip().title()

    return partes

def log_user_action(usuario_id, accion, detalles="", session=None):
    """
    Guarda una acción de usuario en la tabla de auditoría.
    Si se proporciona una sesión, la reutiliza. Si no, crea una nueva.
    """
    def _log_action(s):
        log_entry = AuditoriaAccion(usuario_id=usuario_id, accion=accion, detalles=detalles)
        s.add(log_entry)

    if session:
        # Si nos pasan una sesión, la usamos sin hacer commit aquí.
        _log_action(session)
    else:
        # Si no hay sesión, creamos una para esta única acción.
        session = Session()
        try:
            with db_lock:
                _log_action(session)
                session.commit()
        finally:
            session.close()

def log_system_error(description):
    """Guarda un evento de error en la tabla de logs del sistema."""
    # Esta función usa su propia sesión para asegurar que el log se guarde
    # incluso si la sesión principal hace un rollback.
    session = Session()
    try:
        with db_lock:
            log_entry = LogSistema(
                tipo_evento='Error',
                descripcion=description,
                estado_log='Abierto'
            )
            session.add(log_entry)
            session.commit()
    except Exception as e:
        print(f"FATAL: No se pudo guardar el log de error en la BD: {e}")
        # No hacemos rollback aquí porque la sesión es solo para este log

def procesar_y_guardar_causa(ruta_pdf_origen, usuario_id):
    """
    Procesa un único archivo PDF y lo guarda en la base de datos.
    Retorna (True, "Mensaje de éxito") o (False, "Mensaje de error").
    """
    CARPETA_ARCHIVADOS = "data/causas_archivadas"
    os.makedirs(CARPETA_ARCHIVADOS, exist_ok=True)
    
    nombre_archivo = os.path.basename(ruta_pdf_origen)
    session = Session()
    
    with db_lock:
        try:
            # 1. Verificar si el archivo ya fue procesado
            if session.query(DocumentoPDF).filter_by(nombre_archivo=nombre_archivo).first():
                return False, f"El archivo '{nombre_archivo}' ya ha sido procesado anteriormente."

            # 2. Extraer texto
            texto = extraer_texto_pdf_con_ocr(ruta_pdf_origen)
            if not texto:
                return False, "No se pudo extraer texto del PDF."

            # 3. Extraer metadatos y partes
            metadatos = extraer_metadatos_causa(texto)
            rit_causa = metadatos.get("rit") or nombre_archivo.replace('.pdf', '')
            partes = identificar_partes(texto)
            
            sujeto_principal_nombre = next(iter(partes.values()), f"Anónimo_{rit_causa}")
            # Lógica mejorada para seleccionar el sujeto principal, priorizando el rol de 'víctima'
            sujeto_principal_nombre = None
            if 'victima' in partes:
                sujeto_principal_nombre = partes['victima']
            elif 'demandante' in partes:
                sujeto_principal_nombre = partes['demandante']
            elif partes:
                sujeto_principal_nombre = next(iter(partes.values()))

            # 4. Crear/Obtener AdultoMayor
            adulto = session.query(AdultoMayor).filter_by(nombre=sujeto_principal_nombre).first()
            if not adulto:
                adulto = AdultoMayor(nombre=sujeto_principal_nombre)
                session.add(adulto)
                session.flush()

            # 5. Copiar archivo y crear CausaJudicial
            ruta_destino = os.path.join(CARPETA_ARCHIVADOS, nombre_archivo)
            shutil.copy(ruta_pdf_origen, ruta_destino)

            causa = CausaJudicial(
                RIT=rit_causa,
                tribunal=metadatos.get("tribunal") or "Familia",
                comuna=metadatos.get("comuna"),
                materia=metadatos.get("materia"),
                fecha_ingreso=metadatos.get("fecha"),
                estado_procesal=metadatos.get("estado"),
                descripcion=texto[:500],
                adulto_id=adulto.id,
                usuario_carga_id=usuario_id,
                ruta_archivo_interno=ruta_destino
            )
            session.add(causa)
            session.flush()

            # 6. Crear DocumentoPDF
            doc_pdf = DocumentoPDF(nombre_archivo=nombre_archivo, texto_extraido=texto, causa_id=causa.id)
            session.add(doc_pdf)

            # 7. Identificar y asociar variables de riesgo
            # Ahora se leen las variables y sus patrones directamente desde la BD
            variables_activas_db = session.query(VariableRiesgo).filter_by(estado='Activa').all()
            variables_encontradas = []
            for variable in variables_activas_db:
                if not variable.patrones:
                    continue
                # Comprobar cada patrón para la variable actual
                for patron in variable.patrones.splitlines():
                    if patron and re.search(patron, texto, re.IGNORECASE):
                        variables_encontradas.append(variable)
                        break # Pasar a la siguiente variable una vez que se encuentra una coincidencia

            if variables_encontradas:
                evaluacion = EvaluacionRiesgo(
                    nivel_riesgo="Por determinar",
                    observaciones=f"Análisis automático. Variables encontradas: {', '.join([v.nombre for v in variables_encontradas])}",
                    causa_id=causa.id
                )
                for var in variables_encontradas:
                    evaluacion.variables.append(var)
                session.add(evaluacion)

            # 8. Confirmar transacción
            session.commit()
            return True, f"Causa '{rit_causa}' cargada y analizada exitosamente."

        except Exception as e:
            session.rollback()
            error_msg = f"Error crítico al procesar '{nombre_archivo}': {e}"
            print(f"❌ {error_msg}")
            log_system_error(error_msg) # Registrar el error en la tabla de logs
            return False, f"Ocurrió un error inesperado al procesar el archivo."
        finally:
            session.close()

def finalizar_causa_por_rit(rit_causa, usuario_id):
    """
    Cambia el estado de una causa a 'Finalizada' y establece la fecha de finalización.
    Retorna (True, "Mensaje de éxito") o (False, "Mensaje de error").
    """
    session = Session()
    with db_lock:
        try:
            causa = session.query(CausaJudicial).filter_by(RIT=rit_causa).first()
            if not causa:
                return False, f"No se encontró una causa con RIT '{rit_causa}'."
            
            if causa.estado_causa == 'Finalizada':
                return False, f"La causa '{rit_causa}' ya se encuentra finalizada."

            causa.estado_causa = 'Finalizada'
            causa.fecha_finalizacion = datetime.now()
            session.commit()
            log_user_action(usuario_id, "FINALIZAR_CAUSA", f"RIT: {rit_causa}")
            return True, f"La causa '{rit_causa}' ha sido marcada como finalizada."
        except Exception as e:
            session.rollback()
            print(f"❌ Error al finalizar la causa '{rit_causa}': {e}")
            return False, "Ocurrió un error inesperado al finalizar la causa."
        finally:
            session.close()

def obtener_ruta_pdf_por_rit(rit_causa):
    """
    Busca una causa por su RIT y retorna la ruta de su archivo PDF.
    Retorna la ruta del archivo o None si no se encuentra.
    """
    session = Session()
    try:
        causa = session.query(CausaJudicial).filter_by(RIT=rit_causa).first()
        if causa and causa.ruta_archivo_interno:
            return causa.ruta_archivo_interno
        return None
    finally:
        session.close()

def cargar_detalles_causa(rit_causa):
    """
    Carga todos los detalles de una causa específica, incluyendo sus relaciones
    (evaluaciones, variables, documentos).
    """
    session = Session()
    try:
        causa_detallada = (
            session.query(CausaJudicial)
            .filter(CausaJudicial.RIT == rit_causa)
            .options(
                joinedload(CausaJudicial.evaluaciones).joinedload(EvaluacionRiesgo.variables),
                joinedload(CausaJudicial.documentos)
            )
            .first()
        )
        return causa_detallada
    finally:
        session.close()

def cargar_causas_finalizadas(search_term=None):
    """
    Carga todas las causas con estado 'Finalizada' desde la BD.
    Si se provee un search_term, filtra por RIT o nombre del adulto mayor.
    """
    session = Session()
    try:
        query = (
            session.query(CausaJudicial)
            .filter(CausaJudicial.estado_causa == 'Finalizada')
            .options(joinedload(CausaJudicial.adulto_mayor))
        )
        
        if search_term:
            # Búsqueda por RIT o por nombre del adulto mayor
            query = query.filter(
                (CausaJudicial.RIT.ilike(f"%{search_term}%")) |
                (AdultoMayor.nombre.ilike(f"%{search_term}%"))
            )

        return query.order_by(CausaJudicial.fecha_finalizacion.desc()).all()
    finally:
        session.close()

# === LÓGICA PARA GESTIÓN DE VARIABLES ===

def cargar_todas_variables():
    """Carga todas las variables de riesgo para la tabla de gestión."""
    session = Session()
    try:
        return session.query(VariableRiesgo).order_by(VariableRiesgo.nombre).all()
    finally:
        session.close()

def guardar_variable(data, usuario_id):
    """Crea o actualiza una variable de riesgo. Incluye validación de regex."""
    session = Session()
    with db_lock:
        try:
            # Validar patrones de regex
            if data['patrones']:
                for i, patron in enumerate(data['patrones'].splitlines()):
                    if not patron: continue
                    try:
                        re.compile(patron)
                    except re.error as e:
                        return False, f"Error en el patrón de la línea {i+1}: {e}"

            if data['id']: # Actualizar
                variable = session.query(VariableRiesgo).get(data['id'])
                if not variable:
                    return False, "La variable que intentas editar no existe."
                
                accion_log = "MODIFICAR_VARIABLE"
                variable.nombre = data['nombre']
                variable.descripcion = data['descripcion']
                variable.peso_relativo = data['peso']
                variable.patrones = data['patrones']
                variable.tipo = 'Agravante' if data['peso'] > 0 else 'Mitigante'
            else: # Crear
                accion_log = "CREAR_VARIABLE"
                variable = VariableRiesgo(
                    nombre=data['nombre'],
                    descripcion=data['descripcion'],
                    peso_relativo=data['peso'],
                    patrones=data['patrones'],
                    tipo='Agravante' if data['peso'] > 0 else 'Mitigante',
                    estado='Activa'
                )
                session.add(variable)
            
            session.commit()
            log_user_action(usuario_id, accion_log, f"Nombre: {variable.nombre}")
            return True, f"Variable '{variable.nombre}' guardada exitosamente."
        except Exception as e:
            session.rollback()
            print(f"❌ Error al guardar variable: {e}")
            return False, "Ocurrió un error inesperado al guardar la variable."
        finally:
            session.close()

def toggle_variable_status(variable_id, editor_usuario_id):
    """
    Cambia el estado de una variable entre 'Activa' e 'Inactiva'.
    Retorna (True, "Mensaje de éxito") o (False, "Mensaje de error").
    """
    session = Session()
    with db_lock:
        try:
            variable = session.query(VariableRiesgo).get(variable_id)
            if not variable:
                return False, f"No se encontró la variable con ID {variable_id}."

            estado_anterior = variable.estado
            variable.estado = 'Inactiva' if estado_anterior == 'Activa' else 'Activa'
            
            log_user_action(editor_usuario_id, "CAMBIAR_ESTADO_VARIABLE", f"ID: {variable.id}, Nombre: {variable.nombre}, Nuevo Estado: {variable.estado}")
            session.commit()
            return True, f"El estado de la variable '{variable.nombre}' ha sido cambiado a '{variable.estado}'."
        except Exception as e:
            session.rollback()
            print(f"❌ Error al cambiar estado de variable: {e}")
            return False, "Ocurrió un error inesperado al cambiar el estado."
        finally:
            session.close()

# === LÓGICA PARA GESTIÓN DE PROGRAMAS SOCIALES ===

def cargar_programas_sociales():
    """Carga todos los programas sociales. Usa cache para rendimiento."""
    global _PROGRAMAS_CACHE
    if _PROGRAMAS_CACHE is not None:
        return _PROGRAMAS_CACHE
    
    session = Session()
    try:
        programas = session.query(ProgramaSocial).order_by(ProgramaSocial.nombre).all()
        # Deserializar JSON para uso inmediato si es necesario, aunque SQLAlchemy devuelve objetos
        # Mantenemos los objetos SQLAlchemy pero nos aseguramos de que estén desconectados o sean simples
        # Para el cache, mejor guardar una lista de objetos desconectados o diccionarios si hay problemas de sesión
        # Por simplicidad, retornamos la lista. Si hay problemas de "Session closed", habrá que copiar datos.
        session.expunge_all() 
        _PROGRAMAS_CACHE = programas
        return programas
    finally:
        session.close()

def guardar_programa_social(data, usuario_id):
    """Crea o actualiza un programa social."""
    global _PROGRAMAS_CACHE
    session = Session()
    with db_lock:
        try:
            if data['id']: # Actualizar
                prog = session.query(ProgramaSocial).get(data['id'])
                if not prog: return False, "El programa no existe."
                prog.nombre = data['nombre']
                prog.variables_clave = json.dumps(data['variables_clave'])
                prog.variables_contexto = json.dumps(data['variables_contexto'])
                prog.descripcion = data['descripcion']
                accion = "MODIFICAR_PROGRAMA"
            else: # Crear
                prog = ProgramaSocial(
                    nombre=data['nombre'],
                    variables_clave=json.dumps(data['variables_clave']),
                    variables_contexto=json.dumps(data['variables_contexto']),
                    descripcion=data['descripcion']
                )
                session.add(prog)
                accion = "CREAR_PROGRAMA"
            
            session.commit()
            log_user_action(usuario_id, accion, f"Programa: {prog.nombre}")
            _PROGRAMAS_CACHE = None # Invalidar cache
            return True, f"Programa '{prog.nombre}' guardado exitosamente."
        except Exception as e:
            session.rollback()
            return False, f"Error al guardar programa: {e}"
        finally:
            session.close()

def eliminar_programa_social(prog_id, usuario_id):
    """Elimina un programa social."""
    global _PROGRAMAS_CACHE
    # Implementación básica (se deja como ejercicio o si se solicita explícitamente)
    # Por seguridad, a veces es mejor solo desactivar, pero aquí eliminaremos.
    pass 

# === LÓGICA PARA LOGS DEL SISTEMA ===

def cargar_logs_sistema(solo_abiertos=True):
    """Carga los logs del sistema desde la BD."""
    session = Session()
    try:
        query = session.query(LogSistema)
        if solo_abiertos:
            query = query.filter(LogSistema.estado_log == 'Abierto')
        return query.order_by(LogSistema.fecha_evento.desc()).all()
    finally:
        session.close()

def resolver_log(log_id, usuario_id):
    """Marca un log como 'Cerrado'."""
    session = Session()
    with db_lock:
        try:
            log_entry = session.query(LogSistema).get(log_id)
            if not log_entry:
                return False, f"No se encontró el log con ID {log_id}."
            
            log_entry.estado_log = 'Cerrado'
            log_entry.fecha_solucion = datetime.now()
            log_entry.usuario_responsable_id = usuario_id
            log_user_action(usuario_id, "RESOLVER_LOG_SISTEMA", f"Log ID: {log_id}")
            return True, f"Log ID {log_id} marcado como resuelto."
        except Exception as e:
            session.rollback()
            return False, f"Error al resolver el log: {e}"
        finally:
            session.close()

# === LÓGICA PARA GENERACIÓN ASISTIDA DE PATRONES ===

def generar_patrones_desde_palabras_clave(palabras_clave_texto):
    """Convierte una lista de palabras clave (una por línea) en patrones regex."""
    patrones_generados = []
    palabras_clave = palabras_clave_texto.strip().splitlines()
    for palabra in palabras_clave:
        palabra = palabra.strip()
        if not palabra:
            continue
        # Escapar caracteres especiales de regex y reemplazar espacios con \s+
        patron_simple = re.escape(palabra).replace(r'\ ', r'\s+')
        # Añadir \b para buscar palabras completas y (?i) para case-insensitive
        patron_final = fr"(?i)\b{patron_simple}\b"
        patrones_generados.append(patron_final)
    return patrones_generados

def probar_patrones_en_db(patrones):
    """Prueba una lista de patrones contra todos los textos de la BD y devuelve el conteo de hits."""
    session = Session()
    try:
        todos_los_textos = session.query(DocumentoPDF.texto_extraido).all()
        resultados = {patron: 0 for patron in patrones}
        for (texto,) in todos_los_textos:
            for patron in patrones:
                if re.search(patron, texto, re.IGNORECASE):
                    resultados[patron] += 1
        return True, resultados
    finally:
        session.close()

def reanalizar_todas_las_causas():
    """
    Recorre todas las causas, re-evalúa las variables de riesgo basadas en los patrones
    actuales en la BD y actualiza las evaluaciones.
    Retorna (True, "Mensaje") o (False, "Mensaje").
    """
    with db_lock:
        session = Session()
        try:
            print("🚀 Iniciando re-análisis de todas las causas...")
            # 1. Cargar todas las variables activas y sus patrones una sola vez
            variables_activas_db = session.query(VariableRiesgo).filter_by(estado='Activa').all()

            # 2. Cargar todas las causas con sus documentos y evaluaciones
            causas_a_revisar = session.query(CausaJudicial).options(
                joinedload(CausaJudicial.documentos),
                joinedload(CausaJudicial.evaluaciones).joinedload(EvaluacionRiesgo.variables)
            ).all()

            causas_actualizadas = 0
            commit_batch_size = 20 # Guardar cambios cada 20 causas para liberar el lock
            for causa in causas_a_revisar:
                if not causa.documentos or not causa.evaluaciones:
                    continue

                texto = causa.documentos[0].texto_extraido
                if not texto:
                    continue

                # 3. Re-identificar variables en el texto con los patrones actuales
                nuevas_variables_encontradas = []
                for variable in variables_activas_db:
                    if not variable.patrones: continue
                    for patron in variable.patrones.splitlines():
                        if patron and re.search(patron, texto, re.IGNORECASE):
                            nuevas_variables_encontradas.append(variable)
                            break
                
                # 3.1. NUEVO: Re-intentar detectar la comuna si no existe o para actualizarla
                nuevos_metadatos = extraer_metadatos_causa(texto)
                if nuevos_metadatos.get("comuna"):
                    causa.comuna = nuevos_metadatos["comuna"]
                
                # 4. Actualizar la evaluación existente
                causa.evaluaciones[0].variables = nuevas_variables_encontradas
                causa.evaluaciones[0].observaciones = f"Re-análisis automático. Variables encontradas: {', '.join([v.nombre for v in nuevas_variables_encontradas])}"
                causas_actualizadas += 1
                
                # Guardar en lotes para no bloquear la base de datos por mucho tiempo
                if causas_actualizadas % commit_batch_size == 0:
                    session.commit()

            session.commit() # Asegurarse de guardar el último lote
            msg = f"Re-análisis completado. Se actualizaron las evaluaciones de {causas_actualizadas} causas."
            print(f"✅ {msg}")
            return True, msg
        except Exception as e:
            session.rollback()
            error_msg = f"Error crítico durante el re-análisis: {e}"
            print(f"❌ {error_msg}")
            log_system_error(error_msg)
            return False, error_msg
        finally:
            session.close()

def eliminar_todas_las_causas(usuario_id):
    """
    Elimina TODAS las causas, documentos, evaluaciones y adultos mayores de la base de datos.
    También limpia la carpeta de archivos físicos.
    Mantiene usuarios, variables, programas y logs.
    """
    session = Session()
    with db_lock:
        try:
            # 1. Eliminar datos de la BD
            # Borramos en orden para respetar dependencias (aunque cascade ayuda)
            session.query(EvaluacionRiesgo).delete()
            session.query(DocumentoPDF).delete()
            session.query(CausaJudicial).delete()
            session.query(AdultoMayor).delete()
            
            session.commit()
            
            # 2. Limpiar carpeta de archivos físicos
            carpeta_archivados = "data/causas_archivadas"
            if os.path.exists(carpeta_archivados):
                for filename in os.listdir(carpeta_archivados):
                    file_path = os.path.join(carpeta_archivados, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"No se pudo borrar {file_path}. Razón: {e}")
            
            log_user_action(usuario_id, "RESET_CAUSAS", "Se eliminaron todas las causas y archivos asociados (Limpieza Total).")
            return True, "Sistema limpiado exitosamente. Todas las causas han sido eliminadas."
        except Exception as e:
            session.rollback()
            return False, f"Error al limpiar el sistema: {e}"
        finally:
            session.close()

# === LÓGICA PARA GESTIÓN DE USUARIOS ===

def cargar_todos_los_usuarios():
    """Carga todos los usuarios del sistema."""
    session = Session()
    try:
        return session.query(Usuario).order_by(Usuario.nombre).all()
    finally:
        session.close()

def guardar_usuario(data, editor_usuario_id):
    """Crea o actualiza un usuario."""
    session = Session()
    from core.auth import hashear_password # Importación local para romper el ciclo
    with db_lock:
        try:
            if data['id']: # Actualizar usuario existente
                usuario = session.query(Usuario).get(data['id'])
                if not usuario:
                    return False, "El usuario que intentas editar no existe."
                
                # Verificar si el RUT o email ya existen en otro usuario
                if session.query(Usuario).filter(Usuario.rut == data['rut'], Usuario.id != data['id']).first():
                    return False, f"El RUT '{data['rut']}' ya está registrado para otro usuario."
                if session.query(Usuario).filter(Usuario.email == data['email'], Usuario.id != data['id']).first():
                    return False, f"El email '{data['email']}' ya está registrado para otro usuario."

                usuario.nombre = data['nombre']
                usuario.rut = data['rut']
                usuario.email = data['email']
                usuario.rol = data['rol']
                usuario.estado = data['estado']
                if data['password']: # Solo actualizar contraseña si se proporcionó una nueva
                    usuario.password_hash = hashear_password(data['password'])
                
                log_user_action(editor_usuario_id, "MODIFICAR_USUARIO", f"Usuario afectado: {usuario.nombre} (ID: {usuario.id})")
                # Aquí se podría añadir lógica de auditoría para cambios de usuario

            else: # Crear nuevo usuario
                # Verificar si el RUT o email ya existen
                if session.query(Usuario).filter_by(rut=data['rut']).first():
                    return False, f"El RUT '{data['rut']}' ya está registrado."
                if session.query(Usuario).filter_by(email=data['email']).first():
                    return False, f"El email '{data['email']}' ya está registrado."

                if not data['password']:
                    return False, "Para un nuevo usuario, la contraseña no puede estar vacía."

                usuario = Usuario(
                    nombre=data['nombre'],
                    rut=data['rut'],
                    email=data['email'],
                    rol=data['rol'],
                    password_hash=hashear_password(data['password']),
                    estado=data['estado']
                )
                session.add(usuario)
                session.flush() # Para obtener el ID del nuevo usuario
                # Si es el primer usuario, el editor es él mismo.
                id_editor_real = editor_usuario_id if editor_usuario_id is not None else usuario.id
                log_user_action(
                    id_editor_real, 
                    "CREAR_USUARIO", 
                    f"Nuevo usuario: {usuario.nombre} (ID: {usuario.id})", 
                    session=session
                )
            
            session.commit()
            return True, f"Usuario '{usuario.nombre}' guardado exitosamente."
        except Exception as e:
            session.rollback()
            error_msg = f"Error al guardar usuario: {e}"
            print(f"❌ {error_msg}")
            log_system_error(error_msg) # Registrar el error en la tabla de logs del sistema
            return False, f"Ocurrió un error inesperado al guardar el usuario: {e}"
        finally:
            session.close()

def toggle_usuario_status(usuario_id, editor_usuario_id):
    """
    Cambia el estado de un usuario entre 'Activo' e 'Inactivo'.
    Retorna (True, "Mensaje de éxito") o (False, "Mensaje de error").
    """
    with db_lock:
        session = Session()
        try:
            usuario = session.query(Usuario).get(usuario_id)
            if not usuario:
                return False, f"No se encontró el usuario con ID {usuario_id}."
            
            estado_anterior = usuario.estado
            usuario.estado = 'Inactivo' if estado_anterior == 'Activo' else 'Activo'
            
            log_user_action(editor_usuario_id, "CAMBIAR_ESTADO_USUARIO", f"Usuario: {usuario.nombre}, Nuevo Estado: {usuario.estado}")
            session.commit()
            return True, f"El estado del usuario '{usuario.nombre}' ha sido cambiado a '{usuario.estado}'."
        except Exception as e:
            session.rollback()
            print(f"❌ Error al cambiar estado de usuario: {e}")
            return False, "Ocurrió un error inesperado al cambiar el estado del usuario."
        finally:
            session.close()

# === LÓGICA PARA AUDITORÍA ===

def cargar_registros_auditoria():
    """Carga todos los registros de la tabla de auditoría de acciones."""
    session = Session()
    try:
        return session.query(AuditoriaAccion).options(joinedload(AuditoriaAccion.usuario)).order_by(AuditoriaAccion.fecha_accion.desc()).all()
    finally:
        session.close()


# === LÓGICA PARA DASHBOARD/REPORTES ===

def get_dashboard_stats():
    """
    Calcula la distribución de derivaciones por programa para el dashboard.
    Retorna un diccionario con los conteos de la sugerencia principal.
    """
    session = Session()
    try:
        causas_activas = cargar_causas_activas() # Reutilizamos la función existente
        distribution = {}
        for causa in causas_activas:
            sugerencia_info = calcular_sugerencia_derivacion(causa)
            # Tomamos la primera sugerencia (la principal) antes del " / "
            sugerencia_principal = sugerencia_info['sugerencia'].split(" / ")[0]
            
            if sugerencia_principal not in distribution:
                distribution[sugerencia_principal] = 0
            distribution[sugerencia_principal] += 1
            
        return True, dict(sorted(distribution.items(), key=lambda item: item[1], reverse=True))
    except Exception as e:
        return False, f"Error al obtener estadísticas: {e}"
    finally:
        session.close()