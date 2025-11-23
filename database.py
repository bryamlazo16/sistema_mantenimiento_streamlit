from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sqlite3

# Configuración de la base de datos
Base = declarative_base()

class Equipo(Base):
    __tablename__ = 'equipos'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    ubicacion = Column(String(100))
    estado = Column(String(20), default='Operativo')
    fecha_instalacion = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'ubicacion': self.ubicacion,
            'estado': self.estado,
            'fecha_instalacion': self.fecha_instalacion.isoformat() if self.fecha_instalacion else None
        }

class OrdenTrabajo(Base):
    __tablename__ = 'ordenes_trabajo'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text, nullable=False)
    tipo = Column(String(20), nullable=False)
    prioridad = Column(String(20), nullable=False)
    estado = Column(String(20), default='Pendiente')
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_inicio_plan = Column(DateTime)
    fecha_fin_plan = Column(DateTime)
    fecha_inicio_real = Column(DateTime)
    fecha_fin_real = Column(DateTime)
    tecnico_asignado = Column(String(100))
    horas_estimadas = Column(Float)
    horas_reales = Column(Float)
    costo_estimado = Column(Float)
    costo_real = Column(Float)
    observaciones = Column(Text)
    
    equipo_id = Column(Integer, ForeignKey('equipos.id'))
    aviso_id = Column(Integer, ForeignKey('avisos_averias.id'))
    
    equipo = relationship("Equipo", backref="ordenes_trabajo")
    aviso = relationship("AvisoAveria", backref="ordenes_trabajo")
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'tipo': self.tipo,
            'prioridad': self.prioridad,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_inicio_plan': self.fecha_inicio_plan.isoformat() if self.fecha_inicio_plan else None,
            'fecha_fin_plan': self.fecha_fin_plan.isoformat() if self.fecha_fin_plan else None,
            'tecnico_asignado': self.tecnico_asignado,
            'equipo_nombre': self.equipo.nombre if self.equipo else None
        }

class AvisoAveria(Base):
    __tablename__ = 'avisos_averias'
    
    id = Column(Integer, primary_key=True)
    codigo = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text, nullable=False)
    fecha_reporte = Column(DateTime, default=datetime.utcnow)
    reportado_por = Column(String(100), nullable=False)
    prioridad = Column(String(20), nullable=False)
    estado = Column(String(20), default='Reportado')
    fecha_cierre = Column(DateTime)
    observaciones = Column(Text)
    
    equipo_id = Column(Integer, ForeignKey('equipos.id'))
    equipo = relationship("Equipo", backref="avisos")
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'descripcion': self.descripcion,
            'fecha_reporte': self.fecha_reporte.isoformat(),
            'reportado_por': self.reportado_por,
            'prioridad': self.prioridad,
            'estado': self.estado,
            'equipo_nombre': self.equipo.nombre if self.equipo else None
        }

# Configuración de la base de datos
engine = create_engine('sqlite:///mantenimiento.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def inicializar_datos():
    """Inicializar datos de ejemplo"""
    session = get_session()
    
    # Verificar si ya existen datos
    if session.query(Equipo).count() == 0:
        # Crear equipos de ejemplo
        equipos = [
            Equipo(
                codigo=f"EQ-{i:05d}",
                nombre=nombre,
                descripcion=descripcion,
                ubicacion=ubicacion,
                estado=estado
            ) for i, (nombre, descripcion, ubicacion, estado) in enumerate([
                ("Compresor Principal A-125", "Compresor de aire de 100HP", "Sala de Máquinas 1", "Operativo"),
                ("Motor B-42", "Motor eléctrico 50HP", "Línea de Producción 2", "Operativo"),
                ("Transportador C-8", "Banda transportadora 20m", "Área de Empaque", "En Mantenimiento"),
                ("Bomba Hidráulica D-15", "Bomba de aceite 25HP", "Sala de Máquinas 2", "Operativo"),
                ("Ventilador E-22", "Ventilador industrial", "Área de Proceso", "Parado")
            ], 1)
        ]
        
        session.add_all(equipos)
        session.commit()
        
        # Crear órdenes de trabajo de ejemplo
        ordenes = [
            OrdenTrabajo(
                codigo=f"OT-{i:05d}",
                descripcion=descripcion,
                tipo=tipo,
                prioridad=prioridad,
                estado=estado,
                equipo_id=equipo_id,
                tecnico_asignado=tecnico,
                fecha_inicio_plan=datetime.now(),
                fecha_fin_plan=datetime.now()
            ) for i, (descripcion, tipo, prioridad, estado, equipo_id, tecnico) in enumerate([
                ("Revisión mensual compresor principal", "Preventivo", "Media", "En Progreso", 1, "Juan Pérez"),
                ("Cambio de rodamientos motor B", "Correctivo", "Alta", "Pendiente", 2, "María García"),
                ("Lubricación cadena transportadora", "Preventivo", "Baja", "Completada", 3, "Carlos López"),
                ("Reparación fuga de aceite", "Correctivo", "Alta", "Pendiente", 4, "Ana Martínez")
            ], 1)
        ]
        
        session.add_all(ordenes)
        
        # Crear avisos de ejemplo
        avisos = [
            AvisoAveria(
                codigo=f"AV-{i:05d}",
                descripcion=descripcion,
                reportado_por=reportado_por,
                prioridad=prioridad,
                estado=estado,
                equipo_id=equipo_id
            ) for i, (descripcion, reportado_por, prioridad, estado, equipo_id) in enumerate([
                ("Fuga de aceite en válvula principal", "Operario 1", "Alta", "Reportado", 1),
                ("Fallo en arranque motor auxiliar", "Supervisor", "Crítica", "En Análisis", 2),
                ("Ruido anormal en transportador", "Técnico", "Media", "Resuelto", 3)
            ], 1)
        ]
        
        session.add_all(avisos)
        session.commit()
    
    session.close()