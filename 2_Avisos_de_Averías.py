import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_session, AvisoAveria, Equipo

st.set_page_config(page_title="Avisos de Averías", layout="wide")

st.title("⚠️ Avisos de Averías")

session = get_session()

# Formulario para nuevo aviso
with st.form("nuevo_aviso"):
    st.subheader("Reportar Nueva Avería")
    
    col1, col2 = st.columns(2)
    
    with col1:
        descripcion = st.text_area("Descripción de la avería", height=100)
        equipo_id = st.selectbox(
            "Equipo afectado",
            options=[eq.id for eq in session.query(Equipo).all()],
            format_func=lambda x: session.query(Equipo).get(x).nombre
        )
        
    with col2:
        reportado_por = st.text_input("Reportado por")
        prioridad = st.selectbox("Prioridad", ["Baja", "Media", "Alta", "Crítica"])
        observaciones = st.text_area("Observaciones adicionales")
    
    submitted = st.form_submit_button("Reportar Avería")
    
    if submitted:
        if descripcion and equipo_id and reportado_por:
            # Generar código
            ultimo_aviso = session.query(AvisoAveria).order_by(AvisoAveria.id.desc()).first()
            nuevo_codigo = f"AV-{ultimo_aviso.id + 1:05d}" if ultimo_aviso else "AV-00001"
            
            nuevo_aviso = AvisoAveria(
                codigo=nuevo_codigo,
                descripcion=descripcion,
                reportado_por=reportado_por,
                prioridad=prioridad,
                equipo_id=equipo_id,
                observaciones=observaciones
            )
            
            session.add(nuevo_aviso)
            session.commit()
            st.success(f"Aviso {nuevo_codigo} reportado exitosamente!")
            st.rerun()
        else:
            st.error("Por favor complete todos los campos requeridos")

# Mostrar avisos
st.subheader("Avisos de Averías Activos")

avisos = session.query(AvisoAveria).order_by(AvisoAveria.fecha_reporte.desc()).all()

if avisos:
    datos = []
    for aviso in avisos:
        datos.append({
            'Código': aviso.codigo,
            'Descripción': aviso.descripcion,
            'Equipo': aviso.equipo.nombre if aviso.equipo else 'N/A',
            'Prioridad': aviso.prioridad,
            'Estado': aviso.estado,
            'Reportado por': aviso.reportado_por,
            'Fecha': aviso.fecha_reporte.strftime('%d/%m/%Y %H:%M')
        })
    
    df = pd.DataFrame(datos)
    st.dataframe(df, use_container_width=True)
    
    # Detalles y gestión de avisos
    st.subheader("Gestión de Aviso Seleccionado")
    aviso_seleccionado = st.selectbox(
        "Seleccionar aviso para gestionar",
        options=[a.codigo for a in avisos]
    )
    
    if aviso_seleccionado:
        aviso = session.query(AvisoAveria).filter_by(codigo=aviso_seleccionado).first()
        if aviso:
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Descripción:** {aviso.descripcion}")
                st.write(f"**Equipo:** {aviso.equipo.nombre if aviso.equipo else 'N/A'}")
                st.write(f"**Reportado por:** {aviso.reportado_por}")
            with col2:
                st.write(f"**Prioridad:** {aviso.prioridad}")
                st.write(f"**Estado:** {aviso.estado}")
                st.write(f"**Fecha Reporte:** {aviso.fecha_reporte.strftime('%d/%m/%Y %H:%M')}")
            
            if aviso.observaciones:
                st.write(f"**Observaciones:** {aviso.observaciones}")
            
            # Actualizar estado
            col1, col2 = st.columns(2)
            with col1:
                nuevo_estado = st.selectbox("Cambiar estado", 
                                          ["Reportado", "En Análisis", "En Reparación", "Resuelto"],
                                          index=["Reportado", "En Análisis", "En Reparación", "Resuelto"].index(aviso.estado))
            with col2:
                nuevas_observaciones = st.text_area("Actualizar observaciones", value=aviso.observaciones or "")
            
            if st.button("Actualizar Aviso"):
                aviso.estado = nuevo_estado
                aviso.observaciones = nuevas_observaciones
                if nuevo_estado == "Resuelto" and not aviso.fecha_cierre:
                    aviso.fecha_cierre = datetime.now()
                session.commit()
                st.success("Aviso actualizado correctamente!")
                st.rerun()
            
            # Crear orden de trabajo desde aviso
            if st.button("Crear Orden de Trabajo desde este Aviso"):
                ultima_orden = session.query(OrdenTrabajo).order_by(OrdenTrabajo.id.desc()).first()
                nuevo_codigo = f"OT-{ultima_orden.id + 1:05d}" if ultima_orden else "OT-00001"
                
                nueva_orden = OrdenTrabajo(
                    codigo=nuevo_codigo,
                    descripcion=f"Reparación: {aviso.descripcion}",
                    tipo="Correctivo",
                    prioridad=aviso.prioridad,
                    equipo_id=aviso.equipo_id,
                    aviso_id=aviso.id,
                    fecha_inicio_plan=datetime.now()
                )
                
                session.add(nueva_orden)
                aviso.estado = "En Reparación"
                session.commit()
                st.success(f"Orden de trabajo {nuevo_codigo} creada desde el aviso!")
                st.rerun()
else:
    st.info("No hay avisos de averías registrados")

session.close()