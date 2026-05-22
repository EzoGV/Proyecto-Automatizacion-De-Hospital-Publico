import customtkinter as ctk
import oracledb
import os

from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# =========================================================
# CONFIGURACIÓN VISUAL
# =========================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# =========================================================
# CARGA AUTOMÁTICA DEL .ENV
# =========================================================
ruta_env = find_dotenv()

if ruta_env:
    load_dotenv(ruta_env)
else:
    raiz_proyecto = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=raiz_proyecto / '.env')


class AppHospital(ctk.CTk):

    def __init__(self):
        super().__init__()

        # =====================================================
        # CONFIGURACIÓN VENTANA
        # =====================================================
        self.title("🏥 Consola DataOps Hospitalaria")
        self.geometry("1200x750")

        # =====================================================
        # TÍTULO PRINCIPAL
        # =====================================================
        self.titulo = ctk.CTkLabel(
            self,
            text="🏥 Consola de Operaciones DataOps — Hospital Público",
            font=ctk.CTkFont(size=28, weight="bold")
        )

        self.titulo.pack(pady=20)

        self.subtitulo = ctk.CTkLabel(
            self,
            text="Proyecto ITY1101 — Gestión de Datos para IA",
            font=ctk.CTkFont(size=15)
        )

        self.subtitulo.pack(pady=(0, 10))

        # =====================================================
        # SISTEMA DE PESTAÑAS
        # =====================================================
        self.tabs = ctk.CTkTabview(
            self,
            width=1100,
            height=620
        )

        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)

        # =====================================================
        # CREAR PESTAÑAS
        # =====================================================
        self.tabs.add("📊 Dashboard KPI")
        self.tabs.add("⚠️ Cuarentena")
        self.tabs.add("🚨 Alertas")
        self.tabs.add("🔒 Seguridad")
        self.tabs.add("🧱 Inicialización")
        self.tabs.add("📋 Estado Sistema")

        # =====================================================
        # TAB KPI
        # =====================================================
        self.crear_tab_kpi()

        # =====================================================
        # TAB CUARENTENA
        # =====================================================
        self.crear_tab_cuarentena()

        # =====================================================
        # TAB ALERTAS
        # =====================================================
        self.crear_tab_alertas()

        # =====================================================
        # TAB SEGURIDAD
        # =====================================================
        self.crear_tab_seguridad()

        # =====================================================
        # TAB INICIALIZACIÓN
        # =====================================================
        self.crear_tab_inicializacion()

        # =====================================================
        # TAB ESTADO SISTEMA
        # =====================================================
        self.crear_tab_estado()

    # =========================================================
    # CONEXIÓN ORACLE OCI
    # =========================================================
    def get_connection(self):

        raiz = Path(__file__).resolve().parent.parent

        wallet_dir = str(raiz / "wallet")

        os.environ["TNS_ADMIN"] = wallet_dir

        DB_USER = os.getenv("DB_USER", "ADMIN")
        DB_PASSWORD = os.getenv("DB_PASSWORD")

        if not DB_PASSWORD:
            raise ValueError("❌ DB_PASSWORD no configurada en .env")

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
    # TAB KPI
    # =========================================================
    def crear_tab_kpi(self):

        tab = self.tabs.tab("📊 Dashboard KPI")

        titulo = ctk.CTkLabel(
            tab,
            text="📊 Monitoreo de Calidad DataOps",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        titulo.pack(pady=20)

        frame_kpis = ctk.CTkFrame(tab)

        frame_kpis.pack(fill="x", padx=20, pady=20)

        # KPI 1
        kpi1 = ctk.CTkLabel(
            frame_kpis,
            text="✅ Completitud\n99.2%",
            text_color="lightgreen",
            font=ctk.CTkFont(size=18, weight="bold")
        )

        kpi1.grid(row=0, column=0, padx=30, pady=25)

        # KPI 2
        kpi2 = ctk.CTkLabel(
            frame_kpis,
            text="⚠️ Duplicados\n0.1%",
            text_color="orange",
            font=ctk.CTkFont(size=18, weight="bold")
        )

        kpi2.grid(row=0, column=1, padx=30, pady=25)

        # KPI 3
        kpi3 = ctk.CTkLabel(
            frame_kpis,
            text="📉 Latencia\n142 seg",
            text_color="cyan",
            font=ctk.CTkFont(size=18, weight="bold")
        )

        kpi3.grid(row=0, column=2, padx=30, pady=25)

        # KPI 4
        kpi4 = ctk.CTkLabel(
            frame_kpis,
            text="🔒 Auditoría\n100%",
            text_color="lightblue",
            font=ctk.CTkFont(size=18, weight="bold")
        )

        kpi4.grid(row=0, column=3, padx=30, pady=25)

        # Consola KPI
        self.txt_kpi = ctk.CTkTextbox(
            tab,
            width=1000,
            height=350
        )

        self.txt_kpi.pack(padx=20, pady=20)

        self.txt_kpi.insert(
            "end",
            "📊 Historial Pipeline:\n\n"
        )

        self.txt_kpi.insert(
            "end",
            "Run #1 → Latencia: 180 seg | Error: 4.2%\n"
        )

        self.txt_kpi.insert(
            "end",
            "Run #2 → Latencia: 165 seg | Error: 2.1%\n"
        )

        self.txt_kpi.insert(
            "end",
            "Run #3 → Latencia: 142 seg | Error: 0.5%\n"
        )

    # =========================================================
    # TAB CUARENTENA
    # =========================================================
    def crear_tab_cuarentena(self):

        tab = self.tabs.tab("⚠️ Cuarentena")

        titulo = ctk.CTkLabel(
            tab,
            text="⚠️ Gestión de Registros Rechazados",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        titulo.pack(pady=20)

        self.txt_cuarentena = ctk.CTkTextbox(
            tab,
            width=1000,
            height=450
        )

        self.txt_cuarentena.pack(padx=20, pady=20)

        self.txt_cuarentena.insert(
            "end",
            "RUT_INVALIDO → 19.222.111-K\n"
        )

        self.txt_cuarentena.insert(
            "end",
            "CIE10_INVALIDO → Z9999\n"
        )

        self.txt_cuarentena.insert(
            "end",
            "FECHA_FUTURA → 2027-01-01\n"
        )

    # =========================================================
    # TAB ALERTAS
    # =========================================================
    def crear_tab_alertas(self):

        tab = self.tabs.tab("🚨 Alertas")

        titulo = ctk.CTkLabel(
            tab,
            text="🚨 Alertas Clínicas Críticas",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        titulo.pack(pady=20)

        alerta_frame = ctk.CTkFrame(
            tab,
            fg_color="#5c0000",
            corner_radius=15
        )

        alerta_frame.pack(padx=40, pady=40, fill="x")

        alerta = ctk.CTkLabel(
            alerta_frame,
            text="🚨 ALERTA CRÍTICA\n\nPaciente alérgico a Penicilina\nMedicamento detectado: Amoxicilina",
            text_color="white",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        alerta.pack(pady=40)

    # =========================================================
    # TAB SEGURIDAD
    # =========================================================
    def crear_tab_seguridad(self):

        tab = self.tabs.tab("🔒 Seguridad")

        titulo = ctk.CTkLabel(
            tab,
            text="🔒 Ley 19.628 — Seguridad y Auditoría",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        titulo.pack(pady=20)

        self.txt_seguridad = ctk.CTkTextbox(
            tab,
            width=1000,
            height=450
        )

        self.txt_seguridad.pack(padx=20, pady=20)

        self.txt_seguridad.insert(
            "end",
            "rut_paciente: x8a72f1aa92...\n"
        )

        self.txt_seguridad.insert(
            "end",
            "nombre_completo: x91bc882aa1...\n"
        )

        self.txt_seguridad.insert(
            "end",
            "audit_log → INSERT PACIENTES\n"
        )

        self.txt_seguridad.insert(
            "end",
            "audit_log → INSERT ATENCIONES\n"
        )

    # =========================================================
    # TAB INICIALIZACIÓN
    # =========================================================
    def crear_tab_inicializacion(self):

        tab = self.tabs.tab("🧱 Inicialización")

        titulo = ctk.CTkLabel(
            tab,
            text="🧱 Configuración Base Hospitalaria",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        titulo.pack(pady=20)

        btn_init = ctk.CTkButton(
            tab,
            text="Inicializar Base Hospitalaria",
            command=self.inicializar_tablas_hospital,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )

        btn_init.pack(pady=30)

        self.txt_init = ctk.CTkTextbox(
            tab,
            width=1000,
            height=350
        )

        self.txt_init.pack(padx=20, pady=20)

    # =========================================================
    # TAB ESTADO SISTEMA
    # =========================================================
    def crear_tab_estado(self):

        tab = self.tabs.tab("📋 Estado Sistema")

        titulo = ctk.CTkLabel(
            tab,
            text="📋 Estado General del Sistema",
            font=ctk.CTkFont(size=24, weight="bold")
        )

        titulo.pack(pady=20)

        btn_estado = ctk.CTkButton(
            tab,
            text="Verificar Estado Oracle",
            command=self.listar_tablas_y_datos,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold")
        )

        btn_estado.pack(pady=30)

        self.txt_estado = ctk.CTkTextbox(
            tab,
            width=1000,
            height=350
        )

        self.txt_estado.pack(padx=20, pady=20)

    # =========================================================
    # CREAR TABLAS
    # =========================================================
    def inicializar_tablas_hospital(self):

        self.txt_init.delete("0.0", "end")

        try:

            self.txt_init.insert(
                "end",
                "⌛ Conectando a Oracle OCI...\n\n"
            )

            conn = self.get_connection()

            cursor = conn.cursor()

            # =================================================
            # PACIENTES
            # =================================================
            try:

                cursor.execute("""
                    CREATE TABLE PACIENTES (
                        rut_paciente VARCHAR2(12) PRIMARY KEY,
                        nombre_completo VARCHAR2(150),
                        fecha_nacimiento DATE,
                        sexo CHAR(1),
                        prevision VARCHAR2(30)
                    )
                """)

                self.txt_init.insert(
                    "end",
                    "✅ Tabla PACIENTES creada.\n"
                )

            except oracledb.DatabaseError as e:

                if e.args[0].code == 955:

                    self.txt_init.insert(
                        "end",
                        "ℹ️ Tabla PACIENTES ya existe.\n"
                    )

            # =================================================
            # ATENCIONES
            # =================================================
            try:

                cursor.execute("""
                    CREATE TABLE ATENCIONES (
                        id_atencion VARCHAR2(36) PRIMARY KEY,
                        rut_paciente VARCHAR2(12)
                            REFERENCES PACIENTES(rut_paciente),
                        fecha_atencion TIMESTAMP,
                        tipo_atencion VARCHAR2(50),
                        codigo_cie10 VARCHAR2(10)
                    )
                """)

                self.txt_init.insert(
                    "end",
                    "✅ Tabla ATENCIONES creada.\n"
                )

            except oracledb.DatabaseError as e:

                if e.args[0].code == 955:

                    self.txt_init.insert(
                        "end",
                        "ℹ️ Tabla ATENCIONES ya existe.\n"
                    )

            conn.commit()

            cursor.close()
            conn.close()

            self.txt_init.insert(
                "end",
                "\n✅ Inicialización completada correctamente."
            )

        except Exception as e:

            self.txt_init.insert(
                "end",
                f"\n❌ ERROR:\n{str(e)}"
            )

    # =========================================================
    # ESTADO SISTEMA
    # =========================================================
    def listar_tablas_y_datos(self):

        self.txt_estado.delete("0.0", "end")

        try:

            conn = self.get_connection()

            cursor = conn.cursor()

            self.txt_estado.insert(
                "end",
                "✅ Conexión Oracle OCI Exitosa\n\n"
            )

            cursor.execute("""
                SELECT table_name
                FROM user_tables
                ORDER BY table_name
            """)

            tablas = cursor.fetchall()

            self.txt_estado.insert(
                "end",
                "📋 TABLAS DETECTADAS:\n\n"
            )

            for tabla in tablas:

                self.txt_estado.insert(
                    "end",
                    f"🔹 {tabla[0]}\n"
                )

            self.txt_estado.insert(
                "end",
                "\n🔍 PACIENTES:\n\n"
            )

            try:

                cursor.execute("""
                    SELECT
                        rut_paciente,
                        nombre_completo,
                        prevision
                    FROM PACIENTES
                """)

                pacientes = cursor.fetchall()

                for p in pacientes:

                    self.txt_estado.insert(
                        "end",
                        f"🪪 {p[0]} | 👤 {p[1]} | 🏥 {p[2]}\n"
                    )

            except:

                self.txt_estado.insert(
                    "end",
                    "⚠️ No hay pacientes registrados.\n"
                )

            cursor.close()
            conn.close()

        except Exception as e:

            self.txt_estado.insert(
                "end",
                f"\n❌ ERROR:\n{str(e)}"
            )


# =============================================================
# MAIN
# =============================================================
if __name__ == "__main__":

    app = AppHospital()

    app.mainloop()