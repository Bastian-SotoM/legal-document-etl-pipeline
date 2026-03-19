from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text, DateTime, Table
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

# Base declarativa para todos los modelos
Base = declarative_base()

# --- TABLAS DE ASOCIACIÓN Y AUDITORÍA ---

# Tabla intermedia para la relación N-N entre EvaluacionRiesgo y VariableRiesgo
evaluacion_variable = Table(
    'evaluacion_variable',
    Base.metadata,
    Column('evaluacion_id', Integer, ForeignKey('evaluacion_riesgo.id', ondelete='CASCADE')),
    Column('variable_id', Integer, ForeignKey('variable_riesgo.id', ondelete='CASCADE'))
)

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    rut = Column(String, unique=True, nullable=False)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String, nullable=False, default='Analista') # 'Analista', 'Administrador'
    estado = Column(String, nullable=False, default='Activo') # 'Activo', 'Inactivo'

class AuditoriaAccion(Base):
    __tablename__ = 'auditoria_acciones'
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    accion = Column(String, nullable=False) # Ej: 'INICIO_SESION', 'FINALIZAR_CAUSA', 'MODIFICAR_VARIABLE'
    detalles = Column(Text) # Ej: "RIT: C-123-2024", "Variable: Edad", "Usuario: Juan Perez"
    fecha_accion = Column(DateTime, default=datetime.now)
    usuario = relationship('Usuario')

class LogSistema(Base):
    __tablename__ = 'log_sistema'
    id = Column(Integer, primary_key=True)
    tipo_evento = Column(String, nullable=False) # 'Error', 'Solución', 'Mantenimiento'
    descripcion = Column(Text, nullable=False)
    fecha_evento = Column(DateTime, default=datetime.now)
    estado_log = Column(String, default='Abierto') # 'Abierto', 'Cerrado'
    fecha_solucion = Column(DateTime)
    usuario_responsable_id = Column(Integer, ForeignKey('usuarios.id'))
    usuario_responsable = relationship('Usuario')

# --- ENTIDADES PRINCIPALES ---

class AdultoMayor(Base):
    __tablename__ = 'adulto_mayor'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150))
    causas = relationship('CausaJudicial', back_populates='adulto_mayor')

class CausaJudicial(Base):
    __tablename__ = 'causa_judicial'
    id = Column(Integer, primary_key=True)
    RIT = Column(String(50))
    tribunal = Column(String(150))
    comuna = Column(String(100)) # NUEVO: Para almacenar la comuna detectada
    materia = Column(String(100))
    fecha_ingreso = Column(Date) # Fecha del documento
    estado_procesal = Column(String(100))
    descripcion = Column(Text)
    # Nuevos campos para la V2
    fecha_carga = Column(DateTime, default=datetime.now)
    fecha_finalizacion = Column(DateTime, nullable=True)
    estado_causa = Column(String, default='En Proceso') # 'En Proceso', 'Finalizada'
    ruta_archivo_interno = Column(String) # Ruta al PDF en data/causas_archivadas/
    adulto_id = Column(Integer, ForeignKey('adulto_mayor.id'))
    usuario_carga_id = Column(Integer, ForeignKey('usuarios.id'))
    adulto_mayor = relationship('AdultoMayor', back_populates='causas')
    documentos = relationship('DocumentoPDF', back_populates='causa', cascade='all, delete')
    evaluaciones = relationship('EvaluacionRiesgo', back_populates='causa', cascade='all, delete')

class DocumentoPDF(Base):
    __tablename__ = 'documento_pdf'
    id = Column(Integer, primary_key=True)
    nombre_archivo = Column(String(255), unique=True)
    texto_extraido = Column(Text)
    fecha_procesamiento = Column(DateTime, default=datetime.now)
    causa_id = Column(Integer, ForeignKey('causa_judicial.id'))
    causa = relationship('CausaJudicial', back_populates='documentos')

class VariableRiesgo(Base):
    __tablename__ = 'variable_riesgo'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150))
    descripcion = Column(Text)
    peso_relativo = Column(Float)
    patrones = Column(Text) # JSON o texto separado por saltos de línea
    tipo = Column(String, default='Agravante') # 'Agravante', 'Mitigante'
    estado = Column(String, default='Activa') # 'Activa', 'Inactiva'
    evaluaciones = relationship('EvaluacionRiesgo', secondary=evaluacion_variable, back_populates='variables')

class EvaluacionRiesgo(Base):
    __tablename__ = 'evaluacion_riesgo'
    id = Column(Integer, primary_key=True)
    nivel_riesgo = Column(String(20))  # bajo, medio, alto
    fecha_evaluacion = Column(DateTime, default=datetime.now)
    observaciones = Column(Text)
    causa_id = Column(Integer, ForeignKey('causa_judicial.id'))
    causa = relationship('CausaJudicial', back_populates='evaluaciones')
    variables = relationship('VariableRiesgo', secondary=evaluacion_variable, back_populates='evaluaciones')

class ProgramaSocial(Base):
    __tablename__ = 'programa_social'
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    variables_clave = Column(Text) # Almacenado como JSON (lista de strings)
    variables_contexto = Column(Text) # Almacenado como JSON (lista de strings)
    territorio = Column(Text) # NUEVO: "Nacional", "Regional" o lista de comunas
    descripcion = Column(Text)