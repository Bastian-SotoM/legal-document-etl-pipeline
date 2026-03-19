# -*- coding: utf-8 -*-
"""
Script para Poblar la Base de Datos (Versión 2.0)

Lee archivos PDF desde una carpeta de entrada, extrae metadatos y variables
de riesgo, y guarda toda la información en la base de datos siguiendo el
nuevo esquema.
"""

import os
import re
import shutil
from datetime import datetime
import fitz  # PyMuPDF
from pdf2image import convert_from_path
import pytesseract
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Asegurarnos de que el script pueda encontrar los módulos de 'core'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.models import AdultoMayor, CausaJudicial, DocumentoPDF, EvaluacionRiesgo, VariableRiesgo, Usuario 
from core.config import NOMBRES_VARIABLES, PATRONES_VARIABLES, PATRONES_METADATOS, PATRONES_ROLES

# === CONFIGURACIÓN ===
CARPETA_ENTRADA = "causas_a_procesar"  # Carpeta donde dejas los PDFs para procesar
CARPETA_ARCHIVADOS = "data/causas_archivadas" # Carpeta donde el sistema guarda su copia
BD_PATH = "data/riesgo_patrimonial.db"

# === CONEXIÓN A BASE DE DATOS ===
engine = create_engine(f"sqlite:///{BD_PATH}", echo=False)
Session = sessionmaker(bind=engine)

# === LÓGICA DE EXTRACCIÓN DE METADATOS ===

def parse_fecha(fecha_str):
    """Parsea la fecha a objeto Date."""
    if not fecha_str: return None
    try:
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
    """Extrae RIT, tribunal, materia, etc., usando los patrones mejorados."""
    metadatos = {"rit": None, "tribunal": None, "materia": None, "fecha": None, "estado": None}

    # Extraer RIT
    for pattern in PATRONES_METADATOS["rit"]:
        matches = re.findall(pattern, texto)
        if matches:
            candidate = matches[-1]
            if isinstance(candidate, tuple): candidate = candidate[0]
            candidate = candidate.replace('\n', ' ').strip()
            year_match = re.search(r'(\d{4})$', candidate)
            if year_match and 2000 <= int(year_match.group(1)) <= 2026:
                metadatos["rit"] = candidate
                break

    # Extraer Tribunal
    for pattern in PATRONES_METADATOS["tribunal"]:
        matches = re.findall(pattern, texto)
        if matches:
            candidate = matches[-1]
            if isinstance(candidate, tuple): candidate = candidate[0] if candidate[0] else candidate[1] if len(candidate) > 1 else str(candidate)
            candidate = candidate.replace('\n', ' ').strip()
            if candidate and len(candidate) > 2:
                metadatos["tribunal"] = candidate.title()
                break

    # Extraer Materia
    materia_match = re.search(PATRONES_METADATOS["materia"], texto)
    if materia_match:
        metadatos["materia"] = materia_match.group(1).title().strip()

    # Extraer Fecha
    fecha_match = re.search(PATRONES_METADATOS["fecha"], texto)
    if fecha_match:
        metadatos["fecha"] = parse_fecha(fecha_match.group(1))

    # Extraer Estado
    estado_match = re.search(PATRONES_METADATOS["estado"], texto)
    if estado_match:
        metadatos["estado"] = estado_match.group(1).strip()
        
    # Si el RIT no se encontró, usar nombre de archivo como fallback
    if not metadatos["rit"]:
        print("  -> No se encontró RIT con patrones, usando nombre de archivo como fallback.")

    return metadatos


# Funciones de extracción y análisis
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

def identificar_partes(texto):
    partes = {}
    for rol, patron in PATRONES_ROLES.items():
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            nombre_completo = match.group(1).strip()
            partes[rol] = nombre_completo
    if not partes:
        partes['parte_1'] = 'Anónimo'
    return partes

def identificar_variable_con_contexto(texto, patrones):
    for patron in patrones:
        if re.search(patron, texto, re.IGNORECASE):
            return True
    return False

# === PROCESO PRINCIPAL: ANALIZAR Y POBLAR BD ===
def poblar_base_de_datos():
    os.makedirs(CARPETA_ARCHIVADOS, exist_ok=True)
    if not os.path.exists(CARPETA_ENTRADA):
        print(f"⚠️ No se encontró la carpeta '{CARPETA_ENTRADA}'. Por favor, créala y añade archivos PDF.")
        return

    session = Session()
    try:
        # Traer las variables desde la BD a un diccionario para fácil acceso
        variables_db = {v.nombre: v for v in session.query(VariableRiesgo).all()}
        # Asumimos que el usuario con ID 1 es el administrador que ejecuta este script
        admin_user = session.query(Usuario).filter_by(id=1).first()

        if not variables_db:
            print("❌ No hay variables de riesgo en la base de datos. Ejecuta '1_preparar_bd.py' primero.")
            return
        if not admin_user:
            print("❌ No se ha creado un usuario administrador (ID=1). Ejecuta 'gestion_usuarios.py' para crear el primer usuario.")
            return

        for archivo in sorted([f for f in os.listdir(CARPETA_ENTRADA) if f.endswith(".pdf")]):
            ruta_origen = os.path.join(CARPETA_ENTRADA, archivo)
            print(f"\nProcesando archivo: {archivo}")

            if session.query(DocumentoPDF).filter_by(nombre_archivo=archivo).first():
                print("  -> Archivo ya existe en la BD. Saltando.")
                continue

            texto = extraer_texto_pdf_con_ocr(ruta_origen)
            if not texto:
                print("  -> No se pudo extraer texto. Saltando archivo.")
                continue

            metadatos = extraer_metadatos_causa(texto)
            rit_causa = metadatos.get("rit") or archivo.replace('.pdf', '')
            print(f"  -> RIT extraído: {rit_causa}")

            partes = identificar_partes(texto)
            sujeto_principal = {}
            if 'victima' in partes:
                sujeto_principal = {'victima': partes['victima']}
            elif 'demandante' in partes:
                sujeto_principal = {'demandante': partes['demandante']}
            elif partes:
                primer_rol = list(partes.keys())[0]
                sujeto_principal = {primer_rol: partes[primer_rol]}

            if not sujeto_principal:
                print("  -> No se pudo identificar un sujeto principal. Saltando.")
                continue

            rol, nombre_sujeto = list(sujeto_principal.items())[0]
            print(f"  -> Sujeto principal: {nombre_sujeto} (Rol: {rol})")

            adulto = session.query(AdultoMayor).filter_by(nombre=nombre_sujeto).first()
            if not adulto:
                adulto = AdultoMayor(nombre=nombre_sujeto)
                session.add(adulto)
                session.flush()

            # Copiar el archivo a la carpeta de archivados del sistema
            ruta_destino = os.path.join(CARPETA_ARCHIVADOS, archivo)
            shutil.copy(ruta_origen, ruta_destino)

            causa = CausaJudicial(
                RIT=rit_causa, tribunal=metadatos.get("tribunal"), materia=metadatos.get("materia"),
                fecha_ingreso=metadatos.get("fecha"), estado_procesal=metadatos.get("estado"),
                descripcion=texto[:500], 
                adulto_id=adulto.id,
                usuario_carga_id=admin_user.id, # Asociar al usuario que carga
                ruta_archivo_interno=ruta_destino # Guardar la nueva ruta
            )
            session.add(causa)
            session.flush()

            doc_pdf = DocumentoPDF(nombre_archivo=archivo, texto_extraido=texto, causa_id=causa.id)
            session.add(doc_pdf)

            variables_encontradas = [
                var_nombre for var_nombre in NOMBRES_VARIABLES 
                if identificar_variable_con_contexto(texto, PATRONES_VARIABLES.get(var_nombre, []))
            ]
            print(f"  -> Variables encontradas ({len(variables_encontradas)}): {', '.join(variables_encontradas) or 'Ninguna'}")

            if variables_encontradas:
                evaluacion = EvaluacionRiesgo(
                    nivel_riesgo="Por determinar",
                    observaciones=f"Análisis automático. Variables encontradas: {', '.join(variables_encontradas)}",
                    causa_id=causa.id
                )
                for nombre_var in variables_encontradas:
                    if nombre_var in variables_db:
                        evaluacion.variables.append(variables_db[nombre_var])
                session.add(evaluacion)

            session.commit()
            print(f"  -> ✅ '{archivo}' guardado en la base de datos.")

    except Exception as e:
        print(f"❌ Error durante el procesamiento: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    poblar_base_de_datos()
    print("\n🎯 Proceso de población de la base de datos completado.")