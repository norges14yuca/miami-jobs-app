import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURACIÓN ---
URL = "https://miami-jobs-app-mer8ukuhycmpmnhdbk9bgz.streamlit.app/"

def configurar_driver():
    options = Options()
    # options.add_argument('--headless') 
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def main():
    print("--- 📖 INICIANDO LECTURA DE TEXTO (V4) ---")
    driver = configurar_driver()
    
    try:
        driver.get(URL)
        time.sleep(5) 

        # 1. ENTRAR AL IFRAME
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if len(iframes) > 0:
            print("➡️ Entrando al Iframe 1...")
            driver.switch_to.frame(iframes[0])
            time.sleep(3)
            
            # 2. INTENTO 1: BUSCAR EL DATAFRAME (LA TABLA)
            print("\n🔎 --- BUSCANDO LA TABLA DE DATOS ---")
            tablas = driver.find_elements(By.CSS_SELECTOR, "[data-testid='stDataFrame']")
            if tablas:
                print("✅ ¡SE ENCONTRÓ EL COMPONENTE DE TABLA (DataFrame)!")
            else:
                print("⚠️ No se detectó el elemento 'stDataFrame' estándar.")

            # 3. INTENTO 2: LEER TODO EL TEXTO VISIBLE
            print("\n📖 --- VOLCADO DE TEXTO DE LA PÁGINA ---")
            # Obtenemos el texto del cuerpo principal dentro del iframe
            body_text = driver.find_element(By.TAG_NAME, "body").text
            
            # Limpiamos líneas vacías para que sea legible
            lineas = [linea for linea in body_text.split('\n') if linea.strip()]
            
            print(f"📄 Se leyeron {len(lineas)} líneas de texto.")
            print("------------------------------------------------")
            # Imprimimos las primeras 20 líneas para ver si hay ofertas
            for i, linea in enumerate(lineas[:20]):
                print(f"   Line {i+1}: {linea}")
            print("------------------------------------------------")
            
            if len(lineas) > 20:
                print("   ... (Texto restante omitido)")

        else:
            print("❌ No se encontraron iframes.")

    except Exception as e:
        print(f"🔥 Error: {e}")

    finally:
        print("\nCerrando...")
        driver.quit()

if __name__ == "__main__":
    main()
