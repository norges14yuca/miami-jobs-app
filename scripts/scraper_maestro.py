import time
import pandas as pd
import re
import sqlite3
import os
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "datos", "miami_jobs.db")
CSV_PATH = os.path.join(BASE_DIR, "datos", "miami_jobs.csv")

# URL BASE SIN EL FINAL (Nosotros añadiremos el &startrow=...)
URL_BASE = "https://apply.dadeschools.net/search/?q=&sortColumn=referencedate&sortDirection=asc"

def iniciar_navegador():
    print("🔵 Iniciando navegador Chrome...")
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless') # Descomenta para ocultar navegador
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def limpiar_fecha(texto_fecha):
    try:
        obj_fecha = datetime.strptime(texto_fecha.strip(), "%b %d, %Y")
        return obj_fecha.strftime("%Y-%m-%d")
    except:
        return None

def extraer_escuela(titulo):
    """Limpia el título para sacar solo el nombre de la escuela"""
    if "_" in titulo:
        parte_final = titulo.split("_")[-1]
        nombre_limpio = re.sub(r'\(\d+\)', '', parte_final).strip()
        return nombre_limpio
    return "General / District Wide"

def fase_1_obtener_links(driver):
    print("\n🚜 --- FASE 1: RECOLECCIÓN POR URL ---")
    links_totales = []
    
    offset = 0      # Empezamos en 0
    salto = 100     # Saltamos de 100 en 100
    
    while True:
        url_actual = f"{URL_BASE}&startrow={offset}"
        print(f"   🔎 Visitando bloque: {offset} -> {url_actual}")
        driver.get(url_actual)
        
        try:
            WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.TAG_NAME, "tr")))
            elementos = driver.find_elements(By.CSS_SELECTOR, "td a") 
            nuevos = [e.get_attribute("href") for e in elementos if "job" in e.get_attribute("href")]
            nuevos = list(set(nuevos)) 
            
            if len(nuevos) == 0:
                print("   🛑 No se encontraron más links. Fin de la búsqueda.")
                break
                
            links_totales.extend(nuevos)
            print(f"      ✅ Encontrados: {len(nuevos)} links nuevos.")
            
            offset += salto
            time.sleep(2) 
            
        except Exception as e:
            print(f"   ⚠️ Error o fin de lista en offset {offset}: {e}")
            break
            
    lista_final = list(set(links_totales))
    print(f"🎯 FASE 1 TERMINADA. Total ofertas únicas: {len(lista_final)}")
    return lista_final

def fase_2_mineria_datos(driver, links):
    print(f"\n⛏️ --- FASE 2: MINERÍA DE DETALLES ({len(links)} ofertas) ---")
    base_datos = []
    
    for i, link in enumerate(links):
        print(f"   ⏳ ({i+1}/{len(links)}) Procesando...", end="\r")
        sys.stdout.flush() 
        
        item = {
            "req_id": None, "titulo": "Sin Titulo", "escuela": "Desconocida",
            "categoria": None, "fecha_publicacion": None, "ubicacion_raw": None,
            "salario_min": 0.0, "es_por_hora": False, "pdf_url": None,
            "email_contacto": None, "deadline": None, "descripcion_html": None,
            "url_oferta": link,
            "link_apply_directo": None # <--- CAMPO CLAVE
        }
        
        try:
            driver.get(link)
            # time.sleep(0.5) 
            
            # 1. TEXTO COMPLETO
            try:
                cuerpo = driver.find_element(By.TAG_NAME, "body").text
                item["descripcion_html"] = cuerpo
            except: cuerpo = ""

            # 2. CABECERA Y ESCUELA
            try:
                item["titulo"] = driver.find_element(By.TAG_NAME, "h1").text
                item["escuela"] = extraer_escuela(item["titulo"])
            except: pass
            
            # 3. SPANS
            campos = {"req_id": "Req ID", "fecha_publicacion": "Posted On", 
                      "categoria": "Category", "ubicacion_raw": "Location"}
            for key, label in campos.items():
                try:
                    val = driver.find_element(By.XPATH, f"//span[contains(text(), '{label}')]/following-sibling::span").text
                    if key == "fecha_publicacion": item[key] = limpiar_fecha(val)
                    else: item[key] = val
                except: pass

            # 4. SALARIO
            match_sal = re.search(r"(?:Salary Minimum|Starting Salary):?\s*\$([\d,]+\.?\d*)", cuerpo, re.IGNORECASE)
            if match_sal:
                sal = float(match_sal.group(1).replace(",", ""))
                item["salario_min"] = sal
                if sal < 100: item["es_por_hora"] = True

            # 5. PDF Y EMAIL
            match_pdf = re.search(r"(https?://salary\.dadeschools\.net/.*\.pdf)", cuerpo)
            if match_pdf: item["pdf_url"] = match_pdf.group(1)
            
            match_email = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cuerpo)
            if match_email: item["email_contacto"] = match_email.group(0)

            # 6. DEADLINE
            match_d = re.search(r"(?:deadline is|Deadline:)\s*([A-Za-z]+\s\d{1,2},\s\d{4})", cuerpo, re.IGNORECASE)
            if match_d: item["deadline"] = limpiar_fecha(match_d.group(1))

            # 7. EXTRACCIÓN DEL LINK "APPLY NOW"
            try:
                # Intenta encontrar el botón por texto "Apply" insensible a mayúsculas/minúsculas
                boton_apply = driver.find_element(By.XPATH, "//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'apply')]")
                item["link_apply_directo"] = boton_apply.get_attribute("href")
            except:
                # Si falla, asume la estructura estándar de URL + /apply
                if link.endswith("/"):
                    item["link_apply_directo"] = link + "apply"
                else:
                    item["link_apply_directo"] = link + "/apply"

            base_datos.append(item)

        except Exception as e:
            continue

    print("\n✅ FASE 2 TERMINADA.")
    return base_datos

def guardar_datos(datos):
    if not datos:
        print("❌ No hay datos para guardar.")
        return

    print(f"\n💾 --- GUARDANDO {len(datos)} REGISTROS ---")
    df = pd.DataFrame(datos)
    
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    
    df.to_csv(CSV_PATH, index=False, encoding='utf-8-sig')
    print(f"   ✅ CSV creado: {CSV_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        df.to_sql("ofertas", conn, if_exists="replace", index=False)
        conn.close()
        print(f"   ✅ Base de Datos SQL: {DB_PATH}")
    except Exception as e:
        print(f"   ❌ Error SQL: {e}")

if __name__ == "__main__":
    driver = iniciar_navegador()
    try:
        links = fase_1_obtener_links(driver)
        if len(links) > 0:
            datos = fase_2_mineria_datos(driver, links)
            guardar_datos(datos)
        else:
            print("⚠️ No se encontraron links en la Fase 1.")
    except Exception as e:
        print(f"\n❌ ERROR FATAL: {e}")
    finally:
        print("👋 Cerrando navegador.")
        driver.quit()
