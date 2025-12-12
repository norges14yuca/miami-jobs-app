import streamlit as st
import pandas as pd
import sqlite3
import os

# Configuración de pantalla
st.set_page_config(page_title="Miami Jobs Explorer", layout="wide")

# --- CONFIGURACIÓN CORREGIDA ---
# El archivo vive dentro de la carpeta "datos"
DB_PATH = os.path.join("datos", "miami_jobs.db")

@st.cache_data
def cargar_datos():
    # Depuración: Si no existe, avisa dónde está buscando
    if not os.path.exists(DB_PATH):
        return None
    
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM ofertas", conn)
    except:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

st.title("🍎 Miami-Dade Schools: Cloud Visor")
st.caption("Versión Online Restaurada (v1.50.0)")

df = cargar_datos()

# Si falla, mostramos ayuda visual
if df is None:
    st.error(f"❌ ERROR CRÍTICO: No encuentro la base de datos.")
    st.warning(f"📍 Estoy buscando aquí: `{os.path.abspath(DB_PATH)}`")
    st.info("💡 Asegúrate de estar ejecutando el comando desde la carpeta 'miami_jobs_app' y que la carpeta 'datos' exista.")
    st.stop()

if df.empty:
    st.warning("⚠️ La base de datos se encontró, pero está vacía.")
    st.stop()

# --- FILTROS LATERALES ---
with st.sidebar:
    st.header("🔍 Filtros")
    busqueda = st.text_input("Buscar cargo o escuela:")
    
    if "salario_min" in df.columns:
        max_val = df["salario_min"].fillna(0).max()
        if max_val > 0:
            salario = st.slider("Salario Mínimo ($)", 0, int(max_val), 0, step=1000)
        else:
            salario = 0
    else:
        salario = 0

# --- LÓGICA DE FILTRADO ---
df_filtrado = df.copy()

if busqueda:
    mask = df_filtrado["titulo"].str.contains(busqueda, case=False, na=False) | \
           df_filtrado["escuela"].str.contains(busqueda, case=False, na=False)
    df_filtrado = df_filtrado[mask]

if "salario_min" in df.columns:
    df_filtrado = df_filtrado[df_filtrado["salario_min"] >= salario]

df_filtrado = df_filtrado.reset_index(drop=True)

# --- TABLA PRINCIPAL ---
column_cfg = {
    "link_apply_directo": st.column_config.LinkColumn("Acción", display_text="🚀 APLICAR"),
    "url_oferta": st.column_config.LinkColumn("Original", display_text="🔗 Web"),
    "salario_min": st.column_config.NumberColumn("Salario Min", format="$%.2f"),
    "titulo": st.column_config.TextColumn("Cargo", width="large"),
    "descripcion_html": None, 
    "ubicacion_raw": None,
    "pdf_url": None,
    "req_id": None
}

evento = st.dataframe(
    df_filtrado,
    column_config=column_cfg,
    use_container_width=True,
    hide_index=True,
    selection_mode="single-row",
    on_select="rerun",
    height=400
)

# --- DETALLE DE LA OFERTA ---
st.markdown("---")
st.header("📄 Detalle de la Oferta")

if df_filtrado.empty:
    st.warning("No hay ofertas que coincidan con tu búsqueda.")
    st.stop()

# LÓGICA DE SELECCIÓN AUTOMÁTICA
# Si el usuario selecciona una fila, usamos esa. Si no, usamos la primera (índice 0).
if len(evento.selection.rows) > 0:
    indice_seleccionado = evento.selection.rows[0]
    fila = df_filtrado.iloc[indice_seleccionado]
else:
    fila = df_filtrado.iloc[0]

# --- VISUALIZACIÓN DEL DETALLE ---
c1, c2 = st.columns([1, 2])

with c1:
    st.info(f"**ID:** {fila.get('req_id', 'N/A')}")
    st.write(f"**🏢 Escuela:**")
    st.subheader(fila.get('escuela', 'No especificada'))
    
    sal = fila.get('salario_min', 0)
    st.success(f"**💰 Salario Base:** ${sal:,.2f}")
    
    link = fila.get("link_apply_directo") or fila.get("url_oferta")
    if link:
        st.link_button("🚀 Ir a la Postulación Oficial", link, type="primary", use_container_width=True)

with c2:
    st.write("**Descripción del Puesto:**")
    desc = fila.get("descripcion_html", "No hay descripción disponible.")
    with st.container(height=500, border=True):
        st.markdown(desc, unsafe_allow_html=True)
