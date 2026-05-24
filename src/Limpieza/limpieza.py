import oracledb
import pandas as pd
import os
import logging
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# 1. CONFIGURACIÓN DE CARPETA DE LOGS (Mantenemos la trazabilidad)

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

ruta_env = find_dotenv()
if ruta_env:
    load_dotenv(ruta_env)
else:
    raiz_proyecto = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=raiz_proyecto / '.env')

# ── CONEXIÓN ORACLE SEGURA ──────────────────────────────────────────────────
def get_connection():
    # Ruta a la wallet (relativa a la raíz del proyecto)
    raiz = Path(__file__).resolve().parent.parent.parent
    wallet_dir = str(raiz / "wallet")

    os.environ["TNS_ADMIN"] = wallet_dir

    DB_USER = os.getenv("DB_USER", "ADMIN")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    if not DB_PASSWORD:
        raise ValueError("❌ ERROR: DB_PASSWORD no configurada en .env")

    connection = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn="pipelinehibridohospital_high",  # mismo DSN que interfaz.py
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=DB_PASSWORD
    )

    logging.info(f"Conexion exitosa a Oracle Cloud (OCI) como {DB_USER}")
    return connection

def registrar_audit_log(connection, etapa, kpi_nombre, valor_calculado, estado):
    cursor = connection.cursor()
    sql = """
        INSERT INTO AUDIT_LOG (etapa_pipeline, kpi_nombre, valor_calculado, estado)
        VALUES (:1, :2, :3, :4)
    """
    cursor.execute(sql, [etapa, kpi_nombre, str(valor_calculado), estado])
    connection.commit()
    cursor.close()

def limpiar_rut(rut):
    """
    Normaliza el RUT: quita puntos, espacios y guiones, y luego 
    le vuelve a poner el guion antes del dígito verificador.
    """
    if pd.isna(rut):
        return rut
    
    # Convertimos a string, mayúsculas y quitamos basura
    rut_str = str(rut).upper().replace(".", "").replace("-", "").strip()
    
    if len(rut_str) < 2:
        return rut_str # Por si viene un dato extremadamente corrupto
        
    # Retornamos todo menos el último caracter + guion + último caracter
    return f"{rut_str[:-1]}-{rut_str[-1]}"



def iniciar_limpieza():
    logging.info("=== INICIO DE ETAPA 2: LIMPIEZA Y TRANSFORMACION ===")
    
    ruta_raw = "./data/raw"
    ruta_processed = "./data/processed"
    
    # Aseguramos que exista la carpeta processed
    os.makedirs(ruta_processed, exist_ok=True)
    
    try:
        # ==========================================
        # 1. LECTURA DINÁMICA Y CONSOLIDACIÓN
        # ==========================================
        archivos_raw = [f for f in os.listdir(ruta_raw) if f.endswith(('.csv', '.xlsx', '.xls'))]
        
        if not archivos_raw:
            logging.warning("No hay archivos en data/raw para limpiar.")
            print("⚠️ No hay archivos en data/raw para limpiar.")
            return
            
        lista_dfs = []
        
        for archivo in archivos_raw:
            ruta_archivo = os.path.join(ruta_raw, archivo)
            try:
                if archivo.endswith('.csv'):
                    df_temp = pd.read_csv(ruta_archivo)
                else:
                    df_temp = pd.read_excel(ruta_archivo)
                
                lista_dfs.append(df_temp)
                logging.info(f"Archivo cargado exitosamente: {archivo} con {len(df_temp)} filas.")
            except Exception as e:
                logging.error(f"Error al leer el archivo {archivo}: {e}")
                
        if not lista_dfs:
            logging.error("No se pudo cargar ningún dataframe válido.")
            return
            
        df_consolidado = pd.concat(lista_dfs, ignore_index=True)
        total_inicial = len(df_consolidado)
        logging.info(f"Lectura exitosa. Registros consolidados: {total_inicial}")
        
        # ==========================================
        # 2. ELIMINAR DUPLICADOS EXACTOS
        # ==========================================
        df_consolidado.drop_duplicates(inplace=True)
        total_sin_duplicados = len(df_consolidado)
        duplicados_eliminados = total_inicial - total_sin_duplicados
        logging.info(f"Limpieza: {duplicados_eliminados} filas duplicadas eliminadas.")
        
        # ==========================================
        # 3. TRATAMIENTO DE NULOS Y NORMALIZACIÓN DE NOMBRES
        # ==========================================
        df_consolidado['nombre_completo'] = df_consolidado['nombre_completo'].fillna('DESCONOCIDO')
        df_consolidado['nombre_completo'] = df_consolidado['nombre_completo'].str.strip().str.title()
        
        # ==========================================
        # 4. NORMALIZACIÓN DE RUT
        # ==========================================
        df_consolidado['rut_paciente'] = df_consolidado['rut_paciente'].apply(limpiar_rut)
        
        # ==========================================
        # 5. ESTANDARIZACIÓN DE FECHAS
        # ==========================================
        df_consolidado['fecha_nacimiento'] = pd.to_datetime(df_consolidado['fecha_nacimiento'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_consolidado['fecha_atencion'] = pd.to_datetime(df_consolidado['fecha_atencion'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # ==========================================
        # 6. TRATAMIENTO DE NULOS EN ALERGIAS
        # ==========================================
        df_consolidado['alergia_principio'] = df_consolidado['alergia_principio'].fillna('Ninguna')
        
        # ==========================================
        # 7. ESTANDARIZAR VARIABLES CATEGÓRICAS
        # ==========================================
        df_consolidado['prevision'] = df_consolidado['prevision'].str.strip().str.upper()
        df_consolidado['tipo_atencion'] = df_consolidado['tipo_atencion'].str.strip().str.upper()

        # ==========================================
        # 8. EXPORTAR RESULTADO LIMPIO (CSV Y EXCEL)
        # ==========================================
        archivo_salida_csv = os.path.join(ruta_processed, 'dataset_hospitales_limpio.csv')
        archivo_salida_excel = os.path.join(ruta_processed, 'dataset_hospitales_limpio.xlsx')
        
        # Generar CSV (ideal para máquinas/base de datos)
        df_consolidado.to_csv(archivo_salida_csv, index=False)
        
        # Generar Excel (ideal para humanos/trazabilidad)
        df_consolidado.to_excel(archivo_salida_excel, index=False, sheet_name='Datos_Limpios')
        
        logging.info(f"Exportacion exitosa a CSV y Excel con {total_sin_duplicados} registros finales.")
        logging.info("=== FIN DE ETAPA 2: LIMPIEZA Y TRANSFORMACION ===")
        
        print(f"Etapa 2 Completada: Limpieza aplicada.")
        print(f"Archivos generados en la carpeta '{ruta_processed}':")
        print(f"    {archivo_salida_csv}")
        print(f"    {archivo_salida_excel}")

        # ==========================================
        # 9. REGISTRAR KPIs EN AUDIT_LOG
        # ==========================================
        try:
            conn = get_connection()
            print(f"✅ Conexion a Oracle exitosa desde Limpieza")
            registrar_audit_log(conn, 'LIMPIEZA', 'REGISTROS_ENTRADA', total_inicial, 'OK')
            registrar_audit_log(conn, 'LIMPIEZA', 'DUPLICADOS_ELIMINADOS', duplicados_eliminados, 'OK' if duplicados_eliminados == 0 else 'ALERTA')
            registrar_audit_log(conn, 'LIMPIEZA', 'REGISTROS_LIMPIOS', total_sin_duplicados, 'OK')
            tasa_limpieza = ((total_sin_duplicados / total_inicial) * 100)
            registrar_audit_log(conn, 'LIMPIEZA', 'TASA_RETENCION', f"{tasa_limpieza:.2f}%", 'OK' if tasa_limpieza >= 95 else 'ALERTA')
            
            conn.close()
            logging.info("KPIs de limpieza registrados en AUDIT_LOG correctamente.")
        except Exception as e:
            print(f"❌ ERROR REAL en AUDIT_LOG: {e}")  # <-- esto te dirá exactamente qué falla
            logging.warning(f"No se pudo registrar en AUDIT_LOG: {e}")
        
    except Exception as e:
        logging.error(f"Error critico en la limpieza: {e}")
        print(f"Ocurrio un error. Revisa el archivo de logs:")

if __name__ == "__main__":
    iniciar_limpieza()