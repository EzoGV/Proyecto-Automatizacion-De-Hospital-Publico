import customtkinter as ctk
import oracledb
import os

# Configuración visual de la ventana
ctk.set_appearance_mode("Dark")  # Forzamos el modo oscuro que se ve genial
ctk.set_default_color_theme("blue")

class AppHospital(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🏥 Sistema Hospitalario - Control de Tablas DevOps")
        self.geometry("700x550")

        # Título Principal
        self.titulo = ctk.CTkLabel(self, text="Panel de Control de Datos (Oracle 23c)", font=ctk.CTkFont(size=22, weight="bold"))
        self.titulo.pack(pady=15)

        # --- Zona de Botones ---
        self.frame_botones = ctk.CTkFrame(self)
        self.frame_botones.pack(pady=10, fill="x", padx=40)

        self.btn_inicializar = ctk.CTkButton(self.frame_botones, text="🧱 1. Crear Estructura Base Hospital", fg_color="#2baf52", hover_color="#1e7a39", command=self.inicializar_tablas_hospital)
        self.btn_inicializar.pack(side="left", padx=20, pady=10, expand=True)

        self.btn_consultar = ctk.CTkButton(self.frame_botones, text="🔄 2. Ver Tablas Existentes", command=self.listar_tablas_y_datos)
        self.btn_consultar.pack(side="right", padx=20, pady=10, expand=True)

        # --- Zona de Reportes ---
        self.label_reporte = ctk.CTkLabel(self, text="Consola de Estado y Estructuras:", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_reporte.pack(pady=(10, 0), anchor="w", padx=40)

        self.txt_resultados = ctk.CTkTextbox(self, width=620, height=320, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_resultados.pack(pady=10)

    def get_connection(self):
        """
        CONEXIÓN EN MODO PRODUCCIÓN (NUBE OCI)
        Lee dinámicamente la Wallet sin importar en qué computadora se ejecute.
        """
        import os
        
        # 1. Detecta automáticamente la carpeta donde está guardado este archivo 'interfaz.py'
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 2. Si tu archivo está en la raíz, calcula la ruta hacia la carpeta 'wallet'
        #    (Asegúrate de tener la carpeta 'wallet' con sus archivos al lado de interfaz.py)
        wallet_dir = os.path.join(base_dir, "wallet")
        
        # En caso de que ejecutes desde una subcarpeta (ej: 'src/'), descomenta la línea de abajo:
        wallet_dir = os.path.join(os.path.dirname(base_dir), "wallet")
        
        # 3. Configurar variables de entorno dinámicas para la Wallet
        os.environ["TNS_ADMIN"] = wallet_dir
        
        # 4. Credenciales de producción en la nube
        DB_USER = os.getenv("DB_USER", "ADMIN")
        DB_PASSWORD = os.getenv("DB_PASSWORD")
        dsn_nube = "pipelinehibridohospital_high"

        # Conexión nativa robusta en modo Thin para la nube
        return oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=dsn_nube,
            config_dir=wallet_dir,
            wallet_location=wallet_dir,
            wallet_password=DB_PASSWORD  # Usamos la misma contraseña de la base de datos
        )

    def inicializar_tablas_hospital(self):
        """Crea la estructura del hospital según la documentación del pipeline"""
        self.txt_resultados.delete("0.0", "end")
        self.txt_resultados.insert("end", "⌛ Conectando a Oracle local para inicializar tablas...\n")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # 1. Tabla PACIENTES (Datos Demográficos)
            try:
                cursor.execute("""
                    CREATE TABLE PACIENTES (
                        rut_paciente VARCHAR2(12) PRIMARY KEY,
                        nombre_completo VARCHAR2(150) NOT NULL,
                        fecha_nacimiento DATE NOT NULL,
                        sexo CHAR(1) CHECK (sexo IN ('M', 'F', 'I')),
                        prevision VARCHAR2(30)
                    )
                """)
                self.txt_resultados.insert("end", "✅ Tabla 'PACIENTES' creada.\n")
                
                # Insertar registro inicial estructurado correctamente
                cursor.execute("""
                    INSERT INTO PACIENTES VALUES (
                        '12.345.678-9', 'Juan Perez Jose', TO_DATE('1980-05-15', 'YYYY-MM-DD'), 'M', 'FONASA'
                    )
                """)
                conn.commit()
                self.txt_resultados.insert("end", "📌 Paciente de prueba insertado.\n")
            except oracledb.DatabaseError as e:
                if e.args[0].code == 955: self.txt_resultados.insert("end", "ℹ️ Tabla 'PACIENTES' ya existía.\n")
                else: raise e

            # 2. Tabla ATENCIONES (Historial Clínico)
            try:
                cursor.execute("""
                    CREATE TABLE ATENCIONES (
                        id_atencion VARCHAR2(36) PRIMARY KEY,
                        rut_paciente VARCHAR2(12) REFERENCES PACIENTES(rut_paciente),
                        fecha_atencion DATE NOT NULL,
                        diagnostico VARCHAR2(200)
                    )
                """)
                self.txt_resultados.insert("end", "✅ Tabla 'ATENCIONES' creada.\n")
            except oracledb.DatabaseError as e:
                if e.args[0].code == 955: self.txt_resultados.insert("end", "ℹ️ Tabla 'ATENCIONES' ya existía.\n")
                else: raise e

            # 3. Tabla LOGS DE AUDITORÍA (Métrica de Cobertura de tu doc técnica)
            try:
                cursor.execute("""
                    CREATE TABLE AUDIT_LOG (
                        id_log NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        etapa_pipeline VARCHAR2(50),
                        kpi_nombre VARCHAR2(50),
                        valor_calculado VARCHAR2(20),
                        estado VARCHAR2(15),
                        timestamp_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                self.txt_resultados.insert("end", "✅ Tabla 'AUDIT_LOG' creada para auditorías DataOps.\n")
            except oracledb.DatabaseError as e:
                if e.args[0].code == 955: self.txt_resultados.insert("end", "ℹ️ Tabla 'AUDIT_LOG' ya existía.\n")
                else: raise e

            cursor.close()
            conn.close()
            self.txt_resultados.insert("end", "\n👍 ¡Entorno base configurado y listo en tu Docker!")

        except Exception as e:
            self.txt_resultados.insert("end", f"\n❌ Error al inicializar: {str(e)}")

    def listar_tablas_y_datos(self):
        """Muestra qué tablas existen en el entorno actual"""
        self.txt_resultados.delete("0.0", "end")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
            tablas = cursor.fetchall()

            self.txt_resultados.insert("end", "📋 === TABLAS DETECTADAS ===\n")
            if not tablas:
                self.txt_resultados.insert("end", "No hay tablas creadas por el usuario todavía.\n")
            else:
                for t in tablas:
                    self.txt_resultados.insert("end", f"🔹 [{t[0]}]\n")
            
            # Consultar contenido base de pacientes
            self.txt_resultados.insert("end", "\n🔍 === VISTA RÁPIDA: PACIENTES ===\n")
            try:
                cursor.execute("SELECT rut_paciente, nombre_completo, prevision FROM pacientes")
                pacientes = cursor.fetchall()
                if not pacientes:
                    self.txt_resultados.insert("end", "La tabla está vacía.\n")
                for p in pacientes:
                    self.txt_resultados.insert("end", f"🪪 RUT: {p[0]} | 👤 Nombre: {p[1]} | 🏥 Previsión: {p[2]}\n")
            except oracledb.DatabaseError:
                self.txt_resultados.insert("end", "⚠️ No se pudo leer la tabla 'PACIENTES'.\n")

            cursor.close()
            conn.close()

        except Exception as e:
            self.txt_resultados.insert("end", f"❌ Error de conexión: {str(e)}")

if __name__ == "__main__":
    app = AppHospital()
    app.mainloop()