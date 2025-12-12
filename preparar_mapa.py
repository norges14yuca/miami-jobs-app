import sqlite3
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import os
import time

DB_PATH = os.path.join("datos", "miami_jobs.db")

# --- NIVEL 1: COORDENADAS EXACTAS (Para los casos imposibles) ---
# Aquí ponemos los que fallan por dirección. Les damos el GPS directo.
COORDENADAS_FIJAS = {
    # Los centros de mantenimiento (MSC) en 12525 NW 147th Ave
    "MAINTENANCE SVC 1": (25.889360, -80.431790),
    "MAINTENANCE SVC 2": (25.889360, -80.431790),
    "MAINTENANCE SVC 3": (25.889360, -80.431790),
    "MAINTENANCE SVC 4": (25.889360, -80.431790),
    # Robert Renick Educational Center
    "ROBERT RENICK EDUCAT": (25.963470, -80.236660),
}

# --- NIVEL 2: DIRECCIONES CORREGIDAS (Para el resto) ---
CORRECCIONES = {
    "General / District Wide": "1450 NE 2nd Ave, Miami, FL 33132",
    "FACILITIES MAINTENAN": "1450 NE 2nd Ave, Miami, FL 33132",
    "TRANSPORTATION VEHIC": "1450 NE 2nd Ave, Miami, FL 33132",
    "FOOD & NUTRITION": "7042 West Flagler Street, Miami, FL",
    "TITLE I SUPPLEMENTAL": "1450 NE 2nd Ave, Miami, FL 33132",
    "EARLY CHILDHOOD PROG": "1450 NE 2nd Ave, Miami, FL 33132",
    "DIST INSP, OPS & EME": "1450 NE 2nd Ave, Miami, FL 33132",
    "PERSONNEL OPERATIONS": "1450 NE 2nd Ave, Miami, FL 33132",
    "MIAMI-DADE SCHOOLS P": "1450 NE 2nd Ave, Miami, FL 33132",
    "CENTRAL WEST TRANSP": "13775 NW 6th St, Miami, FL 33182",
    "NE TRANSPORTATION CE": "1450 NE 2nd Ave, Miami, FL 33132",
    "SOUTH TRANSPORTATION": "660 SW 3rd Ave, Florida City, FL 33034",
    "10M": "1450 NE 2nd Ave, Miami, FL 33132",
    # Correcciones de nombres específicos
    "CARRIE P. MEEK/WESTV": "1901 NW 127th St, Miami, FL 33167",
    "MIAMI SOUTHRIDGE SEN": "Miami Southridge Senior High",
    "ROBERT MORGAN EDUCAT": "18180 SW 122nd Ave, Miami, FL 33177",
    "COCONUT GROVE ELEMEN": "3351 Matilda St, Miami, FL 33133",
    "NORTH TWIN LAKES ELE": "625 W 74th Pl, Hialeah, FL 33014",
    "JOHN I. SMITH K-8": "10415 NW 52nd St, Doral, FL 33178",
    "E.W.F. STIRRUP ELEME": "330 NW 97th Ave, Miami, FL 33172",
    "MIAMI CORAL PARK SEN": "8865 SW 16th St, Miami, FL 33165",
    "SANTA CLARA ELEMENTA": "1051 NW 29th Ter, Miami, FL 33127",
    "JANN MANN EDUCATION": "16101 NW 44th Ct, Opa-locka, FL 33054",
    "KEY BISCAYNE K - 8 C": "150 W McIntyre St, Key Biscayne, FL 33149",
    "CHARLES R. DREW K-8": "1775 NW 60th St, Miami, FL 33142",
    "MIA CORAL PARK ADULT": "8865 SW 16th St, Miami, FL 33165",
    "PAUL LAURENCE DUNBAR": "505 NW 20th St, Miami, FL 33127",
    "WILLIAM H. TURNER TE": "10151 NW 19th Ave, Miami, FL 33147",
    "VIRGINIA A. BOONE/HI": "20500 NE 24th Ave, Miami, FL 33180",
    "iPREPARATORY ACADEMY": "1500 Biscayne Blvd, Miami, FL 33132",
    "BOWMAN ASHE/DOOLIN": "6601 SW 152nd Ave, Miami, FL 33193",
    "MYRTLE GROVE K-8": "3125 NW 176th St, Miami Gardens, FL 33056",
    "MADIES IVES K-8 PREP": "20770 NE 14th Ave, Miami, FL 33179",
    "DR. MARVIN DUNN ACAD": "12001 SW 272nd St, Miami, FL 33032",
    "DR. WILLIAM A. CHAPM": "275 NW 2nd St, Homestead, FL 33030",
    "SPRINGVIEW ELEMENTAR": "1122 Bluebird Ave, Miami Springs, FL 33166",
    "DR. F. W SKYWAY ELEM": "4555 NW 206th Ter, Miami Gardens, FL 33055",
    "VENETIAN PARC ACADEMY": "15450 SW 144th St, Miami, FL 33196",
    "BARBARA J. HAWKINS E": "19010 NW 37th Ave, Miami Gardens, FL 33056",
    "DR. TONI BILBAO PREP": "8905 NW 114th Ave, Doral, FL 33178",
    "ITECH@ THOMAS A. EDI": "6101 NW 2nd Ave, Miami, FL 33127",
    "RUTH K. BROAD/BAY HA": "1155 93rd St, Bay Harbor Islands, FL 33154",
    "GEORGE T. BAKER AVIA": "3275 NW 42nd Ave, Miami, FL 33142",
    "JACK D. GORDON COMMU": "14600 Country Walk Dr, Miami, FL 33186",
    "MIAMI BEACH FIENBERG": "1420 Washington Ave, Miami Beach, FL 33139",
    "HUBERT O. SIBLEY K-8": "255 NW 115th St, Miami, FL 33168",
    "GERTRUDE K. EDELMAN/": "16100 NE 19th Ave, North Miami Beach, FL 33162",
    "JOHN A. FERGUSON SEN": "15900 SW 56th St, Miami, FL 33185",
    "DR. ROBERT B. INGRAM": "600 Ahmad St, Opa-locka, FL 33054",
    "MIAMI CAROL CITY SEN": "3301 Miami Gardens Dr, Miami Gardens, FL 33056",
    "D.A. DORSEYTECH COLL": "7100 NW 17th Ave, Miami, FL 33147",
    "HIALEAH GARDENS SENI": "11700 Hialeah Gardens Blvd, Hialeah Gardens, FL 33018",
    "COCONUT PALM K-8 CEN": "24400 SW 124th Ave, Homestead, FL 33032",
    "C.O.P.E. NORTH ALTER": "9950 NW 19th Ave, Miami, FL 33147",
    "MARCOS A. MILAM K-8": "6020 W 16th Ave, Hialeah, FL 33012",
    "DR. HENRY E. PERRINE": "8851 SW 168th St, Palmetto Bay, FL 33157",
    "LAKEVIEW ELEMENTARY": "1290 NW 115th St, Miami, FL 33167",
    "W. J. BRYAN ELEMENTA": "1201 NE 125th St, North Miami, FL 33161",
    "JOSE MARTI MAST 6-12": "5701 W 24th Ave, Hialeah, FL 33016"
}

def limpiar_nombre(texto):
    t = texto.upper()
    t = t.replace("SENI", "SENIOR HIGH")
    t = t.replace("ELEM", "ELEMENTARY SCHOOL")
    t = t.replace("MID", "MIDDLE SCHOOL")
    t = t.replace("CTR", "CENTER")
    t = t.replace("ACAD", "ACADEMY")
    return t

def preparar_datos():
    if not os.path.exists(DB_PATH):
        print("❌ No encuentro la base de datos.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Buscamos TODO lo que no esté perfecto (incluyendo los que fallaron con 0.1 o 0.01)
    df_pendientes = pd.read_sql("""
        SELECT req_id, escuela FROM ofertas 
        WHERE latitud IS NULL OR latitud < 1
    """, conn)
    
    if df_pendientes.empty:
        print("🎉 ¡OBJETIVO ALCANZADO! 100% DE ESCUELAS LOCALIZADAS.")
        conn.close()
        return

    print(f"🌍 Atacando las últimas {len(df_pendientes)} escuelas difíciles...")
    
    geolocator = Nominatim(user_agent="miami_jobs_final_v4", timeout=10)

    for i, row in df_pendientes.iterrows():
        escuela_raw = row['escuela']
        req_id = row['req_id']
        
        # 1. ¿Está en la lista de Coordenadas Fijas (Nivel Nuclear)?
        if escuela_raw in COORDENADAS_FIJAS:
            lat, lon = COORDENADAS_FIJAS[escuela_raw]
            print(f"🎯 [GPS Directo] {escuela_raw} -> {lat}, {lon}")
            cursor.execute("UPDATE ofertas SET latitud = ?, longitud = ? WHERE req_id = ?", (lat, lon, req_id))
            conn.commit()
            continue # Saltamos al siguiente ciclo

        # 2. ¿Está en el diccionario de direcciones (Nivel Manual)?
        if escuela_raw in CORRECCIONES:
            busqueda = CORRECCIONES[escuela_raw]
            tipo = "Manual"
        else:
            # 3. Limpieza automática (Nivel Auto)
            nombre_limpio = limpiar_nombre(escuela_raw)
            busqueda = f"{nombre_limpio}, Miami-Dade, FL"
            tipo = "Auto"

        # Intento de geocodificación normal
        try:
            location = geolocator.geocode(busqueda)
            if location:
                print(f"   ✅ ({tipo}) {escuela_raw} -> {location.latitude}")
                cursor.execute(
                    "UPDATE ofertas SET latitud = ?, longitud = ? WHERE req_id = ?", 
                    (location.latitude, location.longitude, req_id)
                )
                conn.commit()
            else:
                print(f"   ❌ Aún falla: {busqueda}")
                # No marcamos error permanente, dejamos que el usuario lo vea
            
            time.sleep(1.2) 

        except Exception as e:
            print(f"   ⚠️ Error: {e}")
            time.sleep(2) 

    conn.close()
    print("🏁 Proceso terminado.")

if __name__ == "__main__":
    preparar_datos()
