from flask import Flask
from threading import Thread
import time
import logging

# Vypni logging Flasku, aby nebyl spam v konzoli
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')

@app.route('/')
def home():
    return "✅ Discord bot je online a běží! 🚀"

def run():
    # Použij port 8080 (Replit ho automaticky otevírá)
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    """
    Spustí Flask web server na pozadí.
    Tento server reaguje na HTTP požadavky,
    což zabrání Replit v uspání bota.
    """
    print("🔄 Spouštím keep-alive server...")
    
    # Vytvoř a spusť vlákno s Flask serverem
    server = Thread(target=run)
    server.daemon = True  # Toto vlákno se ukončí s hlavním programem
    server.start()
    
    # Počkej chvilku než se server rozjede
    time.sleep(2)
    print("✅ Keep-alive server běží na http://0.0.0.0:8080")