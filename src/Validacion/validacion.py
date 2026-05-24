# src/Validacion/validacion.py
import pandas as pd
import os
import re
import oracledb
import sys
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

raiz_proyecto = Path(__file__).resolve().parent.parent
sys.path.append(str(raiz_proyecto))
# Cargar credenciales ocultas desde .env
load_dotenv()

# ── logging MEJORADO (DataOps) ──────────────────────────────────────────────
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

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

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

# ── LISTAS BLANCAS ────────────────────────────────────────────────────────────
SEXOS_VALIDOS       = {'M', 'F'}
PREVISIONES_VALIDAS = {'FONASA', 'ISAPRE', 'NINGUNA', 'DIPRECA', 'CAPREDENA'}
TIPOS_ATENCION      = {'CONSULTA', 'HOSPITALIZACION', 'PROCEDIMIENTO', 'URGENCIA'}

# ── CREAR TABLA CUARENTENA ────────────────────────────────────────────────────
def crear_tabla_cuarentena(connection):
    cursor = connection.cursor()
    # 1. Intentar crear la tabla si no existe
    try:
        sql = """CREATE TABLE CUARENTENA (
            id_registro VARCHAR2(36), campo_fallido VARCHAR2(50), 
            valor_encontrado VARCHAR2(200), motivo_rechazo VARCHAR2(100), 
            timestamp_validacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""
        cursor.execute(sql)
    except Exception:
        pass # La tabla ya existe
    
    # 2. LIMPIEZA: Borrar registros anteriores para que cada ejecucion sea limpia
    cursor.execute("DELETE FROM CUARENTENA")

    
    connection.commit()
    cursor.close()
    logging.info("Tabla CUARENTENA y errores_validacion limpiadas para nueva ejecucion.")

# ── FUNCIONES DE VALIDACIÓN ───────────────────────────────────────────────────
def validar_formato_rut(rut):
    return bool(re.match(r'^\d{7,8}-[\dkK]$', str(rut).strip()))

def validar_fecha(fecha_str, formato):
    try:
        datetime.strptime(str(fecha_str), formato)
        return True
    except:
        return False

def validar_rut_chileno(rut):
    try:
        cuerpo, dv = str(rut).strip().split('-')
        cuerpo = cuerpo.replace('.', '')
        suma, factor = 0, 2
        for digito in reversed(cuerpo):
            suma += int(digito) * factor
            factor = 2 if factor == 7 else factor + 1
        resto = 11 - (suma % 11)
        if resto == 11: dv_calculado = '0'
        elif resto == 10: dv_calculado = 'K'
        else: dv_calculado = str(resto)
        return dv.upper() == dv_calculado
    except:
        return False

def validar_edad(fecha_nacimiento, fecha_atencion):
    try:
        fnac = datetime.strptime(str(fecha_nacimiento), '%Y-%m-%d')
        fat  = datetime.strptime(str(fecha_atencion)[:10], '%Y-%m-%d')
        return 0 <= ((fat - fnac).days / 365.25) <= 120
    except:
        return False

def validar_coherencia_fechas(fecha_nacimiento, fecha_atencion):
    try:
        fnac = datetime.strptime(str(fecha_nacimiento), '%Y-%m-%d')
        fat  = datetime.strptime(str(fecha_atencion)[:10], '%Y-%m-%d')
        return fat >= fnac
    except:
        return False

def validar_resultado_valor(valor):
    if pd.isna(valor): return True 
    try:
        return float(valor) >= 0
    except:
        return False

def validar_dosis(dosis):
    return bool(re.match(r'^\d+(\.\d+)?(mg|ml|g|mcg|UI)$', str(dosis).strip(), re.IGNORECASE))  

def validar_codigo_cie10(codigo, catalogo_cie10):
    return str(codigo).strip() in catalogo_cie10

def validar_fecha_no_futura(fecha_str, formato):
    try:
        fecha = datetime.strptime(str(fecha_str), formato)
        return fecha <= datetime.now()
    except:
        return False

def validar_codigo_minsal(codigo):
    return bool(re.match(r'^M\d{3}$', str(codigo).strip()))

# ── MOTOR DE KPIs Y BD ────────────────────────────────────────────────────────
def insertar_cuarentena(cursor, id_registro, campo, valor, motivo_rechazo):
    sql = """
        INSERT INTO CUARENTENA (id_registro, campo_fallido, valor_encontrado, motivo_rechazo)
        VALUES (:1, :2, :3, :4)
    """
    cursor.execute(sql, [str(id_registro), str(campo), str(valor), str(motivo_rechazo)])

def calcular_kpi_completitud(df):
    logging.info("--- INICIO KPI: COMPLETITUD POR COLUMNA ---")
    total_filas = len(df)
    for columna in df.columns:
        if columna == 'motivo_rechazo': continue 
        incompletos = df[columna].isna().sum() + (df[columna].astype(str).str.strip() == '').sum()
        completitud = ((total_filas - incompletos) / total_filas) * 100
        if completitud < 99.0:
            logging.warning(f"Completitud BAJA en [{columna}]: {completitud:.2f}%")
        else:
            logging.info(f"Completitud OK en [{columna}]: {completitud:.2f}%")

def calcular_kpi_errores(total, errores_filas):
    logging.info("--- INICIO KPI: TASA DE ERROR ---")
    tasa_error = (errores_filas / total) * 100
    logging.info(f"Registros validos procesados: {total - errores_filas} ({100 - tasa_error:.2f}%)")
    logging.info(f"Registros con error (Cuarentena): {errores_filas} ({tasa_error:.2f}%)")

def calcular_kpi_auditoria(errores_detalle):
    logging.info("--- INICIO KPI: AUDITORIA DE ERRORES ---")
    conteo = {}
    for _, _, _, motivo_rechazo in errores_detalle:
        conteo[motivo_rechazo] = conteo.get(motivo_rechazo, 0) + 1
    for motivo_rechazo, cantidad in sorted(conteo.items(), key=lambda x: x[1], reverse=True):
        logging.info(f"Anomalia detectada - {motivo_rechazo}: {cantidad} incidentes")

# ── MOTOR PRINCIPAL DE VALIDACIÓN ──────────────────────────────────────────────
def iniciar_validacion():
    logging.info("=== INICIO DE ETAPA 3: VALIDACION ESTRUCTURAL Y SEMANTICA ===")

    ruta_dataset = "./data/processed/dataset_hospitales_limpio.csv"
    ruta_validos = "./data/validated"
    ruta_invalidos = "./data/invalidated"
    os.makedirs(ruta_validos, exist_ok=True)
    os.makedirs(ruta_invalidos, exist_ok=True)

    try:
        df = pd.read_csv(ruta_dataset)
        total = len(df)
        logging.info(f"Dataset cargado desde Processed: {total} registros a validar.")
        
        df['motivo_rechazo'] = ""

        try:
            df_cie10 = pd.read_csv("./data/CIE-10/codigos_cie10.csv")
            catalogo_cie10 = set(df_cie10['codigo'].str.strip())
        except:
            catalogo_cie10 = {'J00', 'E11.9', 'I10', 'A09.9'}

        # CONEXIÓN ORACLE (AHORA SÍ ES REAL)
        connection = get_connection()
        crear_tabla_cuarentena(connection)
        cursor = connection.cursor()

        errores_detalle = []
        ids_atencion_vistos  = set()
        ids_examen_vistos    = set()
        indices_malos = set()

        logging.info("Iniciando escaneo de Reglas de Negocio registro por registro...")

        for index, fila in df.iterrows():
            id_reg = fila['id_atencion']
            motivos_fila = []

            if not validar_formato_rut(fila['rut_paciente']):
                motivos_fila.append('RUT_FORMATO_INVALIDO')
                errores_detalle.append((id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_FORMATO_INVALIDO'))
            elif not validar_rut_chileno(fila['rut_paciente']):
                motivos_fila.append('RUT_DIGITO_INVALIDO')
                errores_detalle.append((id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_DIGITO_INVALIDO'))
            
            if not validar_fecha(fila['fecha_nacimiento'], '%Y-%m-%d'):
                motivos_fila.append('FECHA_NACIMIENTO_INVALIDA')
                errores_detalle.append((id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'FECHA_NACIMIENTO_INVALIDA'))
            
            if not validar_fecha(fila['fecha_atencion'], '%Y-%m-%d %H:%M:%S'):
                motivos_fila.append('FECHA_ATENCION_INVALIDA')
                errores_detalle.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_INVALIDA'))
            
            if not validar_coherencia_fechas(fila['fecha_nacimiento'], fila['fecha_atencion']):
                motivos_fila.append('FECHA_ATENCION_ANTERIOR_NACIMIENTO')
                errores_detalle.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_ANTERIOR_NACIMIENTO'))
            
            if not validar_edad(fila['fecha_nacimiento'], fila['fecha_atencion']):
                motivos_fila.append('EDAD_FUERA_DE_RANGO')
                errores_detalle.append((id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'EDAD_FUERA_DE_RANGO'))
            
            if fila['sexo'] not in SEXOS_VALIDOS:
                motivos_fila.append('SEXO_INVALIDO')
                errores_detalle.append((id_reg, 'sexo', fila['sexo'], 'SEXO_INVALIDO'))
            
            if fila['prevision'] not in PREVISIONES_VALIDAS:
                motivos_fila.append('PREVISION_INVALIDA')
                errores_detalle.append((id_reg, 'prevision', fila['prevision'], 'PREVISION_INVALIDA'))
            
            if fila['tipo_atencion'] not in TIPOS_ATENCION:
                motivos_fila.append('TIPO_ATENCION_INVALIDO')
                errores_detalle.append((id_reg, 'tipo_atencion', fila['tipo_atencion'], 'TIPO_ATENCION_INVALIDO'))
            
            if not validar_resultado_valor(fila['resultado_valor']):
                motivos_fila.append('RESULTADO_VALOR_INVALIDO')
                errores_detalle.append((id_reg, 'resultado_valor', fila['resultado_valor'], 'RESULTADO_VALOR_INVALIDO'))
            
            if not validar_dosis(fila['dosis_prescrita']):
                motivos_fila.append('DOSIS_FORMATO_INVALIDO')
                errores_detalle.append((id_reg, 'dosis_prescrita', fila['dosis_prescrita'], 'DOSIS_FORMATO_INVALIDO'))
            
            if not validar_codigo_cie10(fila['codigo_cie10'], catalogo_cie10):
                motivos_fila.append('CODIGO_CIE10_NO_EXISTE')
                errores_detalle.append((id_reg, 'codigo_cie10', fila['codigo_cie10'], 'CODIGO_CIE10_NO_EXISTE'))
            
            if not validar_fecha_no_futura(fila['fecha_atencion'], '%Y-%m-%d %H:%M:%S'):
                motivos_fila.append('FECHA_ATENCION_FUTURA')
                errores_detalle.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_FUTURA'))
            
            if not validar_codigo_minsal(fila['codigo_minsal']):
                motivos_fila.append('CODIGO_MINSAL_FORMATO_INVALIDO')
                errores_detalle.append((id_reg, 'codigo_minsal', fila['codigo_minsal'], 'CODIGO_MINSAL_FORMATO_INVALIDO'))
            
            if id_reg in ids_atencion_vistos:
                motivos_fila.append('ID_ATENCION_DUPLICADO')
                errores_detalle.append((id_reg, 'id_atencion', id_reg, 'ID_ATENCION_DUPLICADO'))
            else:
                ids_atencion_vistos.add(id_reg)
                
            if fila['id_examen'] in ids_examen_vistos:
                motivos_fila.append('ID_EXAMEN_DUPLICADO')
                errores_detalle.append((id_reg, 'id_examen', fila['id_examen'], 'ID_EXAMEN_DUPLICADO'))
            else:
                ids_examen_vistos.add(fila['id_examen'])
            
            if len(motivos_fila) > 0:
                indices_malos.add(index)
                df.at[index, 'motivo_rechazo'] = " | ".join(motivos_fila)
                logging.warning(f"Fila {index} enviada a cuarentena. Motivo(s): {' | '.join(motivos_fila)}")
                
                # INSERCIÓN REAL EN BD ORACLE
                for id_r, col, val, mot in errores_detalle[-len(motivos_fila):]:
                    insertar_cuarentena(cursor, id_r, col, val, mot)

        # SEPARACIÓN Y GUARDADO
        logging.info("Separando registros Válidos e Inválidos...")
        df_validos = df.drop(index=list(indices_malos)).drop(columns=['motivo_rechazo'])
        df_invalidos = df.loc[list(indices_malos)]

        archivo_validos_csv = os.path.join(ruta_validos, 'dataset_hospitales_validado.csv')
        archivo_validos_excel = os.path.join(ruta_validos, 'dataset_hospitales_validado.xlsx')
        archivo_invalidos_csv = os.path.join(ruta_invalidos, 'dataset_hospitales_rechazados.csv')
        archivo_invalidos_excel = os.path.join(ruta_invalidos, 'dataset_hospitales_rechazados.xlsx')

        df_validos.to_csv(archivo_validos_csv, index=False)
        df_validos.to_excel(archivo_validos_excel, index=False, sheet_name='Validos')
        
        if not df_invalidos.empty:
            df_invalidos.to_csv(archivo_invalidos_csv, index=False)
            df_invalidos.to_excel(archivo_invalidos_excel, index=False, sheet_name='Rechazados')

        calcular_kpi_completitud(df)
        calcular_kpi_errores(total, len(indices_malos))
        calcular_kpi_auditoria(errores_detalle)

        # KPI: Tasa de completitud general
        tasa_validez = ((total - len(indices_malos)) / total) * 100
        registrar_audit_log(connection, 'VALIDACION', 'TASA_VALIDEZ', f"{tasa_validez:.2f}%", 'OK' if tasa_validez >= 90 else 'ALERTA')
        registrar_audit_log(connection, 'VALIDACION', 'REGISTROS_VALIDOS', len(df_validos), 'OK')
        registrar_audit_log(connection, 'VALIDACION', 'REGISTROS_RECHAZADOS', len(indices_malos), 'OK' if len(indices_malos) == 0 else 'ALERTA')
        registrar_audit_log(connection, 'VALIDACION', 'TOTAL_PROCESADOS', total, 'OK')
        
        connection.commit()
        logging.info("Transaccion de CUARENTENA finalizada en BD Oracle.")

        cursor.close()
        connection.close()

        print(f"\n✅ Etapa 3 Completada: {len(df_validos)} registros validos.")
        print(f"Validos generados en: {ruta_validos}")
        if not df_invalidos.empty:
            print(f"🔴 Rechazados (Cuarentena) en BD y en carpeta: {ruta_invalidos}")

    except Exception as e:
        logging.error(f"Error critico en validacion: {e}")
        print(f"❌ Ocurrio un error: {e}")

if __name__ == "__main__":
    iniciar_validacion()