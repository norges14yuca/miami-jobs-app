import streamlit as st
import pandas as pd
import sqlite3
import os

# Configuración de pantalla
st.set_page_config(page_title="Miami Jobs Explorer", layout="wide")

# --- CONFIGURACIÓN PARA LA NUBE ---
# Al subirlo a GitHub, pondremos el archivo .db junto al script
DB_PATH = "miami_jobs.db"

def cargar_datos():
    # Verificamos si existe la DB
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM ofertas", conn)
    except:
        df = pd.DataFrame()
    conn.close()
    return df

st.title("🍎 Miami-Dade Schools: Cloud Visor")
st.caption("Versión Online para Control de Calidad")

df = cargar_datos()

if df.empty:
    st.error(f"⚠️ No encuentro el archivo '{DB_PATH}'. Asegúrate de subirlo a GitHub junto con este script.")
    st.stop()

# --- FILTROS ---
with st.sidebar:
    st.header("🔍 Filtros")
    busqueda = st.text_input("Buscar texto:")
    
    if "salario_min" in df.columns:
        max_sal = int(df["salario_min"].max())
        salario = st.slider("Salario Min ($)", 0, max_sal, 0, step=1000)

# --- APLICAR FILTROS ---
df_filtrado = df.copy()

if busqueda:
    mask = df_filtrado["titulo"].str.contains(busqueda, case=False, na=False) | \
           df_filtrado["escuela"].str.contains(busqueda, case=False, na=False)
    df_filtrado = df_filtrado[mask]

if "salario_min" in df.columns:
    df_filtrado = df_filtrado[df_filtrado["salario_min"] >= salario]

df_filtrado = df_filtrado.reset_index(drop=True)

# --- TABLA INTERACTIVA ---
evento = st.dataframe(
    df_filtrado,
    column_config={
        "link_apply_directo": st.column_config.LinkColumn("Acción", display_text="🚀 APLICAR"),
        "url_oferta": st.column_config.LinkColumn("Original", display_text="🔗 Web"),
        "salario_min": st.column_config.NumberColumn("Salario", format="$%.2f"),
        "descripcion_html": None, 
        "ubicacion_raw": None,
        "pdf_url": None
    },
    use_container_width=True,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun", 
    height=400
)

# --- DETALLE ---
st.markdown("---")
st.header("📄 Detalle")

if evento.selection.rows:
    indice = evento.selection.rows[0]
    fila = df_filtrado.iloc[indice]
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.info(f"**ID:** {fila['req_id']}")
        st.write(f"**Escuela:** {fila['escuela']}")
        st.success(f"**Salario:** ${fila.get('salario_min', 0)}")
        
        link = fila.get("link_apply_directo", fila["url_oferta"])
        st.link_button("🚀 Ir a Aplicar", link, type="primary")

    with c2:
        st.text_area("Descripción:", value=fila.get("descripcion_html", ""), height=500)
else:
    st.info("👆 Selecciona una oferta arriba para ver detalles.")
