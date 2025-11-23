import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import get_session, inicializar_datos, OrdenTrabajo, AvisoAveria, Equipo
from sqlalchemy import func

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
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<h1 class="main-header">🔧 Sistema de Gestión de Mantenimiento</h1>', unsafe_allow_html=True)

# Obtener datos
session = get_session()

# Métricas principales
st.subheader("📊 Métricas Principales")
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
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Órdenes por Estado")
    session = get_session()
    estado_data = session.query(
        OrdenTrabajo.estado, 
        func.count(OrdenTrabajo.id).label('cantidad')
    ).group_by(OrdenTrabajo.estado).all()
    session.close()
    
    if estado_data:
        df_estado = pd.DataFrame(estado_data, columns=['Estado', 'Cantidad'])
        fig = px.pie(df_estado, values='Cantidad', names='Estado', 
                     color_discrete_sequence=px.colors.qualitative.Set3)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay órdenes de trabajo registradas")

with col2:
    st.subheader("📊 Órdenes por Prioridad")
    session = get_session()
    prioridad_data = session.query(
        OrdenTrabajo.prioridad, 
        func.count(OrdenTrabajo.id).label('cantidad')
    ).group_by(OrdenTrabajo.prioridad).all()
    session.close()
    
    if prioridad_data:
        df_prioridad = pd.DataFrame(prioridad_data, columns=['Prioridad', 'Cantidad'])
        fig = px.bar(df_prioridad, x='Prioridad', y='Cantidad',
                     color='Prioridad', 
                     color_discrete_map={
                         'Baja': '#00cc96',
                         'Media': '#ffa15a', 
                         'Alta': '#ef553b',
                         'Crítica': '#d62728'
                     })
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay órdenes de trabajo registradas")

# Órdenes recientes
st.markdown("---")
st.subheader("🔄 Órdenes de Trabajo Recientes")
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
    st.dataframe(df_ordenes, use_container_width=True, hide_index=True)
else:
    st.info("No hay órdenes de trabajo recientes")

# Avisos críticos
st.markdown("---")
st.subheader("🚨 Avisos de Averías Críticos")
session = get_session()
avisos_criticos = session.query(AvisoAveria).filter(
    AvisoAveria.prioridad.in_(['Alta', 'Crítica'])
).order_by(AvisoAveria.fecha_reporte.desc()).limit(5).all()
session.close()

if avisos_criticos:
    for aviso in avisos_criticos:
        with st.expander(f"⚠️ {aviso.codigo} - {aviso.descripcion[:50]}...", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Equipo:** {aviso.equipo.nombre if aviso.equipo else 'N/A'}")
                st.write(f"**Reportado por:** {aviso.reportado_por}")
            with col2:
                st.write(f"**Prioridad:** {aviso.prioridad}")
                st.write(f"**Estado:** {aviso.estado}")
            with col3:
                st.write(f"**Fecha:** {aviso.fecha_reporte.strftime('%d/%m/%Y %H:%M')}")
            
            if aviso.observaciones:
                st.info(f"**Observaciones:** {aviso.observaciones}")
else:
    st.info("No hay avisos críticos")

# Quick actions en sidebar
st.sidebar.title("⚡ Acciones Rápidas")
if st.sidebar.button("🆕 Nueva Orden de Trabajo", use_container_width=True):
    st.switch_page("pages/1_Órdenes_de_Trabajo.py")

if st.sidebar.button("⚠️ Nuevo Aviso de Avería", use_container_width=True):
    st.switch_page("pages/2_Avisos_de_Averías.py")

if st.sidebar.button("🔄 Actualizar Datos", use_container_width=True):
    st.rerun()

# Información del sistema en sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Información del Sistema")
st.sidebar.write(f"**Última actualización:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")

session = get_session()
total_equipos = session.query(Equipo).count()
session.close()
st.sidebar.write(f"**Total equipos:** {total_equipos}")

st.sidebar.markdown("---")
st.sidebar.info("""
**Sistema de Gestión de Mantenimiento**
                
Desarrollado con Streamlit
🔧 Versión 1.0
""")