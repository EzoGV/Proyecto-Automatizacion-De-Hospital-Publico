import os
import oracledb
from dotenv import load_dotenv
from pathlib import Path

# ==========================================
# CARGAR .env
# ==========================================

load_dotenv()

# ==========================================
# CONEXIÓN ORACLE
# ==========================================

def get_connection():

    raiz = Path(__file__).resolve().parent.parent.parent

    wallet_dir = str(raiz / "wallet")

    os.environ["TNS_ADMIN"] = wallet_dir

    DB_USER = os.getenv("DB_USER", "ADMIN")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    connection = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn="pipelinehibridohospital_high",
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=DB_PASSWORD
    )

    return connection


# ==========================================
# EJECUCIÓN SQL
# ==========================================

conn = get_connection()
cursor = conn.cursor()

ruta_sql = Path(__file__).parent / "01_tablas_frontend.sql"

with open(ruta_sql, "r", encoding="utf-8") as archivo:
    sql_completo = archivo.read()

bloques = sql_completo.split(";")

for bloque in bloques:

    if bloque.strip():

        try:
            cursor.execute(bloque)
            print("✅ Ejecutado")

        except Exception as e:
            print(f"⚠️ Error: {e}")

conn.commit()

print("\n🚀 Tablas frontend creadas correctamente")

cursor.close()
conn.close()