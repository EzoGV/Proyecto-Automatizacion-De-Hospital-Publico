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

        self.btn_inicializar = ctk.CTkButton(self.frame_botones, text="🧱 1. Crear Tablas de Pacientes", fg_color="#2baf52", hover_color="#1e7a39", command=self.inicializar_tablas_hospital)
        self.btn_inicializar.pack(side="left", padx=20, pady=10, expand=True)

        self.btn_consultar = ctk.CTkButton(self.frame_botones, text="🔄 2. Ver Tablas Existentes", command=self.listar_tablas_y_datos)
        self.btn_consultar.pack(side="right", padx=20, pady=10, expand=True)

        # --- Zona de Reportes ---
        self.label_reporte = ctk.CTkLabel(self, text="Consola de Estado y Estructuras:", font=ctk.CTkFont(size=14, weight="bold"))
        self.label_reporte.pack(pady=(10, 0), anchor="w", padx=40)

        self.txt_resultados = ctk.CTkTextbox(self, width=620, height=320, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_resultados.pack(pady=10)

    def get_connection(self):
        # 1. Ruta absoluta de la carpeta de tu wallet (Asegúrate de que estén ahí cwallet.sso, tnsnames.ora, etc.)
        wallet_dir = r"C:\Users\Pc\Documents\GitHub\Proyecto-Automatizacion-De-Hospital-Publico\wallet"
        
        # 2. Credenciales de la base de datos en la nube
        usuario = "ADMIN"
        clave = "Pax.,ytrG231"
        
        # 3. La contraseña de seguridad con la que se descargó la Wallet desde Oracle Cloud
        # NOTA: Si no la recuerdas o no la definiste, por defecto suele ser la misma de la base de datos o una que tú creaste al descargarla.
        wallet_password = "Pax.,ytrG231" 

        # Conexión nativa robusta para modo Thin en la nube
        return oracledb.connect(
            user=usuario,
            password=clave,
            dsn="pipelinehibridohospital_high",
            config_dir=wallet_dir,
            wallet_location=wallet_dir,
            wallet_password=wallet_password
        )

    def inicializar_tablas_hospital(self):
        """Crea la estructura real del hospital con RUT, Nombre, etc."""
        self.txt_resultados.delete("0.0", "end")
        self.txt_resultados.insert("end", "⌛ Conectando a Oracle para inicializar la base de datos...\n")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Intentamos crear la tabla PACIENTES con las columnas que necesitas
            try:
                cursor.execute("""
                    CREATE TABLE pacientes (
                        rut_paciente VARCHAR2(12) PRIMARY KEY,
                        nombre_completo VARCHAR2(100),
                        edad NUMBER,
                        diagnostico VARCHAR2(200)
                    )
                """)
                self.txt_resultados.insert("end", "✅ Tabla 'PACIENTES' creada exitosamente con campos (rut_paciente, nombre_completo, edad, diagnostico).\n")
                
                # Insertamos un paciente de ejemplo para simular la carga del Data Engineer
                cursor.execute("INSERT INTO pacientes VALUES ('12.345.678-9', 'Juan Perez Jose', 45, 'Control Preventivo')")
                conn.commit()
                self.txt_resultados.insert("end", "📌 Registro de prueba insertado en 'PACIENTES'.\n")

            except oracledb.DatabaseError as e:
                error_obj, = e.args
                if error_obj.code == 955: # Error 955 significa que la tabla ya existía
                    self.txt_resultados.insert("end", "ℹ️ La tabla 'PACIENTES' ya existía en la base de datos.\n")
                else:
                    raise e

            cursor.close()
            conn.close()
            self.txt_resultados.insert("end", "\n👍 ¡Estructura base lista! Ahora presiona 'Ver Tablas Existentes'.")

        except Exception as e:
            self.txt_resultados.insert("end", f"\n❌ Error: {str(e)}")

    def listar_tablas_y_datos(self):
        """Muestra qué tablas existen en la base de datos de Oracle Cloud"""
        self.txt_resultados.delete("0.0", "end")
        
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Consulta maestra de Oracle para ver las tablas del usuario actual
            cursor.execute("SELECT table_name FROM user_tables ORDER BY table_name")
            tablas = cursor.fetchall()

            self.txt_resultados.insert("end", "📋 === TABLAS DETECTADAS EN TU BASE DE DATOS ===\n")
            if not tablas:
                self.txt_resultados.insert("end", "No hay tablas creadas por el usuario todavía.\n")
            else:
                for t in tablas:
                    self.txt_resultados.insert("end", f"🔹 Tabla encontrada: {t[0]}\n")
            
            # Si existe la tabla pacientes, mostramos su contenido para validar las columnas
            self.txt_resultados.insert("end", "\n🔍 === CONTENIDO DE LA TABLA 'PACIENTES' ===\n")
            try:
                cursor.execute("SELECT rut_paciente, nombre_completo, diagnostico FROM pacientes")
                pacientes = cursor.fetchall()
                if not pacientes:
                    self.txt_resultados.insert("end", "La tabla está vacía.\n")
                for p in pacientes:
                    self.txt_resultados.insert("end", f"🪪 RUT: {p[0]} | 👤 Nombre: {p[1]} | 🩺 Diagnóstico: {p[2]}\n")
            except oracledb.DatabaseError:
                self.txt_resultados.insert("end", "⚠️ No se pudo leer 'PACIENTES' (¿Ya presionaste el botón verde para crearla?).\n")

            cursor.close()
            conn.close()

        except Exception as e:
            self.txt_resultados.insert("end", f"❌ Error de conexión: {str(e)}")

if __name__ == "__main__":
    app = AppHospital()
    app.mainloop()