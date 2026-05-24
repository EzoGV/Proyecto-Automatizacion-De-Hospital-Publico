import streamlit as st
import pandas as pd
import oracledb
import os

from dotenv import load_dotenv
from pathlib import Path

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Dashboard Ejecutivo",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

.card {
    background-color: #161B22;
    padding: 25px;
    border-radius: 18px;
    border: 1px solid #30363D;
}

.kpi-title {
    font-size: 14px;
    color: #9CA3AF;
}

.kpi-value {
    font-size: 38px;
    font-weight: bold;
    color: #60A5FA;
}

.section-title {
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CONEXIÓN ORACLE
# =========================================================

load_dotenv()

def get_connection():

    raiz = Path(__file__).resolve().parent.parent.parent.parent
    wallet_dir = str(raiz / "wallet")

    os.environ["TNS_ADMIN"] = wallet_dir

    connection = oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        dsn="pipelinehibridohospital_high",
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=os.getenv("DB_PASSWORD")
    )

    return connection

# =========================================================
# HEADER
# =========================================================

st.title("📊 Dashboard Ejecutivo Hospitalario")

st.caption(
    "Monitoreo operacional del pipeline clínico y observabilidad hospitalaria"
)

st.divider()

# =========================================================
# CONEXIÓN
# =========================================================

try:

    conn = get_connection()

    # =====================================================
    # KPIs
    # =====================================================

    pacientes = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM PACIENTES",
        conn
    )

    atenciones = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM ATENCIONES",
        conn
    )

    examenes = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM EXAMENES",
        conn
    )

    errores = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM errores_validacion",
        conn
    )

    # =====================================================
    # CARDS
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Pacientes",
            pacientes.iloc[0]["TOTAL"]
        )

    with col2:
        st.metric(
            "Atenciones",
            atenciones.iloc[0]["TOTAL"]
        )

    with col3:
        st.metric(
            "Exámenes",
            examenes.iloc[0]["TOTAL"]
        )

    #with col4:
    #    st.metric(
    #        "Errores ETL",
    #        errores.iloc[0]["TOTAL"]
    #    )

    st.divider()

    # =====================================================
    # GRÁFICO 1
    # =====================================================

    st.subheader("🏥 Atenciones por Tipo")

    atenciones_tipo = pd.read_sql("""
        SELECT
            tipo_atencion,
            COUNT(*) cantidad
        FROM ATENCIONES
        GROUP BY tipo_atencion
        ORDER BY cantidad DESC
    """, conn)

    st.bar_chart(
        atenciones_tipo.set_index("TIPO_ATENCION")
    )

    st.divider()

    # =====================================================
    # GRÁFICO 2
    # =====================================================

    st.subheader("🚨 Errores de Calidad de Datos")

    errores_tipo = pd.read_sql("""
        SELECT
            motivo_rechazo,
            COUNT(*) cantidad
        FROM CUARENTENA
        GROUP BY motivo_rechazo
        ORDER BY cantidad DESC
    """, conn)

    st.bar_chart(
        errores_tipo.set_index("MOTIVO_RECHAZO")
    )

    st.divider()

    # =====================================================
    # GRÁFICO 3
    # =====================================================

    st.subheader("💊 Medicamentos Más Prescritos")

    medicamentos = pd.read_sql("""
        SELECT
            codigo_minsal,
            COUNT(*) cantidad
        FROM MEDICAMENTOS
        GROUP BY codigo_minsal
        ORDER BY cantidad DESC
        FETCH FIRST 10 ROWS ONLY
    """, conn)

    st.bar_chart(
        medicamentos.set_index("CODIGO_MINSAL")
    )

    st.divider()

    # =====================================================
    # TABLA EJECUTIVA
    # =====================================================

    st.subheader("📋 Últimos Registros en Cuarentena")

    cuarentena = pd.read_sql("""
        SELECT *
        FROM CUARENTENA
        ORDER BY timestamp_validacion DESC
        FETCH FIRST 20 ROWS ONLY
    """, conn)

    st.dataframe(
        cuarentena,
        use_container_width=True
    )

    conn.close()

except Exception as e:

    st.error(f"Error Oracle Cloud: {e}")