import streamlit as st
import pandas as pd
import oracledb
import os
from dotenv import load_dotenv
from pathlib import Path

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Panel Médico",
    page_icon="🩺",
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

.titulo {
    font-size: 42px;
    font-weight: 700;
    color: white;
}

.subtitulo {
    font-size: 18px;
    color: #9CA3AF;
}

.bloque {
    background-color: #161B22;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 20px;
    border: 1px solid #30363D;
}

.metric-card {
    background-color: #1C2333;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    border: 1px solid #2E3A59;
}

.metric-title {
    font-size: 15px;
    color: #9CA3AF;
}

.metric-value {
    font-size: 28px;
    font-weight: bold;
    color: #4ADE80;
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

st.markdown('<p class="titulo">🩺 Panel Médico</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitulo">Atención clínica y seguimiento de pacientes</p>',
    unsafe_allow_html=True
)

st.divider()

# =========================================================
# BUSCADOR PACIENTE
# =========================================================

st.markdown("## 🔎 Buscar Paciente")

rut_busqueda = st.text_input(
    "Ingrese RUT del paciente",
    placeholder="12.345.678-9"
)

# =========================================================
# CONSULTA
# =========================================================

if st.button("Buscar Información"):

    if rut_busqueda.strip() == "":
        st.warning("Debe ingresar un RUT.")
        st.stop()

    try:

        conn = get_connection()

        query = """
        SELECT
            p.rut_paciente,
            p.nombre_completo,
            p.fecha_nacimiento,
            p.sexo,
            p.prevision,
            a.id_atencion,
            a.fecha_atencion,
            a.tipo_atencion,
            a.codigo_cie10
        FROM pacientes p
        LEFT JOIN atenciones a
            ON p.rut_paciente = a.rut_paciente
        WHERE p.rut_paciente = :rut
        ORDER BY a.fecha_atencion DESC
        """

        df = pd.read_sql(query, conn, params={"rut": rut_busqueda})

        conn.close()

        if df.empty:
            st.error("Paciente no encontrado.")
        else:

            paciente = df.iloc[0]

            # =================================================
            # DATOS PACIENTE
            # =================================================

            st.markdown("## 👤 Información del Paciente")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Paciente</div>
                    <div class="metric-value">{paciente['NOMBRE_COMPLETO']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Previsión</div>
                    <div class="metric-value">{paciente['PREVISION']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-title">Sexo</div>
                    <div class="metric-value">{paciente['SEXO']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # =================================================
            # HISTORIAL
            # =================================================

            st.markdown("## 🏥 Historial Clínico")

            st.dataframe(
                df[[
                    "ID_ATENCION",
                    "FECHA_ATENCION",
                    "TIPO_ATENCION",
                    "CODIGO_CIE10"
                ]],
                use_container_width=True
            )

    except Exception as e:
        st.error(f"Error conexión Oracle: {e}")