import streamlit as st
import pandas as pd
from database import get_session, OrdenTrabajo

st.set_page_config(page_title="Órdenes Completadas", layout="wide")

st.title("✅ Órdenes de Trabajo Completadas")

session = get_session()

# Obtener órdenes completadas
ordenes = session.query(OrdenTrabajo).filter_by(estado="Completada").order_by(
    OrdenTrabajo.fecha_fin_real.desc()
).all()

if ordenes:
    # Métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_completadas = len(ordenes)
        st.metric("Total Completadas", total_completadas)
    
    with col2:
        avg_horas = sum(o.horas_reales or 0 for o in ordenes) / len(ordenes) if ordenes else 0
        st.metric("Promedio Horas", f"{avg_horas:.1f}")
    
    with col3:
        total_costo = sum(o.costo_real or 0 for o in ordenes)
        st.metric("Costo Total", f"${total_costo:,.2f}")
    
    # Tabla de órdenes completadas
    datos = []
    for orden in ordenes:
        datos.append({
            'Código': orden.codigo,
            'Descripción': orden.descripcion,
            'Equipo': orden.equipo.nombre if orden.equipo else 'N/A',
            'Tipo': orden.tipo,
            'Técnico': orden.tecnico_asignado or 'No asignado',
            'Horas Reales': orden.horas_reales or 0,
            'Costo Real': orden.costo_real or 0,
            'Fecha Inicio': orden.fecha_inicio_real.strftime('%d/%m/%Y') if orden.fecha_inicio_real else 'N/A',
            'Fecha Fin': orden.fecha_fin_real.strftime('%d/%m/%Y') if orden.fecha_fin_real else 'N/A'
        })
    
    df = pd.DataFrame(datos)
    st.dataframe(df, use_container_width=True)
    
    # Exportar datos
    if st.button("📊 Exportar a CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Descargar CSV",
            data=csv,
            file_name=f"ordenes_completadas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    st.info("No hay órdenes completadas registradas")

session.close()