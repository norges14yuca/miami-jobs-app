import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def prueba_piloto():
    print("🤖 Iniciando prueba de sistemas...")
    
    # Esto descarga el driver necesario automáticamente
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # Iniciamos el navegador
    driver = webdriver.Chrome(service=service, options=options)
    
    # Vamos a la web de las escuelas
    print("🌍 Navegando a Dade Schools...")
    driver.get("https://apply.dadeschools.net/search/?q=&sortColumn=referencedate&sortDirection=asc")
    
    print("✅ ¡Éxito! La página se abrió. Esperando 5 segundos...")
    time.sleep(5)
    
    print("👋 Cerrando navegador.")
    driver.quit()

if __name__ == "__main__":
    prueba_piloto()
