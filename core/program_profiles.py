# -*- coding: utf-8 -*-
"""
Perfiles de Programas Sociales para el Motor de Coincidencia

Este archivo centraliza la definición de los perfiles de los programas
de derivación, especificando sus variables clave y de contexto.
"""

# - variables_clave: Tienen un peso mayor (+2) y son críticas para la sugerencia.
# - variables_contexto: Tienen un peso menor (+1) y refinan la sugerencia.

PERFILES_PROGRAMAS = {
    "Derivar a ELEAM": {
        "variables_clave": ["Dependencia de Otros", "Aislamiento Social"],
        "variables_contexto": ["Grado de Vulnerabilidad Económica", "Relación con Cuidadores", "Condiciones de Vivienda"],
        "territorio": "Arica, Antofagasta, Copiapó, La Serena, Valparaíso, Huechuraba, Puente Alto, Lo Prado, Rengo, Curicó, Cauquenes, Licantén, Concepción, Los Ángeles, Melipeuco, Cunco, Loncoche, Valdivia, Puerto Montt, Coyhaique, Punta Arenas, Natales, Puerto Natales"
    },
    "Derivar a CEDIAM": {
        "variables_clave": ["Dependencia de Otros"],
        "variables_contexto": ["Relación con Cuidadores", "Condición Cognitiva", "Aislamiento Social"],
        "territorio": "Pica, Pozo Almonte, Huara, Iquique, Calama, Taltal, Tocopilla, Freirina, Caldera, Huasco, Chañaral, Alto del Carmen, Vicuña, Los Vilos, La Higuera, Illapel, Combarbalá, Andacollo, Monte Patria, Ovalle, Coquimbo, Paihuano, La Serena, Canela, Viña del Mar, Algarrobo, Catemu, Quilpué, La Calera, El Tabo, El Quisco, San Felipe, Juan Fernández, Valparaíso, Putaendo, Cartagena, Quintero, Calle Larga, Villa Alemana, La Cruz, Mostazal, Marchigüe, Rancagua, Peumo, Graneros, Quinta de Tilcoco, Olivar, Requínoa, Navidad, Coltauco, San Fernando, Peralillo, Romeral, Longaví, San Javier, Constitución, Chanco, Molina, Pencahue, Hualañé, San Clemente, Linares, Cauquenes, Empedrado, Río Claro, Yerbas Buenas, Curicó, Chiguayante, Santa Juana, Cañete, Tomé, Laja, Tirúa, Penco, Tucapel, Quilleco, Nacimiento, Talcahuano, Concepción, Contulmo, Hualqui, Los Ángeles, Curanilahue, Negrete, Lonquimay, Galvarino, Nueva Imperial, Melipeuco, Traiguén, Collipulli, Freire, Curarrehue, Curacautín, Perquenco, Victoria, Padre Las Casas, Vilcún, Lumaco, Loncoche, Saavedra, Los Sauces, Pucón, Villarrica, Ercilla, Gorbea, Futaleufú, Maullín, Calbuco, Castro, Queilén, Palena, Curaco de Vélez, Frutillar, Hualaihué, Los Muermos, Osorno, Quellón, Quinchao, Puqueldón, Puerto Octay, Chaitén, Chonchi, Puerto Varas, Río Ibáñez, Aysén, Coyhaique, Natales, Porvenir, Pirque, Lampa, Maipú, Peñalolén, Lo Espejo, Buin, Independencia, María Pinto, Puente Alto, San Joaquín, San Miguel, Padre Hurtado, Talagante, Cerro Navia, La Granja, Huechuraba, Recoleta, Renca, Melipilla, La Pintana, Santiago, Pudahuel, Ñuñoa, San Bernardo, Estación Central, La Reina, Los Lagos, Paillaco, Lanco, Panguipulli, La Unión, Mafil, Futrono, Arica, Quillón, Coelemu, Quirihue, San Fabián, San Ignacio, Trehuaco, San Carlos, San Nicolás, Ránquil, Yungay, Cobquecura, Ñiquén, Portezuelo, Chillán Viejo, Pinto, Antofagasta, Talca, Punta Arenas, Chillán, Temuco"
    },
    "Derivar a SNAC": {
        "variables_clave": ["Dependencia de Otros", "Relación con Cuidadores"],
        "variables_contexto": ["Grado de Vulnerabilidad Económica", "Condiciones de Vivienda"],
        "territorio": "Putre, Arica, Alto Hospicio, Calama, María Elena, Copiapó, Los Vilos, Paihuano, Salamanca, Papudo, Villa Alemana, Casablanca, La Calera, Rancagua, Doñihue, Santa Cruz, Placilla, Machalí, Villa Alegre, San Clemente, Talca, Linares, Pelarco, Talcahuano, Alto Biobío, Cañete, San Rosendo, Arauco, Angol, Loncoche, Toltén, Lonquimay, Collipulli, Paillaco, Valdivia, Quemchi, Palena, Purranque, Los Muermos, Chaitén, Coyhaique, Guaitecas, Río Ibáñez, Cabo de Hornos, Natales, Peñalolén, Talagante, Quinta Normal, Santiago, Pirque, Til Til, Independencia, Padre Hurtado, Pedro Aguirre Cerda, María Pinto, Recoleta, Estación Central, Quirihue, Chillán, San Carlos, Alto del Carmen, Taltal, Sierra Gorda, Chañaral, Lago Verde, Contulmo, Hualqui, Monte Patria, Los Sauces, Lumaco, Ercilla, Melipeuco, Purén, Curaco de Vélez, Calbuco, Mafil, Futrono, Punta Arenas, Pencahue, Empedrado, San Pedro, Ninhue, Portezuelo, Coinco, Mostazal, Catemu, Putaendo, Quintero, Olmué, Camarones, Iquique, Colchane, Antofagasta, Tocopilla, Caldera, Vallenar, Coquimbo, Combarbalá, Limache, Los Andes, San Felipe, San Antonio, Valparaíso, Viña del Mar, Cerrillos, Cerro Navia, Curacaví, La Florida, La Granja, La Pintana, Lo Espejo, Lo Prado, Maipú, Melipilla, Puente Alto, Renca, San Bernardo, San Ramón, San Fernando, San Vicente, Hualañé, Molina, Curicó, Hualpén, Lota, Los Ángeles, El Carmen, Ránquil, Perquenco, Temuco, Los Lagos, La Unión, Quinchao, Osorno, Puerto Montt, Quellón, Cochrane, Tortel, Porvenir, Torres del Paine, Padre Las Casas, Saavedra, Teodoro Schmidt, Nueva Imperial, Aysén, Chanco, Pelluhue, Curanilahue, Illapel, San Gregorio, Ovalle, Huara, Pudahuel, San José de Maipo, Rengo, Buin, Pozo Almonte, Cobquecura, Coelemu, Coihueco, Yungay, Tierra Amarilla, Huasco, Panguipulli, Río Bueno, Colina, Cauquenes, Constitución, Parral, Río Claro, San Javier, Teno"
    },
    "Programa de Atención Domiciliaria para Personas con Dependencia Severa y Cuidadores": {
        "variables_clave": ["Dependencia de Otros"],
        "variables_contexto": ["Lesiones / Enf. Crónicas", "Enfermedades Terminales"],
        "territorio": "Nacional"
    },
    "Postular a Viviendas Tuteladas (CVT)": {
        "variables_clave": ["Grado de Vulnerabilidad Económica"],
        "variables_contexto": ["Condiciones de Vivienda", "Aislamiento Social"],
        "territorio": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes"
    },
    "Postular a Subsidio de Arriendo": {
        "variables_clave": ["Grado de Vulnerabilidad Económica"],
        "variables_contexto": ["Condiciones de Vivienda", "Edad", "Aislamiento Social"],
        "territorio": "Nacional"
    },
    "Sugerir Programa Vínculos": {
        "variables_clave": ["Aislamiento Social", "Grado de Vulnerabilidad Económica"],
        "variables_contexto": ["Edad", "Participación en Programas de Apoyo Gubernamental"],
        "territorio": "Nacional"
    },
    "Sugerir Vacaciones Tercera Edad": {
        "variables_clave": ["Grado de Vulnerabilidad Económica", "Aislamiento Social"],
        "variables_contexto": ["Edad", "Dependencia de Otros"], # Dependencia nula es factor
        "territorio": "Nacional"
    },
    "Sugerir Voluntariado Asesores": {
        "variables_clave": ["Nivel Educativo"],
        "variables_contexto": ["Edad", "Aislamiento Social", "Dependencia de Otros"],
        "territorio": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes"
    },
    "Activar Defensoría Mayor": {
        "variables_clave": ["Interdicción Judicial"],
        "variables_contexto": ["Historial Patrimonial", "Conflictos Familiares", "Disputas Hereditarias", "Acceso a Asesoría Legal"],
        "territorio": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes"
    },
    "Programa Buen Trato al Mayor": {
        "variables_clave": ["Antecedentes VIF", "Relación con Cuidadores"],
        "variables_contexto": ["Aislamiento Social", "Conflictos Familiares"],
        "territorio": "Arica y Parinacota, Tarapacá, Antofagasta, Atacama, Coquimbo, Valparaíso, Metropolitana, O'Higgins, Maule, Ñuble, Biobío, Araucanía, Los Ríos, Los Lagos, Aysén, Magallanes"
    },
    "Derivar a Oficina Municipal (OMAM)": {
        "variables_clave": ["Grado de Vulnerabilidad Económica"],
        "variables_contexto": ["Condiciones de Vivienda", "Participación en Programas de Apoyo Gubernamental", "Aislamiento Social"],
        "territorio": "Nacional"
    },
    "Derivar a Salud Mental (COSAM)": {
        "variables_clave": ["Deterioro Cognitivo o Enfermedades Mentales"],
        "variables_contexto": ["Conflictos Familiares", "Condición Cognitiva", "Antecedentes VIF"],
        "territorio": "Arica, Iquique, Alto Hospicio, Calama, Antofagasta, Coquimbo, Concón, Quillota, Limache, Independencia, Conchalí, Huechuraba, Recoleta, Quilicura, Colina, Lampa, Til Til, Cerro Navia, Quinta Normal, Lo Prado, Pudahuel, Talagante, Peñaflor, Melipilla, Renca, Estación Central, Maipú, Cerrillos, Santiago, La Reina, Macul, Ñuñoa, Las Condes, Peñalolén, Providencia, Lo Barnechea, Vitacura, El Bosque, Pedro Aguirre Cerda, San Bernardo, San Joaquín, Lo Espejo, San Ramón, La Granja, La Pintana, La Florida, Puente Alto, Pirque, Rancagua, Santa Cruz, Linares, Chillán, San Carlos, Coronel, Hualpén, Temuco, Padre Las Casas, Valdivia, Puerto Montt, Punta Arenas, Curanilahue, Lebu, Cañete, Arauco"
    },
    "Programa de pago a cuidadores de personas con discapacidad (estipendio)": {
        "variables_clave": ["Dependencia de Otros", "Grado de Vulnerabilidad Económica"],
        "variables_contexto": ["Relación con Cuidadores", "Lesiones / Enf. Crónicas", "Grado de Vulnerabilidad Económica"],
        "territorio": "Nacional"
    }
}