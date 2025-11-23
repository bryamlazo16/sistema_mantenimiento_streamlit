import streamlit as st
import pandas as pd
from database import get_session, Equipo, OrdenTrabajo

st.set_page_config(page_title="Gestión de Equipos", layout="wide")

st.title("🏭 Gestión de Equipos")

session = get_session()

# Formulario para nuevo equipo
with st.form("nuevo_equipo"):
    st.subheader("Registrar Nuevo Equipo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input("Nombre del equipo")
        ubicacion = st.text_input("Ubicación")
        
    with col2:
        descripcion = st.text_area("Descripción")
        estado = st.selectbox("Estado", ["Operativo", "En Mantenimiento", "Parado", "Fuera de Servicio"])
    
    submitted = st.form_submit_button("Registrar Equipo")
    
    if submitted:
        if nombre:
            # Generar código
            ultimo_equipo = session.query(Equipo).order_by(Equipo.id.desc()).first()
            nuevo_codigo = f"EQ-{ultimo_equipo.id + 1:05d}" if ultimo_equipo else "EQ-00001"
            
            nuevo_equipo = Equipo(
                codigo=nuevo_codigo,
                nombre=nombre,
                descripcion=descripcion,
                ubicacion=ubicacion,
                estado=estado
            )
            
            session.add(nuevo_equipo)
            session.commit()
            st.success(f"Equipo {nuevo_codigo} registrado exitosamente!")
            st.rerun()
        else:
            st.error("El nombre del equipo es requerido")

# Mostrar equipos
st.subheader("Lista de Equipos")

equipos = session.query(Equipo).order_by(Equipo.nombre).all()

if equipos:
    datos = []
    for equipo in equipos:
        # Contar órdenes por equipo
        ordenes_count = session.query(OrdenTrabajo).filter_by(equipo_id=equipo.id).count()
        ordenes_activas = session.query(OrdenTrabajo).filter_by(equipo_id=equipo.id, estado="En Progreso").count()
        
        datos.append({
            'Código': equipo.codigo,
            'Nombre': equipo.nombre,
            'Ubicación': equipo.ubicacion or 'N/A',
            'Estado': equipo.estado,
            'Total Órdenes': ordenes_count,
            'Órdenes Activas': ordenes_activas,
            'Fecha Registro': equipo.created_at.strftime('%d/%m/%Y')
        })
    
    df = pd.DataFrame(datos)
    st.dataframe(df, use_container_width=True)
    
    # Detalles del equipo seleccionado
    st.subheader("Detalles del Equipo")
    equipo_seleccionado = st.selectbox(
        "Seleccionar equipo para ver detalles",
        options=[e.codigo for e in equipos]
    )
    
    if equipo_seleccionado:
        equipo = session.query(Equipo).filter_by(codigo=equipo_seleccionado).first()
        if equipo:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Nombre:** {equipo.nombre}")
                st.write(f"**Código:** {equipo.codigo}")
                st.write(f"**Ubicación:** {equipo.ubicacion or 'N/A'}")
            with col2:
                st.write(f"**Estado:** {equipo.estado}")
                st.write(f"**Fecha Registro:** {equipo.created_at.strftime('%d/%m/%Y')}")
            
            if equipo.descripcion:
                st.write(f"**Descripción:** {equipo.descripcion}")
            
            # Historial de órdenes del equipo
            st.subheader("Historial de Órdenes")
            ordenes_equipo = session.query(OrdenTrabajo).filter_by(equipo_id=equipo.id).order_by(
                OrdenTrabajo.fecha_creacion.desc()
            ).all()
            
            if ordenes_equipo:
                datos_ordenes = []
                for orden in ordenes_equipo:
                    datos_ordenes.append({
                        'Código': orden.codigo,
                        'Descripción': orden.descripcion,
                        'Tipo': orden.tipo,
                        'Prioridad': orden.prioridad,
                        'Estado': orden.estado,
                        'Técnico': orden.tecnico_asignado or 'No asignado',
                        'Fecha': orden.fecha_creacion.strftime('%d/%m/%Y')
                    })
                
                df_ordenes = pd.DataFrame(datos_ordenes)
                st.dataframe(df_ordenes, use_container_width=True)
            else:
                st.info("No hay órdenes registradas para este equipo")
else:
    st.info("No hay equipos registrados")

session.close()