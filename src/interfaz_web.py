import streamlit as st
import pandas as pd
import oracledb
import os

from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Hospital DataOps",
    page_icon="🏥",
    layout="wide"
)

# =========================================================
# CARGA .ENV
# =========================================================

ruta_env = find_dotenv()

if ruta_env:
    load_dotenv(ruta_env)
else:
    raiz = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=raiz / ".env")

# =========================================================
# CONEXIÓN ORACLE OCI
# =========================================================

@st.cache_resource
def get_connection():

    raiz = Path(__file__).resolve().parent.parent
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

# =========================================================
# FUNCIONES SQL
# =========================================================

def obtener_total_pacientes():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM PACIENTES
    """)

    total = cursor.fetchone()[0]

    cursor.close()

    return total


def obtener_total_atenciones():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM ATENCIONES
    """)

    total = cursor.fetchone()[0]

    cursor.close()

    return total


def obtener_total_alergias():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM ALERGIAS
    """)

    total = cursor.fetchone()[0]

    cursor.close()

    return total

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("🏥 Hospital App")

pagina = st.sidebar.radio(
    "Navegación",
    [
        "Dashboard",
        "Pacientes",
        "Atenciones",
        "Auditoría"
    ]
)

# =========================================================
# DASHBOARD
# =========================================================

if pagina == "Dashboard":

    st.title("📊 Dashboard DataOps Clínico")

    col1, col2, col3 = st.columns(3)

    try:
        total_pacientes = obtener_total_pacientes()
        total_atenciones = obtener_total_atenciones()
        total_alergias = obtener_total_alergias()

        col1.metric(
            "Pacientes",
            total_pacientes
        )

        col2.metric(
            "Atenciones",
            total_atenciones
        )

        col3.metric(
            "Alergias",
            total_alergias
        )

        st.success("✅ Conexión exitosa con Oracle Cloud")

    except Exception as e:

        st.error(f"❌ Error Oracle: {e}")

# =========================================================
# PACIENTES
# =========================================================

elif pagina == "Pacientes":

    st.title("👤 Pacientes")

    try:

        conn = get_connection()

        query = """
            SELECT
                rut_paciente,
                nombre_completo,
                prevision
            FROM PACIENTES
        """

        df = pd.read_sql(query, conn)

        st.dataframe(
            df,
            use_container_width=True
        )

    except Exception as e:

        st.error(f"❌ Error: {e}")

# =========================================================
# ATENCIONES
# =========================================================

elif pagina == "Atenciones":

    st.title("🩺 Atenciones")

    try:

        conn = get_connection()

        query = """
            SELECT
                id_atencion,
                rut_paciente,
                tipo_atencion
            FROM ATENCIONES
        """

        df = pd.read_sql(query, conn)

        st.dataframe(
            df,
            use_container_width=True
        )

    except Exception as e:

        st.error(f"❌ Error: {e}")

# =========================================================
# AUDITORÍA
# =========================================================

elif pagina == "Auditoría":

    st.title("🔒 Auditoría")

    st.info("Módulo de auditoría y seguridad clínica.")