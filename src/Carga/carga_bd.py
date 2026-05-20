# src/Carga/04_carga.py
import pandas as pd
import os
import oracledb
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

ruta_logs = "./RegistroLogs"
if not os.path.exists(ruta_logs):
    os.makedirs(ruta_logs)

# Ahora sí le decimos al logging que guarde el archivo DENTRO de esa carpeta
archivo_log = os.path.join(ruta_logs, 'pipeline_ejecucion.log')

logging.basicConfig(
    filename=archivo_log,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ── CARGA INTELIGENTE DEL ENVIROMENT (.env) ──────────────────────────────────
ruta_env = find_dotenv()
if ruta_env:
    load_dotenv(ruta_env)
else:
    raiz_proyecto = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=raiz_proyecto / '.env')

# ── logging MEJORADO (DataOps) ──────────────────────────────────────────────


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - [CARGA] - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)
logging.getlogging().addHandler(console_handler)

# ── CONEXIÓN ORACLE SEGURA ───────────────────────────────────────────────────
def get_connection():
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "1521")
    DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1") 
    
    if not DB_USER or not DB_PASSWORD:
        raise ValueError("❌ ERROR: Las credenciales del .env están vacías.")
        
    try:
        connection = oracledb.connect(
            user=DB_USER, 
            password=DB_PASSWORD, 
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE
        )
        logging.info(f"Conexión exitosa a Oracle en {DB_HOST}:{DB_PORT} (Servicio: {DB_SERVICE})")
        return connection
    except Exception as e:
        logging.error(f"Error crítico al conectar a Oracle: {e}")
        print("❌ Falla de conexión a BD. Verifica tu Docker y el archivo .env.")
        raise e

# ── MOTOR DE CARGA TRANSACCIONAL ────────────────────────────────────────────
def iniciar_carga():
    logging.info("=== INICIO DE ETAPA 4: CARGA DE DATOS A BASE DE DATOS ===")
    
    ruta_validos = "./data/validated/dataset_hospitales_validado.csv"
    
    if not os.path.exists(ruta_validos):
        logging.error(f"No se encontró el archivo de validados: {ruta_validos}")
        print("❌ Error: No existe el archivo validado. Ejecuta la Etapa 3 primero.")
        return
    try:
        df = pd.read_csv(ruta_validos)
        total_registros = len(df)
        logging.info(f"Archivo detectado. Preparando inserción de {total_registros} atenciones.")

        conn = get_connection()
        cursor = conn.cursor()

        insertados_ok = 0
        errores_bd = 0
        
        # --- INICIO DISEÑO CIFRADO AES-256 ---
        # Obtenemos la llave desde el .env
        llave_secreta = os.getenv("DB_ENCRYPTION_KEY")
        if not llave_secreta:
            raise ValueError("❌ ERROR: DB_ENCRYPTION_KEY no configurada en .env")
        
        # Preparamos el motor de cifrado
        cipher_suite = Fernet(llave_secreta.encode()) 
        # --- FIN DISEÑO CIFRADO ---

        # Iterar sobre cada fila e insertar respetando el Schema Relacional
        for index, fila in df.iterrows():
            try:
                # 1. TABLA: pacientes
                try:
                    sql_paciente = """
                        INSERT INTO pacientes (rut_paciente, nombre_completo, fecha_nacimiento, sexo, prevision)
                        VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'), :4, :5)
                    """
                    cursor.execute(sql_paciente, [
                        str(fila['rut_paciente']), 
                        str(fila['nombre_completo']), 
                        str(fila['fecha_nacimiento']), 
                        str(fila['sexo']), 
                        str(fila['prevision'])
                    ])
                except oracledb.IntegrityError as e:
                    error_obj, = e.args
                    # Ignoramos si el paciente ya existe (Llave Primaria duplicada)
                    if error_obj.code == 1: 
                        pass 
                    else:
                        raise e 

                # 2. TABLA: atenciones
                sql_atencion = """
                    INSERT INTO atenciones (id_atencion, rut_paciente, fecha_atencion, tipo_atencion, codigo_cie10)
                    VALUES (:1, :2, TO_TIMESTAMP(:3, 'YYYY-MM-DD HH24:MI:SS'), :4, :5)
                """
                cursor.execute(sql_atencion, [
                    str(fila['id_atencion']), 
                    str(fila['rut_paciente']), 
                    str(fila['fecha_atencion']), 
                    str(fila['tipo_atencion']), 
                    str(fila['codigo_cie10'])
                ])

                # 3. TABLA: medicamentos (id es SERIAL, no lo mandamos)
                codigo_min = str(fila['codigo_minsal'])
                if pd.notna(codigo_min) and codigo_min.strip() != "" and codigo_min.lower() != "nan":
                    sql_med = """
                        INSERT INTO medicamentos (id_atencion, codigo_minsal, dosis_prescrita)
                        VALUES (:1, :2, :3)
                    """
                    cursor.execute(sql_med, [
                        str(fila['id_atencion']), 
                        codigo_min, 
                        str(fila['dosis_prescrita'])
                    ])

                # 4. TABLA: alergias (id es SERIAL, no lo mandamos)
                alergia = str(fila['alergia_principio']).strip()
                if alergia.upper() != 'NINGUNA' and alergia != "" and alergia.lower() != "nan":
                    cursor.execute("SELECT 1 FROM alergias WHERE rut_paciente = :1 AND UPPER(alergia_principio) = :2", 
                                [str(fila['rut_paciente']), alergia.upper()])
                    if not cursor.fetchone():
                        sql_alergia = """
                            INSERT INTO alergias (rut_paciente, alergia_principio)
                            VALUES (:1, :2)
                        """
                        cursor.execute(sql_alergia, [
                            str(fila['rut_paciente']), 
                            alergia
                        ])

                # 5. TABLA: examenes
                id_exam = str(fila['id_examen'])
                if pd.notna(id_exam) and id_exam.strip() != "" and id_exam.lower() != "nan":
                    sql_examen = """
                        INSERT INTO examenes (id_examen, id_atencion, codigo_examen, resultado_valor, unidad_medida)
                        VALUES (:1, :2, :3, :4, :5)
                    """
                    val_resultado = None if pd.isna(fila['resultado_valor']) else float(fila['resultado_valor'])
                    val_unidad = None if pd.isna(fila['unidad_medida']) else str(fila['unidad_medida'])
                    
                    cursor.execute(sql_examen, [
                        id_exam, 
                        str(fila['id_atencion']), 
                        str(fila['codigo_examen']), 
                        val_resultado, 
                        val_unidad
                    ])

                # TRANSACCIÓN EXITOSA: Todo el grupo de datos de esta fila se guardó bien
                conn.commit() 
                insertados_ok += 1

            except Exception as row_error:
                # ROLLBACK: Si algo falló (ej: examen sin tipo), se deshace todo para ese paciente
                conn.rollback() 
                errores_bd += 1
                logging.error(f"Rollback para id_atencion {fila.get('id_atencion', '?')}. Causa: {row_error}")

        logging.info(f"Proceso de Carga finalizado. Insertados OK: {insertados_ok} | Errores BD: {errores_bd}")
        logging.info("=== FIN DE ETAPA 4: CARGA A BASE DE DATOS ===")
        
        print(f"\n✅ Etapa 4 Completada.")
        print(f"   📊 Registros procesados e insertados: {insertados_ok}/{total_registros}")
        if errores_bd > 0:
            print(f"   ⚠️ Hubo {errores_bd} errores de Integridad en BD. Revisa el log.")

        cursor.close()
        conn.close()

    except Exception as e:
        logging.error(f"Fallo general en la capa de ejecución de BD: {e}")
        print(f"❌ El proceso de carga falló de forma crítica. Error: {e}")

if __name__ == "__main__":
    iniciar_carga()