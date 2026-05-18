import oracledb
import os
from dotenv import load_dotenv
from pathlib import Path

# Cargar el .env forzadamente
raiz = Path(__file__).resolve().parent
load_dotenv(dotenv_path=raiz / '.env')

print("⏳ Intentando conectar a Oracle...")
try:
    conn = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "1521"),
        service_name=os.getenv("DB_SERVICE", "XE") # Ojo aquí, leerá el .env
    )
    print("✅ ¡BINGO! LA CONEXIÓN A ORACLE FUE UN ÉXITO TOTAL. Eres un crack.")
    conn.close()
except Exception as e:
    print(f"❌ Falló. El error exacto es:\n{e}")