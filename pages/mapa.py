import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Mapa de Empleos", layout="wide", page_icon="🗺️")

st.title("🗺️ Mapa de Oportunidades en Miami-Dade")

# --- CONEXIÓN A LA BASE DE DATOS ---
def encontrar_db():
    # Buscamos la DB subiendo un nivel o en la carpeta 'datos'
    posibles = [
        "../datos/miami_jobs.db",  # Desde la carpeta pages/
        "datos/miami_jobs.db",     # Si se corre desde raíz
        "miami_jobs.db"
    ]
    for p in posibles:
        if os.path.exists(p): return p
    return None

path = encontrar_db()
if not path:
    st.error("❌ No se encuentra la base de datos.")
    st.stop()

# --- CARGAR DATOS GEOLOCALIZADOS ---
conn = sqlite3.connect(path)
# Solo traemos las filas que tienen coordenadas válidas (distintas de 0 y 0.1)
query = """
    SELECT req_id, titulo, escuela, salario_min, latitud, longitud 
    FROM ofertas 
    WHERE latitud IS NOT NULL 
    AND latitud != 0 
    AND latitud != 0.1
"""
df = pd.read_sql(query, conn)
conn.close()

if df.empty:
    st.warning("⚠️ No hay ofertas con ubicación detectada todavía.")
    st.info("Ejecuta 'python preparar_mapa.py' nuevamente para intentar encontrar más.")
    st.stop()

# --- PREPARAR EL MAPA ---
# Streamlit necesita columnas llamadas 'lat' y 'lon'
df_mapa = df.rename(columns={'latitud': 'lat', 'longitud': 'lon'})

# Métrica rápida
st.metric("📍 Ubicaciones encontradas", len(df_mapa))

# PINTAR EL MAPA
st.map(df_mapa, 
       latitude='lat', 
       longitude='lon', 
       color='#FF4B4B', # Rojo Streamlit
       size=20, 
       zoom=10)

# --- TABLA DE DATOS DEL MAPA ---
with st.expander("Ver lista de escuelas en el mapa"):
    st.dataframe(
        df_mapa[['escuela', 'titulo', 'salario_min']], 
        column_config={
            "salario_min": st.column_config.NumberColumn("Salario", format="$%.2f")
        },
        use_container_width=True
    )
