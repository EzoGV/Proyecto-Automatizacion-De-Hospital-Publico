import streamlit as st
import pandas as pd
import oracledb
import os

from dotenv import load_dotenv
from pathlib import Path

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Auditoría Hospitalaria",
    page_icon="🛡️",
    layout="wide"
)

# =========================================================
# CSS PROFESIONAL
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #0E1117;
    color: white;
}

.kpi-card {
    background-color: #161B22;
    padding: 25px;
    border-radius: 15px;
    border: 1px solid #30363D;
    text-align: center;
}

.kpi-title {
    font-size: 15px;
    color: #9CA3AF;
}

.kpi-value {
    font-size: 36px;
    font-weight: bold;
    color: #60A5FA;
}

.section-box {
    background-color: #161B22;
    padding: 20px;
    border-radius: 15px;
    border: 1px solid #30363D;
    margin-bottom: 25px;
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

st.markdown("# 🛡️ Centro de Auditoría")
st.caption(
    "Monitoreo de calidad, trazabilidad y observabilidad del pipeline hospitalario"
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

    total_pacientes = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM PACIENTES",
        conn
    )

    total_atenciones = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM ATENCIONES",
        conn
    )

    #total_errores = pd.read_sql(
    #    "SELECT COUNT(*) TOTAL FROM errores_validacion",
    #    conn
    #)

    total_cuarentena = pd.read_sql(
        "SELECT COUNT(*) TOTAL FROM CUARENTENA",
        conn
    )

    # =====================================================
    # CARDS KPI
    # =====================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Pacientes</div>
            <div class="kpi-value">
                {total_pacientes.iloc[0]["TOTAL"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Atenciones</div>
            <div class="kpi-value">
                {total_atenciones.iloc[0]["TOTAL"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

   # with col3:
    #    st.markdown(f"""
    #    <div class="kpi-card">
    #        <div class="kpi-title">Errores Validación</div>
    #        <div class="kpi-value">
    #            {total_errores.iloc[0]["TOTAL"]}
    #        </div>
    #    </div>
    #    """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Registros Cuarentena</div>
            <div class="kpi-value">
                {total_cuarentena.iloc[0]["TOTAL"]}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # =====================================================
    # ERRORES VALIDACIÓN
    # =====================================================

    #st.markdown("## ⚠️ Errores de Validación")

    #errores = pd.read_sql("""
    #    SELECT *
    #    FROM errores_validacion
    #    ORDER BY fila_id DESC
    #""", conn)

    #st.dataframe(
    #    errores,
    #    use_container_width=True,
    #    height=300
    #)

    #st.divider()

    # =====================================================
    # CUARENTENA
    # =====================================================

    st.markdown("## 🚨 Registros en Cuarentena")

    cuarentena = pd.read_sql("""
        SELECT *
        FROM CUARENTENA
        ORDER BY timestamp_validacion DESC
    """, conn)

    st.dataframe(
        cuarentena,
        use_container_width=True,
        height=300
    )

    st.divider()

    # =====================================================
    # TOP ERRORES
    # =====================================================

    st.markdown("## 📊 Top Motivos de Rechazo")

    top_errores = pd.read_sql("""
        SELECT
            motivo_rechazo,
            COUNT(*) cantidad
        FROM CUARENTENA
        GROUP BY motivo_rechazo
        ORDER BY cantidad DESC
    """, conn)

    st.bar_chart(
        top_errores.set_index("MOTIVO_RECHAZO")
    )

    conn.close()

except Exception as e:

    st.error(f"Error Oracle Cloud: {e}")