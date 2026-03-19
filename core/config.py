# -*- coding: utf-8 -*-
"""
Archivo de Configuración Central

Contiene todas las variables, patrones de búsqueda (regex) y pesos
utilizados en el sistema de análisis de riesgo patrimonial.
"""

import re

# === LISTAS GEOGRÁFICAS PARA DETECCIÓN ===
LISTA_REGIONES = [
    "Arica y Parinacota", "Tarapacá", "Antofagasta", "Atacama", "Coquimbo", "Valparaíso",
    "Metropolitana", "O'Higgins", "Maule", "Ñuble", "Biobío", "Araucanía", "Los Ríos",
    "Los Lagos", "Aysén", "Magallanes"
]

# Mapeo de Comuna a Región para la lógica de territorialidad
MAPA_COMUNA_REGION = {
    # Arica y Parinacota
    "Arica": "Arica y Parinacota", "Camarones": "Arica y Parinacota", "Putre": "Arica y Parinacota", "General Lagos": "Arica y Parinacota",
    # Tarapacá
    "Iquique": "Tarapacá", "Alto Hospicio": "Tarapacá", "Pozo Almonte": "Tarapacá", "Camiña": "Tarapacá", "Colchane": "Tarapacá", "Huara": "Tarapacá", "Pica": "Tarapacá",
    # Antofagasta
    "Antofagasta": "Antofagasta", "Mejillones": "Antofagasta", "Sierra Gorda": "Antofagasta", "Taltal": "Antofagasta", "Calama": "Antofagasta", "Ollagüe": "Antofagasta", "San Pedro de Atacama": "Antofagasta", "Tocopilla": "Antofagasta", "María Elena": "Antofagasta",
    # Atacama
    "Copiapó": "Atacama", "Caldera": "Atacama", "Tierra Amarilla": "Atacama", "Chañaral": "Atacama", "Diego de Almagro": "Atacama", "Vallenar": "Atacama", "Alto del Carmen": "Atacama", "Freirina": "Atacama", "Huasco": "Atacama",
    # Coquimbo
    "La Serena": "Coquimbo", "La Higuera": "Coquimbo", "Coquimbo": "Coquimbo", "Andacollo": "Coquimbo", "Vicuña": "Coquimbo", "Paihuano": "Coquimbo", "Ovalle": "Coquimbo", "Río Hurtado": "Coquimbo", "Monte Patria": "Coquimbo", "Combarbalá": "Coquimbo", "Punitaqui": "Coquimbo", "Illapel": "Coquimbo", "Salamanca": "Coquimbo", "Los Vilos": "Coquimbo", "Canela": "Coquimbo",
    # Valparaíso
    "Valparaíso": "Valparaíso", "Casablanca": "Valparaíso", "Concón": "Valparaíso", "Juan Fernández": "Valparaíso", "Puchuncaví": "Valparaíso", "Quintero": "Valparaíso", "Viña del Mar": "Valparaíso", "Isla de Pascua": "Valparaíso", "Los Andes": "Valparaíso", "Calle Larga": "Valparaíso", "Rinconada": "Valparaíso", "San Esteban": "Valparaíso", "La Ligua": "Valparaíso", "Cabildo": "Valparaíso", "Papudo": "Valparaíso", "Petorca": "Valparaíso", "Zapallar": "Valparaíso", "Quillota": "Valparaíso", "La Calera": "Valparaíso", "Hijuelas": "Valparaíso", "La Cruz": "Valparaíso", "Nogales": "Valparaíso", "San Antonio": "Valparaíso", "Algarrobo": "Valparaíso", "Cartagena": "Valparaíso", "El Quisco": "Valparaíso", "El Tabo": "Valparaíso", "Santo Domingo": "Valparaíso", "San Felipe": "Valparaíso", "Catemu": "Valparaíso", "Llaillay": "Valparaíso", "Panquehue": "Valparaíso", "Putaendo": "Valparaíso", "Santa María": "Valparaíso", "Quilpué": "Valparaíso", "Limache": "Valparaíso", "Olmué": "Valparaíso", "Villa Alemana": "Valparaíso",
    # Metropolitana
    "Santiago": "Metropolitana", "Cerrillos": "Metropolitana", "Cerro Navia": "Metropolitana", "Conchalí": "Metropolitana", "El Bosque": "Metropolitana", "Estación Central": "Metropolitana", "Huechuraba": "Metropolitana", "Independencia": "Metropolitana", "La Cisterna": "Metropolitana", "La Florida": "Metropolitana", "La Granja": "Metropolitana", "La Pintana": "Metropolitana", "La Reina": "Metropolitana", "Las Condes": "Metropolitana", "Lo Barnechea": "Metropolitana", "Lo Espejo": "Metropolitana", "Lo Prado": "Metropolitana", "Macul": "Metropolitana", "Maipú": "Metropolitana", "Ñuñoa": "Metropolitana", "Pedro Aguirre Cerda": "Metropolitana", "Peñalolén": "Metropolitana", "Providencia": "Metropolitana", "Pudahuel": "Metropolitana", "Quilicura": "Metropolitana", "Quinta Normal": "Metropolitana", "Recoleta": "Metropolitana", "Renca": "Metropolitana", "San Joaquín": "Metropolitana", "San Miguel": "Metropolitana", "San Ramón": "Metropolitana", "Vitacura": "Metropolitana", "Puente Alto": "Metropolitana", "Pirque": "Metropolitana", "San José de Maipo": "Metropolitana", "Colina": "Metropolitana", "Lampa": "Metropolitana", "Til Til": "Metropolitana", "San Bernardo": "Metropolitana", "Buin": "Metropolitana", "Calera de Tango": "Metropolitana", "Paine": "Metropolitana", "Melipilla": "Metropolitana", "Alhué": "Metropolitana", "Curacaví": "Metropolitana", "María Pinto": "Metropolitana", "San Pedro": "Metropolitana", "Talagante": "Metropolitana", "El Monte": "Metropolitana", "Isla de Maipo": "Metropolitana", "Padre Hurtado": "Metropolitana", "Peñaflor": "Metropolitana",
    # O'Higgins
    "Rancagua": "O'Higgins", "Codegua": "O'Higgins", "Coinco": "O'Higgins", "Coltauco": "O'Higgins", "Doñihue": "O'Higgins", "Graneros": "O'Higgins", "Las Cabras": "O'Higgins", "Machalí": "O'Higgins", "Malloa": "O'Higgins", "Mostazal": "O'Higgins", "Olivar": "O'Higgins", "Peumo": "O'Higgins", "Pichidegua": "O'Higgins", "Quinta de Tilcoco": "O'Higgins", "Rengo": "O'Higgins", "Requínoa": "O'Higgins", "San Vicente": "O'Higgins", "Pichilemu": "O'Higgins", "La Estrella": "O'Higgins", "Litueche": "O'Higgins", "Marchigüe": "O'Higgins", "Navidad": "O'Higgins", "Paredones": "O'Higgins", "San Fernando": "O'Higgins", "Chépica": "O'Higgins", "Chimbarongo": "O'Higgins", "Lolol": "O'Higgins", "Nancagua": "O'Higgins", "Palmilla": "O'Higgins", "Peralillo": "O'Higgins", "Placilla": "O'Higgins", "Pumanque": "O'Higgins", "Santa Cruz": "O'Higgins",
    # Maule
    "Talca": "Maule", "Constitución": "Maule", "Curepto": "Maule", "Empedrado": "Maule", "Maule": "Maule", "Pelarco": "Maule", "Pencahue": "Maule", "Río Claro": "Maule", "San Clemente": "Maule", "San Rafael": "Maule", "Cauquenes": "Maule", "Chanco": "Maule", "Pelluhue": "Maule", "Curicó": "Maule", "Hualañé": "Maule", "Licantén": "Maule", "Molina": "Maule", "Rauco": "Maule", "Romeral": "Maule", "Sagrada Familia": "Maule", "Teno": "Maule", "Vichuquén": "Maule", "Linares": "Maule", "Colbún": "Maule", "Longaví": "Maule", "Parral": "Maule", "Retiro": "Maule", "San Javier": "Maule", "Villa Alegre": "Maule", "Yerbas Buenas": "Maule",
    # Ñuble
    "Chillán": "Ñuble", "Bulnes": "Ñuble", "Cobquecura": "Ñuble", "Coelemu": "Ñuble", "Coihueco": "Ñuble", "Chillán Viejo": "Ñuble", "El Carmen": "Ñuble", "Ninhue": "Ñuble", "Ñiquén": "Ñuble", "Pemuco": "Ñuble", "Pinto": "Ñuble", "Portezuelo": "Ñuble", "Quillón": "Ñuble", "Quirihue": "Ñuble", "Ránquil": "Ñuble", "San Carlos": "Ñuble", "San Fabián": "Ñuble", "San Ignacio": "Ñuble", "San Nicolás": "Ñuble", "Treguaco": "Ñuble", "Yungay": "Ñuble",
    # Biobío
    "Concepción": "Biobío", "Coronel": "Biobío", "Chiguayante": "Biobío", "Florida": "Biobío", "Hualpén": "Biobío", "Hualqui": "Biobío", "Lota": "Biobío", "Penco": "Biobío", "San Pedro de la Paz": "Biobío", "Santa Juana": "Biobío", "Talcahuano": "Biobío", "Tomé": "Biobío", "Lebu": "Biobío", "Arauco": "Biobío", "Cañete": "Biobío", "Contulmo": "Biobío", "Curanilahue": "Biobío", "Los Álamos": "Biobío", "Tirúa": "Biobío", "Los Ángeles": "Biobío", "Antuco": "Biobío", "Cabrero": "Biobío", "Laja": "Biobío", "Mulchén": "Biobío", "Nacimiento": "Biobío", "Negrete": "Biobío", "Quilaco": "Biobío", "Quilleco": "Biobío", "San Rosendo": "Biobío", "Santa Bárbara": "Biobío", "Tucapel": "Biobío", "Yumbel": "Biobío", "Alto Biobío": "Biobío",
    # Araucanía
    "Temuco": "Araucanía", "Carahue": "Araucanía", "Cunco": "Araucanía", "Curarrehue": "Araucanía", "Freire": "Araucanía", "Galvarino": "Araucanía", "Gorbea": "Araucanía", "Lautaro": "Araucanía", "Loncoche": "Araucanía", "Melipeuco": "Araucanía", "Nueva Imperial": "Araucanía", "Padre Las Casas": "Araucanía", "Perquenco": "Araucanía", "Pitrufquén": "Araucanía", "Pucón": "Araucanía", "Saavedra": "Araucanía", "Teodoro Schmidt": "Araucanía", "Toltén": "Araucanía", "Vilcún": "Araucanía", "Villarrica": "Araucanía", "Cholchol": "Araucanía", "Angol": "Araucanía", "Curacautín": "Araucanía", "Ercilla": "Araucanía", "Lonquimay": "Araucanía", "Los Sauces": "Araucanía", "Lumaco": "Araucanía", "Purén": "Araucanía", "Renaico": "Araucanía", "Traiguén": "Araucanía", "Victoria": "Araucanía",
    # Los Ríos
    "Valdivia": "Los Ríos", "Corral": "Los Ríos", "Lanco": "Los Ríos", "Los Lagos": "Los Ríos", "Máfil": "Los Ríos", "Mariquina": "Los Ríos", "Paillaco": "Los Ríos", "Panguipulli": "Los Ríos", "La Unión": "Los Ríos", "Futrono": "Los Ríos", "Lago Ranco": "Los Ríos", "Río Bueno": "Los Ríos",
    # Los Lagos
    "Puerto Montt": "Los Lagos", "Calbuco": "Los Lagos", "Cochamó": "Los Lagos", "Fresia": "Los Lagos", "Frutillar": "Los Lagos", "Los Muermos": "Los Lagos", "Llanquihue": "Los Lagos", "Maullín": "Los Lagos", "Puerto Varas": "Los Lagos", "Castro": "Los Lagos", "Ancud": "Los Lagos", "Chonchi": "Los Lagos", "Curaco de Vélez": "Los Lagos", "Dalcahue": "Los Lagos", "Puqueldón": "Los Lagos", "Queilén": "Los Lagos", "Quellón": "Los Lagos", "Quemchi": "Los Lagos", "Quinchao": "Los Lagos", "Osorno": "Los Lagos", "Puerto Octay": "Los Lagos", "Purranque": "Los Lagos", "Puyehue": "Los Lagos", "Río Negro": "Los Lagos", "San Juan de la Costa": "Los Lagos", "San Pablo": "Los Lagos", "Chaitén": "Los Lagos", "Futaleufú": "Los Lagos", "Hualaihué": "Los Lagos", "Palena": "Los Lagos",
    # Aysén
    "Coyhaique": "Aysén", "Lago Verde": "Aysén", "Aysén": "Aysén", "Cisnes": "Aysén", "Guaitecas": "Aysén", "Cochrane": "Aysén", "O'Higgins": "Aysén", "Tortel": "Aysén", "Chile Chico": "Aysén", "Río Ibáñez": "Aysén",
    # Magallanes
    "Punta Arenas": "Magallanes", "Laguna Blanca": "Magallanes", "Río Verde": "Magallanes", "San Gregorio": "Magallanes", "Cabo de Hornos": "Magallanes", "Antártica": "Magallanes", "Porvenir": "Magallanes", "Primavera": "Magallanes", "Timaukel": "Magallanes", "Natales": "Magallanes", "Torres del Paine": "Magallanes",
}

# Generar lista de comunas para regex a partir del mapa
# Ordenamos por longitud descendente para que el regex priorice coincidencias más largas (ej. "San Pedro de Atacama" antes que "San Pedro")
LISTA_COMUNAS = sorted(list(MAPA_COMUNA_REGION.keys()), key=len, reverse=True)

# === LISTA DE VARIABLES DE RIESGO ===
DEFINICION_VARIABLES = [
    {"nombre": "Edad", "descripcion": "Considera la edad cronológica como un factor de vulnerabilidad interseccional, asignando mayor peso a los mayores de 80 años ('cuarta edad').", "peso": 1},
    {"nombre": "Condición Cognitiva", "descripcion": "Describe el estado de lucidez o conciencia actual, identificando episodios de desorientación o confusión aguda (vulnerabilidad inmediata).", "peso": 2},
    {"nombre": "Nivel Educativo", "descripcion": "Estima las competencias de alfabetización general y financiera. Un nivel bajo disminuye la capacidad para detectar fraudes.", "peso": 1},
    {"nombre": "Deterioro Cognitivo o Enfermedades Mentales", "descripcion": "Presencia documentada de patologías neurodegenerativas (Alzheimer, demencias) o trastornos psiquiátricos graves.", "peso": 2},
    {"nombre": "Dependencia de Otros", "descripcion": "Grado en que el adulto mayor ha perdido la capacidad física para ejecutar ABVD (alimentarse, asearse) sin ayuda.", "peso": 2},
    {"nombre": "Conflictos Familiares", "descripcion": "Presencia de violencia activa o patrones de relación disfuncional en el hogar, contextualizando el riesgo patrimonial.", "peso": 1},
    {"nombre": "Relación con Cuidadores", "descripcion": "Analiza la dinámica con quien asiste. Identifica signos de 'Síndrome del Cuidador Quemado' o negligencia.", "peso": 1},
    {"nombre": "Aislamiento Social", "descripcion": "Grado de desconexión con redes primarias y secundarias. La soledad objetiva o subjetiva invisibiliza el maltrato.", "peso": 2},
    {"nombre": "Acceso a Asesoría Legal", "descripcion": "Verifica si cuenta con representación jurídica (abogado privado o corporación), disminuyendo la necesidad de derivación.", "peso": -1},
    {"nombre": "Acceso a la Protección Judicial", "descripcion": "Identifica la vigencia de medidas cautelares activas, indicando que el riesgo físico ya fue abordado.", "peso": -1},
    {"nombre": "Interdicción Judicial", "descripcion": "Existencia de proceso legal vigente o necesidad manifiesta de iniciarlo para declarar incapacidad de administración.", "peso": 2},
    {"nombre": "Historial Patrimonial", "descripcion": "Evidencia de hechos constitutivos de delito económico (apropiación de pensiones, ventas irregulares).", "peso": 1},
    {"nombre": "Grado de Vulnerabilidad Económica", "descripcion": "Precariedad de ingresos, pobreza o dependencia exclusiva de pensiones básicas (PGU).", "peso": 2},
    {"nombre": "Disputas Hereditarias", "descripcion": "Conflictos familiares activos relacionados con sucesiones, posesiones efectivas o partición de bienes.", "peso": 1},
    {"nombre": "Acción de los Cuidadores", "descripcion": "Rol y acciones de los cuidadores que gestionan el patrimonio del adulto mayor.", "peso": 1}, # Se mantiene por compatibilidad, aunque se solapa con Relación con Cuidadores
    {"nombre": "Condiciones de Vivienda", "descripcion": "Evalúa habitabilidad y seguridad (hacinamiento, falta de servicios, tenencia precaria).", "peso": 1},
    {"nombre": "Participación en Programas de Apoyo Gubernamental", "descripcion": "Vinculación activa a la red comunitaria o programas estatales, factor protector robusto.", "peso": -2},
    {"nombre": "Acceso a Servicios de Cuidado a Largo Plazo", "descripcion": "Confirma si ya recibe cuidados formales o reside en un hogar, mitigando la urgencia de dependencia.", "peso": -1},
    {"nombre": "Número de Causas Judiciales en Curso", "descripcion": "Cuantifica la carga judicial activa. Un alto número sugiere conflicto crónico no resuelto.", "peso": 1},
    {"nombre": "Acciones Legales Previas", "descripcion": "Historial de denuncias o medidas anteriores. La reincidencia indica un entorno persistentemente hostil.", "peso": 1},
    {"nombre": "Antecedentes VIF", "descripcion": "Registros históricos de violencia intrafamiliar. Predictor estadístico fuerte de riesgo vital.", "peso": 1},
    {"nombre": "Enfermedades Terminales", "descripcion": "Diagnósticos de mal pronóstico vital o condición paliativa. Prioriza medidas humanitarias.", "peso": 1},
    {"nombre": "Lesiones / Enf. Crónicas", "descripcion": "Patologías de larga data o lesiones físicas recientes que aumentan la fragilidad física.", "peso": 1}
]

# Extraer listas y diccionarios para compatibilidad con el resto del sistema
NOMBRES_VARIABLES = [var["nombre"] for var in DEFINICION_VARIABLES]
PESOS_VARIABLES = {var["nombre"]: var["peso"] for var in DEFINICION_VARIABLES}

# === UMBRALES PARA NIVELES DE RIESGO ===
# Se usan para asignar "Bajo", "Medio", "Alto" basados en el puntaje ponderado.
# Puntaje <= 5: Bajo (0)
# Puntaje > 5 y <= 10: Medio (1)
# Puntaje > 10: Alto (2)
UMBRALES_RIESGO = [-float('inf'), 6, 10, float('inf')]

# === PATRONES DE BÚSQUEDA (REGEX) PARA VARIABLES DE RIESGO ===
PATRONES_VARIABLES = {
    "Edad": [
        r"(?i)(\d{1,3})\s*años\s*(?:de\s*edad)?", r"(?i)edad\s*de\s*(\d{1,3})",
        r"(?i)nacido\s*(?:el|en)\s*\d{1,2}\s*de\s*\w+\s*de\s*(\d{4})",
        r"(?i)mayor\s*de\s*edad", r"(?i)adulto\s*mayor"
    ],
    "Condición Cognitiva": [
        r"(?i)lucidez", r"(?i)orientad[oa]\s*temporo-espacial", r"(?i)confusi[oó]n\s*aguda",
        r"(?i)desorientad[oa]", r"(?i)estado\s*de\s*conciencia", r"(?i)vigilia"
    ],
    "Nivel Educativo": [
        r"(?i)nivel\s*educativo", r"(?i)educaci[oó]n\s*(?:b[áa]sica|media|superior|general)",
        r"(?i)analfabeto", r"(?i)analfabetismo", r"(?i)lee\s*y\s*escribe", r"(?i)escolaridad"
    ],
    "Deterioro Cognitivo o Enfermedades Mentales": [
        r"(?i)deterioro\s*cognitivo", r"(?i)enfermedades\s*mentales", r"(?i)demencia",
        r"(?i)alzheimer", r"(?i)depresión", r"(?i)ansiedad", r"(?i)trastorno\s*mental",
        r"(?i)psiqui[áa]trico", r"(?i)psicol[óo]gico", r"(?i)tratamiento\s*(?:psiqui[áa]trico|psicol[óo]gico)",
        r"(?i)sintomatología\s*ansioso\s*depresiva"
    ],
    "Dependencia de Otros": [
        r"(?i)dependencia\s*económica", r"(?i)dependencia\s*(?:f[íi]sica|de\s*terceros)",
        r"(?i)cuidador", r"(?i)asistencia\s*(?:permanente|de\s*terceros)",
        r"(?i)no\s*puede\s*valerse\s*por\s*sí\s*mismo"
    ],
    "Conflictos Familiares": [
        r"(?i)conflictos\s*familiares", r"(?i)disputa\s*familiar", r"(?i)problemas\s*familiares",
        r"(?i)desavenencias\s*(?:familiares|entre\s*las\s*partes)", r"(?i)violencia\s*intrafamiliar"
    ],
    "Relación con Cuidadores": [
        r"(?i)relaci[oó]n\s*con\s*cuidadores", r"(?i)confianza\s*en\s*cuidadores",
        r"(?i)sobrecarga\s*del\s*cuidador", r"(?i)síndrome\s*del\s*cuidador",
        r"(?i)negligencia\s*del\s*cuidador", r"(?i)abandono\s*del\s*cuidador",
        r"(?i)cuidador\s*principal"
    ],
    "Aislamiento Social": [
        r"(?i)aislamiento\s*social", r"(?i)sin\s*apoyo\s*social", r"(?i)soledad"
    ],
    "Acceso a Asesoría Legal": [
        r"(?i)acceso\s*a\s*asesor[íi]a\s*legal", r"(?i)asesor[íi]a\s*jur[íi]dica",
        r"(?i)abogado", r"(?i)defensor", r"(?i)corporaci[oó]n\s*de\s*asistencia\s*judicial"
    ],
    "Acceso a la Protección Judicial": [
        r"(?i)acceso\s*a\s*la\s*protección\s*judicial", r"(?i)medidas\s*judiciales",
        r"(?i)protección\s*judicial", r"(?i)leyes\s*sobre\s*violencia\s*intrafamiliar"
    ],
    "Interdicción Judicial": [
        r"(?i)interdicci[óo]n\s*(?:judicial)?", r"(?i)interdicto",
        r"(?i)no\s*puede\s*administrar\s*bienes"
    ],
    "Historial Patrimonial": [
        r"(?i)historial\s*patrimonial", r"(?i)bienes\s*y\s*propiedades", r"(?i)patrimonio",
        r"(?i)transferencias\s*sospechosas"
    ],
    "Grado de Vulnerabilidad Económica": [
        r"(?i)vulnerabilidad\s*econ[óo]mica", r"(?i)dependencia\s*econ[óo]mica",
        r"(?i)pensi[óo]n", r"(?i)apoyo\s*econ[óo]mico\s*de\s*familiares"
    ],
    "Disputas Hereditarias": [
        r"(?i)disputas\s*hereditarias", r"(?i)conflictos\s*por\s*herencias",
        r"(?i)disputas\s*patrimoniales", r"(?i)sucesi[óo]n"
    ],
    "Acción de los Cuidadores": [
        r"(?i)acci[óo]n\s*de\s*los\s*cuidadores", r"(?i)rol\s*de\s*cuidadores",
        r"(?i)administración\s*de\s*bienes\s*por\s*cuidadores"
    ],
    "Condiciones de Vivienda": [
        r"(?i)condiciones\s*de\s*vivienda", r"(?i)seguridad\s*en\s*la\s*vivienda",
        r"(?i)restricci[óo]n\s*de\s*acceso\s*a\s*vivienda", r"(?i)abandono\s*del\s*inmueble"
    ],
    "Participación en Programas de Apoyo Gubernamental": [
        r"(?i)programas\s*de\s*apoyo\s*gubernamental", r"(?i)apoyo\s*estatal",
        r"(?i)programas\s*para\s*adultos\s*mayores"
    ],
    "Acceso a Servicios de Cuidado a Largo Plazo": [
        r"(?i)servicios\s*de\s*cuidado\s*a\s*largo\s*plazo", r"(?i)cuidados\s*residenciales",
        r"(?i)asistencia\s*domiciliaria"
    ],
    "Número de Causas Judiciales en Curso": [
        r"(?i)causas\s*activas", r"(?i)procesos\s*judiciales\s*en\s*curso",
        r"RIT\s*[A-Z]?\s*-\s*\d+", r"causa\s*RIT"
    ],
    "Acciones Legales Previas": [
        r"(?i)acciones\s*legales\s*previas", r"(?i)historial\s*de\s*acciones\s*legales",
        r"(?i)procesos\s*previos\s*(?:relacionados\s*con\s*abuso)?", r"(?i)juicios\s*anteriores"
    ],
    "Antecedentes VIF": [
        r"(?i)antecedentes\s*de\s*VIF", r"(?i)violencia\s*intrafamiliar\s*previa",
        r"(?i)denuncias\s*anteriores\s*por\s*violencia", r"(?i)historial\s*de\s*maltrato"
    ],
    "Enfermedades Terminales": [
        r"(?i)enfermedad\s*terminal", r"(?i)c[áa]ncer\s*terminal",
        r"(?i)cuidados\s*paliativos", r"(?i)desahucio\s*m[ée]dico", r"(?i)pron[óo]stico\s*reservado"
    ],
    "Lesiones / Enf. Crónicas": [
        r"(?i)enfermedad\s*cr[óo]nica", r"(?i)diabetes", r"(?i)hipertensi[óo]n",
        r"(?i)lesiones\s*f[íi]sicas", r"(?i)movilidad\s*reducida", r"(?i)artrosis"
    ]
}

# === PATRONES DE BÚSQUEDA (REGEX) PARA METADATOS DE LA CAUSA ===
PATRONES_METADATOS = {
    "rit": [
        r"(?i)RIT\s*N°?\s*[:\-]?\s*([A-Z]?[\s\-]*[\d.]+[\s\-][\d.]{4,5})",
        r"([A-Z]\s*-\s*\d{1,6}\s*-\s*\d{4})",
        r"([A-Z]\s+\d{1,6}\s+\d{4})",
        r"(?i)RIT\s+[A-Z]\s*-\s*\d{1,6}\s*-\s*\d{4}",
        r"(?i)RIT\s+[A-Z]\s+\d{1,6}\s+\d{4}",
        r"(?i)RIT\s*N°?\s*[:\-]?\s*([A-Z]?[\s\-]*\d[\d\.\-]+\d)"
    ],
    "tribunal": [
        r"(?i)(Juzgado\s+de\s+Familia\s+de\s+[A-ZÁÉÍÓÚÑ\s]+)",
        r"(?i)(Tribunal\s+de\s+Familia\s+de\s+[A-ZÁÉÍÓÚÑ\s]+)"
    ],
    "comuna": [
        # 1. Buscar en el nombre del tribunal (ej. Juzgado de Familia de Maipú)
        # Modificado para no capturar saltos de línea (\s incluye \n, cambiamos a [ \t])
        r"(?i)(?:Juzgado|Tribunal)\s+de\s+(?:Letras|Familia|Garantía)\s+de\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\.]+(?:[ \t]+[A-ZÁÉÍÓÚÑa-záéíóúñ\.]+)*)",
        # 2. Buscar coincidencias directas con la lista de comunas conocidas (más robusto)
        r"(?i)\b(" + "|".join([re.escape(c) for c in LISTA_COMUNAS]) + r")\b"
    ],
    "materia": r"(?i)MATERIA\s*[:\-]?\s*([A-ZÁÉÍÓÚÑ\s]+)",
    "fecha": r"(?:Santiago|Valparaíso|Concepción|Rancagua).*?,\s*(\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚñ]+\s+\d{4})",
    "estado": r"(SENTENCIA|EN TRAMITACIÓN|ARCHIVADA)"
}

# === PATRONES DE BÚSQUEDA (REGEX) PARA IDENTIFICAR PARTES ===
PATRONES_ROLES = {
    # Patrón para roles de demandante/víctima
    'demandante': r"(?i)\b(?:demandante|actora|denunciante|requirente|solicitante|reclamante)\b\s*[:,\s]+(?:don|doña|d\.|sr\.?|sra\.?|señor|señora)?\s*([A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ\s',.-]+?)(?:\s*,|\s+con\s+cédula|\s+RUT|\s+y\s+otro|\n)",

    # Patrón para roles de demandado
    'demandado': r"(?i)\b(?:demandado|denunciado|requerido|imputado|reclamado)\b\s*[:,\s]+(?:don|doña|d\.|sr\.?|sra\.?|señor|señora)?\s*([A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ\s',.-]+?)(?:\s*,|\s+con\s+cédula|\s+RUT|\s+y\s+otro|\n)",

    # Patrón específico para el rol de víctima, que es el más importante
    'victima': r"(?i)\b(?:víctima|afectado|ofendido|causante|adulto\s+mayor)\b\s*[:,\s]+(?:don|doña|d\.|sr\.?|sra\.?|señor|señora)?\s*([A-ZÁÉÍÓÚÑ][a-zA-ZáéíóúñÁÉÍÓÚÑ\s',.-]+?)(?:\s*,|\s+con\s+cédula|\s+RUT|\s+y\s+otro|\n)"
}
# === 4. CONFIGURACIÓN DE LA APLICACIÓN (GUI) ===
# (Se añadirán más configuraciones a medida que se construya la interfaz)

APP_TITLE = "Sistema de Priorización de Riesgo Patrimonial v2.0"