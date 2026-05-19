import os
import oracledb
from dotenv import load_dotenv

# 1. Cargar las credenciales de tu archivo .env
load_dotenv()

def insertar_dato_prueba():
    try:
        print("⏳ Conectando a Oracle...")
        # Conexión forzando el modo Thin con oracledb
        connection = oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "1521"),
            service_name=os.getenv("DB_SERVICE", "XE") # Ojo aquí, leerá el .env
        )
        cursor = connection.cursor()
        print("✅ Conexión exitosa. Preparando el INSERT...")

        # --- PASO 1: CREAR LA TABLA PRIMERO ---
        print("🔨 Verificando/Creando la tabla PACIENTES...")
        try:
            cursor.execute("""
                CREATE TABLE PACIENTES (
                    rut_paciente VARCHAR2(12) PRIMARY KEY,
                    nombre_completo VARCHAR2(150) NOT NULL,
                    fecha_nacimiento DATE NOT NULL,
                    sexo CHAR(1) NOT NULL,
                    prevision VARCHAR2(30) NOT NULL
                )
            """)
            print("✅ Tabla PACIENTES creada desde cero con éxito.")
        except oracledb.DatabaseError as e:
            error_obj, = e.args
            if error_obj.code == 955:
                # El error 955 significa que la tabla ya existía, lo cual está bien
                print("ℹ️ La tabla PACIENTES ya existía. Continuando...")
            else:
                raise # Si es otro error, lo lanzamos

        # --- PASO 2: INSERTAR EL DATO ---
        sql = """
            INSERT INTO PACIENTES (rut_paciente, nombre_completo, fecha_nacimiento, sexo, prevision)
            VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), :4, :5)
        """
        datos_prueba = ["99.999.999-9", "Paciente de Prueba DataOps", "1990-05-20", "M", "FONASA"]
        
        cursor.execute(sql, datos_prueba)
        connection.commit()
        print("✅ ¡Dato insertado y guardado correctamente en la BD!")
        
        # --- PASO 3: LEER EL DATO PARA CORROBORAR ---
        cursor.execute("SELECT rut_paciente, nombre_completo FROM PACIENTES WHERE rut_paciente = '99.999.999-9'")
        fila = cursor.fetchone()
        print(f"🔍 Comprobación en vivo desde Oracle: {fila}")

    except Exception as e:
        print(f"❌ Ocurrió un error: {e}")
        # Si algo falla, deshacemos la operación para no ensuciar la BD
        if 'connection' in locals():
            connection.rollback()
            print("⏪ Rollback ejecutado preventivamente.")
    finally:
        # --- PASO 4: CERRAR CURSORES Y CONEXIONES ---
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
            print("🔒 Conexión cerrada.")

if __name__ == "__main__":
    insertar_dato_prueba()