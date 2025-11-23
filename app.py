import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import get_session, inicializar_datos, OrdenTrabajo, AvisoAveria, Equipo

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión de Mantenimiento",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar datos
inicializar_datos()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🔧 Sistema de Gestión de Mantenimiento</h1>', unsafe_allow_html=True)

# Obtener datos
session = get_session()

# Métricas principales
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_ordenes = session.query(OrdenTrabajo).count()
    st.metric("Total Órdenes", total_ordenes)

with col2:
    ordenes_pendientes = session.query(OrdenTrabajo).filter_by(estado='Pendiente').count()
    st.metric("Órdenes Pendientes", ordenes_pendientes)

with col3:
    ordenes_progreso = session.query(OrdenTrabajo).filter_by(estado='En Progreso').count()
    st.metric("En Progreso", ordenes_progreso)

with col4:
    avisos_activos = session.query(AvisoAveria).filter(AvisoAveria.estado.in_(['Reportado', 'En Análisis'])).count()
    st.metric("Avisos Activos", avisos_activos)

session.close()

# Gráficos y tablas
col1, col2 = st.columns(2)

with col1:
    st.subheader("Órdenes por Estado")
    session = get_session()
    estado_counts = pd.DataFrame(session.query(OrdenTrabajo.estado, 
                                             db.func.count(OrdenTrabajo.id)).group_by(OrdenTrabajo.estado).all(),
                               columns=['Estado', 'Cantidad'])
    session.close()
    
    if not estado_counts.empty:
        fig = px.pie(estado_counts, values='Cantidad', names='Estado', 
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay órdenes de trabajo registradas")

with col2:
    st.subheader("Órdenes por Prioridad")
    session = get_session()
    prioridad_counts = pd.DataFrame(session.query(OrdenTrabajo.prioridad, 
                                                db.func.count(OrdenTrabajo.id)).group_by(OrdenTrabajo.prioridad).all(),
                                  columns=['Prioridad', 'Cantidad'])
    session.close()
    
    if not prioridad_counts.empty:
        fig = px.bar(prioridad_counts, x='Prioridad', y='Cantidad',
                     color='Prioridad', color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay órdenes de trabajo registradas")

# Órdenes recientes
st.subheader("Órdenes de Trabajo Recientes")
session = get_session()
ordenes_recientes = session.query(OrdenTrabajo).order_by(OrdenTrabajo.fecha_creacion.desc()).limit(10).all()
session.close()

if ordenes_recientes:
    datos_ordenes = []
    for orden in ordenes_recientes:
        datos_ordenes.append({
            'Código': orden.codigo,
            'Descripción': orden.descripcion,
            'Equipo': orden.equipo.nombre if orden.equipo else 'N/A',
            'Prioridad': orden.prioridad,
            'Estado': orden.estado,
            'Técnico': orden.tecnico_asignado or 'No asignado',
            'Fecha Creación': orden.fecha_creacion.strftime('%d/%m/%Y %H:%M')
        })
    
    df_ordenes = pd.DataFrame(datos_ordenes)
    st.dataframe(df_ordenes, use_container_width=True)
else:
    st.info("No hay órdenes de trabajo recientes")

# Avisos críticos
st.subheader("Avisos de Averías Críticos")
session = get_session()
avisos_criticos = session.query(AvisoAveria).filter(
    AvisoAveria.prioridad.in_(['Alta', 'Crítica'])
).order_by(AvisoAveria.fecha_reporte.desc()).limit(5).all()
session.close()

if avisos_criticos:
    for aviso in avisos_criticos:
        with st.expander(f"🚨 {aviso.codigo} - {aviso.descripcion[:50]}..."):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Equipo:** {aviso.equipo.nombre if aviso.equipo else 'N/A'}")
                st.write(f"**Reportado por:** {aviso.reportado_por}")
            with col2:
                st.write(f"**Prioridad:** {aviso.prioridad}")
                st.write(f"**Estado:** {aviso.estado}")
            with col3:
                st.write(f"**Fecha:** {aviso.fecha_reporte.strftime('%d/%m/%Y %H:%M')}")
else:
    st.info("No hay avisos críticos")

# Quick actions en sidebar
st.sidebar.title("Acciones Rápidas")
if st.sidebar.button("🆕 Nueva Orden de Trabajo"):
    st.switch_page("pages/1_Órdenes_de_Trabajo.py")

if st.sidebar.button("⚠️ Nuevo Aviso de Avería"):
    st.switch_page("pages/2_Avisos_de_Averías.py")

if st.sidebar.button("🔄 Actualizar Datos"):
    st.rerun()

# Información del sistema en sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("Información del Sistema")
st.sidebar.write(f"**Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.sidebar.write(f"**Total equipos:** {session.query(Equipo).count()}")