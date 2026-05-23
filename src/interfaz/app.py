import streamlit as st

st.set_page_config(
    page_title="Sistema Hospitalario Inteligente",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CSS PERSONALIZADO
# =========================

st.markdown("""
<style>

/* Fondo principal */
.stApp {
    background-color: #0B1120;
    color: white;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #1F2937;
}

/* Inputs */
.stTextInput input {
    background-color: #1F2937;
    color: white;
    border-radius: 10px;
    border: 1px solid #374151;
}

/* Selectbox */
.stSelectbox div[data-baseweb="select"] {
    background-color: #1F2937;
    border-radius: 10px;
}

/* Botón */
.stButton button {
    background: linear-gradient(90deg, #2563EB, #1D4ED8);
    color: white;
    border-radius: 10px;
    height: 50px;
    width: 100%;
    border: none;
    font-size: 16px;
    font-weight: bold;
}

/* Cards */
.card {
    background-color: #111827;
    padding: 2rem;
    border-radius: 20px;
    border: 1px solid #1F2937;
    box-shadow: 0px 0px 20px rgba(0,0,0,0.3);
}

/* Títulos */
.main-title {
    font-size: 42px;
    font-weight: bold;
    color: white;
}

.subtitle {
    color: #9CA3AF;
    font-size: 18px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================

with st.sidebar:
    st.markdown("# 🏥 Hospital Intelligence")
    st.markdown("---")

    st.markdown("---")

    st.markdown("### Estado Sistema")
    st.write("🟢 Oracle Cloud")
    st.write("🟢 Validaciones")
    st.write("🟢 Trazabilidad")

# =========================
# HEADER
# =========================

st.markdown(
    """
    <div class="main-title">
        Sistema Hospitalario Inteligente
    </div>

    <div class="subtitle">
        Oracle Cloud Infrastructure + Pipeline Medallion Architecture
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# LOGIN CARD
# =========================

col1, col2, col3 = st.columns([1,2,1])

with col2:

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("## 🔐 Acceso Plataforma")

    usuario = st.text_input("Usuario")

    password = st.text_input(
        "Contraseña",
        type="password"
    )

    rol = st.selectbox(
        "Seleccionar Rol",
        [
            "Doctor / Personal Médico",
            "Auditoría / Trazabilidad"
        ]
    )

    if st.button("Ingresar al Sistema"):

        if rol == "Doctor / Personal Médico":
            st.switch_page("pages/doctor.py")

        else:
            st.switch_page("pages/auditoria.py")
        
    if st.button("📊 Dashboard Ejecutivo"):
        st.switch_page("pages/dashboard.py")

    st.markdown("</div>", unsafe_allow_html=True)