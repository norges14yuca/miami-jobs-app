import streamlit as st
import pandas as pd
import sqlite3
import os

# --- CONFIGURACIÓN DE PANTALLA ---
st.set_page_config(
    page_title="Miami Jobs Map", 
    layout="wide", 
    page_icon="🗺️",
    initial_sidebar_state="collapsed" # Esconde la barra lateral por defecto
)

# --- ESTILOS CSS PARA APROVECHAR ESPACIO ---
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    h1 {margin-bottom: 0.5rem;}
</style>
""", unsafe_allow_html=True)

# --- 1. BUSCADOR DE BASE DE DATOS ---
def encontrar_db():
    posibles = ["datos/miami_jobs.db", "miami_jobs.db", "../datos/miami_jobs.db"]
    for p in posibles:
        if os.path.exists(p): return p
    return None

path = encontrar_db()
if not path:
    st.error("❌ No se encuentra el archivo 'miami_jobs.db'.")
    st.stop()

# --- 2. CARGAR DATOS ---
@st.cache_data
def get_data(db_path):
    conn = sqlite3.connect(db_path)
    # Traemos solo lo que tiene coordenadas
    query = "SELECT * FROM ofertas WHERE latitud IS NOT NULL AND latitud > 1"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

df = get_data(path)

# Preparar datos para el mapa (Streamlit pide columnas 'lat' y 'lon')
df = df.rename(columns={'latitud': 'lat', 'longitud': 'lon'})

# --- 3. INTERFAZ: TÍTULO ---
c_title, c_metric = st.columns([3, 1])
with c_title:
    st.title("🗺️ Mapa de Empleos")
with c_metric:
    st.metric("Oportunidades", len(df))

# --- 4. MAPA INTERACTIVO (EL PROTAGONISTA) ---
# on_select="rerun" hace que al hacer clic, el script corra de nuevo y sepamos qué se tocó
mapa = st.map(
    df,
    latitude='lat',
    longitude='lon',
    color='#FF4B4B',   # Rojo Streamlit
    size=60,           # Puntos grandes para fácil clic
    zoom=10,
    use_container_width=True,
    height=450,
    on_select="rerun"  # <--- LA CLAVE DE LA INTERACTIVIDAD
)

# --- 5. LOGICA DE SELECCIÓN ---
# Obtenemos las filas seleccionadas (si hay alguna)
seleccion = mapa.selection.rows

st.divider()

if len(seleccion) > 0:
    # --- CASO: USUARIO HIZO CLIC EN UN PUNTO ---
    idx = seleccion[0]
    oferta = df.iloc[idx]
    
    # Diseño de la tarjeta de detalle
    col_izq, col_der = st.columns([1, 2])
    
    with col_izq:
        st.subheader("📍 Escuela Seleccionada")
        st.info(f"**{oferta['escuela']}**")
        
        st.write(f"**Cargo:** {oferta['titulo']}")
        st.write(f"**ID:** {oferta.get('req_id', 'N/A')}")
        
        salario = oferta.get('salario_min', 0)
        st.success(f"💰 **Salario Base:** ${salario:,.2f}")
        
        # Botón de acción
        link = oferta.get("link_apply_directo") or oferta.get("url_oferta")
        if link:
            st.link_button("🚀 APLICAR AHORA", link, type="primary", use_container_width=True)
            
    with col_der:
        st.write("📄 **Descripción del Puesto:**")
        # Caja con scroll para leer cómodo
        with st.container(height=300, border=True):
            html = oferta.get("descripcion_html", "No hay detalles disponibles.")
            st.markdown(html, unsafe_allow_html=True)

else:
    # --- CASO: NADA SELECCIONADO (ESTADO INICIAL) ---
    st.info("👆 **Haz clic en cualquier punto rojo del mapa** para ver los detalles de la oferta aquí.")
    
    # Mostramos una tabla resumen simple abajo
    with st.expander("Ver lista completa en tabla"):
        st.dataframe(
            df[['escuela', 'titulo', 'salario_min']],
            column_config={"salario_min": st.column_config.NumberColumn("Salario", format="$%.2f")},
            use_container_width=True,
            hide_index=True
        )
