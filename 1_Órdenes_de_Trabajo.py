import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_session, OrdenTrabajo, Equipo

st.set_page_config(page_title="Órdenes de Trabajo", layout="wide")

st.title("📋 Gestión de Órdenes de Trabajo")

# Session
session = get_session()

# Formulario para nueva orden
with st.form("nueva_orden"):
    st.subheader("Crear Nueva Orden de Trabajo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        descripcion = st.text_area("Descripción del trabajo", height=100)
        equipo_id = st.selectbox(
            "Equipo",
            options=[eq.id for eq in session.query(Equipo).all()],
            format_func=lambda x: session.query(Equipo).get(x).nombre
        )
        tipo = st.selectbox("Tipo", ["Preventivo", "Correctivo", "Predictivo"])
        
    with col2:
        prioridad = st.selectbox("Prioridad", ["Baja", "Media", "Alta", "Crítica"])
        tecnico_asignado = st.text_input("Técnico Asignado")
        fecha_inicio = st.date_input("Fecha Inicio Planificada")
        fecha_fin = st.date_input("Fecha Fin Planificada")
    
    submitted = st.form_submit_button("Crear Orden")
    
    if submitted:
        if descripcion and equipo_id:
            # Generar código
            ultima_orden = session.query(OrdenTrabajo).order_by(OrdenTrabajo.id.desc()).first()
            nuevo_codigo = f"OT-{ultima_orden.id + 1:05d}" if ultima_orden else "OT-00001"
            
            nueva_orden = OrdenTrabajo(
                codigo=nuevo_codigo,
                descripcion=descripcion,
                tipo=tipo,
                prioridad=prioridad,
                equipo_id=equipo_id,
                tecnico_asignado=tecnico_asignado,
                fecha_inicio_plan=datetime.combine(fecha_inicio, datetime.min.time()),
                fecha_fin_plan=datetime.combine(fecha_fin, datetime.min.time())
            )
            
            session.add(nueva_orden)
            session.commit()
            st.success(f"Orden {nuevo_codigo} creada exitosamente!")
            st.rerun()
        else:
            st.error("Por favor complete todos los campos requeridos")

# Filtros
st.subheader("Filtros")
col1, col2, col3 = st.columns(3)
with col1:
    filtro_estado = st.selectbox("Estado", ["Todos", "Pendiente", "En Progreso", "Completada", "Cancelada"])
with col2:
    filtro_prioridad = st.selectbox("Prioridad", ["Todas", "Baja", "Media", "Alta", "Crítica"])
with col3:
    filtro_equipo = st.selectbox("Equipo", ["Todos"] + [eq.nombre for eq in session.query(Equipo).all()])

# Aplicar filtros
query = session.query(OrdenTrabajo)

if filtro_estado != "Todos":
    query = query.filter(OrdenTrabajo.estado == filtro_estado)

if filtro_prioridad != "Todas":
    query = query.filter(OrdenTrabajo.prioridad == filtro_prioridad)

if filtro_equipo != "Todos":
    query = query.join(Equipo).filter(Equipo.nombre == filtro_equipo)

# Mostrar órdenes
ordenes = query.order_by(OrdenTrabajo.fecha_creacion.desc()).all()

if ordenes:
    datos = []
    for orden in ordenes:
        datos.append({
            'Código': orden.codigo,
            'Descripción': orden.descripcion,
            'Equipo': orden.equipo.nombre if orden.equipo else 'N/A',
            'Tipo': orden.tipo,
            'Prioridad': orden.prioridad,
            'Estado': orden.estado,
            'Técnico': orden.tecnico_asignado or 'No asignado',
            'Fecha Creación': orden.fecha_creacion.strftime('%d/%m/%Y')
        })
    
    df = pd.DataFrame(datos)
    st.dataframe(df, use_container_width=True)
    
    # Detalles de orden seleccionada
    st.subheader("Detalles de Orden Seleccionada")
    orden_seleccionada = st.selectbox(
        "Seleccionar orden para ver detalles",
        options=[o.codigo for o in ordenes]
    )
    
    if orden_seleccionada:
        orden = session.query(OrdenTrabajo).filter_by(codigo=orden_seleccionada).first()
        if orden:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Descripción:** {orden.descripcion}")
                st.write(f"**Equipo:** {orden.equipo.nombre if orden.equipo else 'N/A'}")
                st.write(f"**Tipo:** {orden.tipo}")
                st.write(f"**Prioridad:** {orden.prioridad}")
            with col2:
                st.write(f"**Estado:** {orden.estado}")
                st.write(f"**Técnico:** {orden.tecnico_asignado or 'No asignado'}")
                st.write(f"**Fecha Inicio Plan:** {orden.fecha_inicio_plan.strftime('%d/%m/%Y') if orden.fecha_inicio_plan else 'N/A'}")
                st.write(f"**Fecha Fin Plan:** {orden.fecha_fin_plan.strftime('%d/%m/%Y') if orden.fecha_fin_plan else 'N/A'}")
            
            # Actualizar estado
            nuevo_estado = st.selectbox("Cambiar estado", 
                                      ["Pendiente", "En Progreso", "Completada", "Cancelada"],
                                      index=["Pendiente", "En Progreso", "Completada", "Cancelada"].index(orden.estado))
            
            if st.button("Actualizar Estado"):
                orden.estado = nuevo_estado
                if nuevo_estado == "Completada" and not orden.fecha_fin_real:
                    orden.fecha_fin_real = datetime.now()
                session.commit()
                st.success("Estado actualizado correctamente!")
                st.rerun()
else:
    st.info("No se encontraron órdenes con los filtros aplicados")

session.close()