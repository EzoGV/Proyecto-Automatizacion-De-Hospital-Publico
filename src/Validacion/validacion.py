# src/Validacion/validacion.py
import pandas as pd
import os
import re
import oracledb
from datetime import datetime
from dotenv import load_dotenv

# Cargar credenciales ocultas desde .env
load_dotenv()

# ── logger MEJORADO (DataOps) ──────────────────────────────────────────────
from utils.logger import logger
from utils.logger import ruta_logs

console_handler = logger.StreamHandler()
console_handler.setLevel(logger.INFO)
console_formatter = logger.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S')
console_handler.setFormatter(console_formatter)
logger.getLogger().addHandler(console_handler)

# ── CONEXIÓN ORACLE SEGURA ──────────────────────────────────────────────────
# ── CONEXIÓN ORACLE SEGURA ──────────────────────────────────────────────────
def get_connection():
    """Establece la conexión a Oracle usando variables de entorno (.env) en Modo Thin"""
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "1521")
    DB_SERVICE = os.getenv("DB_SERVICE", "XE")
    
    try:
        # Al pasar host, port y service_name por separado, oracledb usa automáticamente el modo THIN
        connection = oracledb.connect(
            user=DB_USER, 
            password=DB_PASSWORD, 
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE
        )
        logger.info(f"Conexión exitosa a Oracle en {DB_HOST} (Servicio: {DB_SERVICE})")
        return connection
    except Exception as e:
        logger.error(f"Error crítico al conectar a Oracle: {e}")
        print("❌ Falla de conexión a BD. Verifica tu archivo .env y que Oracle esté corriendo.")
        raise e

# ── LISTAS BLANCAS ────────────────────────────────────────────────────────────
SEXOS_VALIDOS       = {'M', 'F'}
PREVISIONES_VALIDAS = {'FONASA', 'ISAPRE', 'NINGUNA', 'DIPRECA', 'CAPREDENA'}
TIPOS_ATENCION      = {'CONSULTA', 'HOSPITALIZACION', 'PROCEDIMIENTO', 'URGENCIA'}

# ── CREAR TABLA CUARENTENA ────────────────────────────────────────────────────
def crear_tabla_cuarentena(connection):
    sql = """
        CREATE TABLE CUARENTENA (
            id_registro          VARCHAR2(36),
            campo_fallido        VARCHAR2(50),
            valor_encontrado     VARCHAR2(200),
            motivo               VARCHAR2(100),
            timestamp_validacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        logger.info("Tabla CUARENTENA verificada/creada exitosamente en BD.")
    except Exception as e:
        if "ORA-00955" in str(e):
            logger.info("Tabla CUARENTENA ya existe en BD, continuando.")
        else:
            logger.error(f"Error creando tabla CUARENTENA: {e}")
            raise

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
def insertar_cuarentena(cursor, id_registro, campo, valor, motivo):
    sql = """
        INSERT INTO CUARENTENA (id_registro, campo_fallido, valor_encontrado, motivo)
        VALUES (:1, :2, :3, :4)
    """
    cursor.execute(sql, [str(id_registro), str(campo), str(valor), str(motivo)])

def calcular_kpi_completitud(df):
    logger.info("--- INICIO KPI: COMPLETITUD POR COLUMNA ---")
    total_filas = len(df)
    for columna in df.columns:
        if columna == 'motivo_rechazo': continue 
        incompletos = df[columna].isna().sum() + (df[columna].astype(str).str.strip() == '').sum()
        completitud = ((total_filas - incompletos) / total_filas) * 100
        if completitud < 99.0:
            logger.warning(f"Completitud BAJA en [{columna}]: {completitud:.2f}%")
        else:
            logger.info(f"Completitud OK en [{columna}]: {completitud:.2f}%")

def calcular_kpi_errores(total, errores_filas):
    logger.info("--- INICIO KPI: TASA DE ERROR ---")
    tasa_error = (errores_filas / total) * 100
    logger.info(f"Registros válidos procesados: {total - errores_filas} ({100 - tasa_error:.2f}%)")
    logger.info(f"Registros con error (Cuarentena): {errores_filas} ({tasa_error:.2f}%)")

def calcular_kpi_auditoria(errores_detalle):
    logger.info("--- INICIO KPI: AUDITORÍA DE ERRORES ---")
    conteo = {}
    for _, _, _, motivo in errores_detalle:
        conteo[motivo] = conteo.get(motivo, 0) + 1
    for motivo, cantidad in sorted(conteo.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"Anomalía detectada - {motivo}: {cantidad} incidentes")

# ── MOTOR PRINCIPAL DE VALIDACIÓN ──────────────────────────────────────────────
def iniciar_validacion():
    logger.info("=== INICIO DE ETAPA 3: VALIDACIÓN ESTRUCTURAL Y SEMÁNTICA ===")

    ruta_dataset = "./data/processed/dataset_hospitales_limpio.csv"
    ruta_validos = "./data/validated"
    ruta_invalidos = "./data/invalidated"
    os.makedirs(ruta_validos, exist_ok=True)
    os.makedirs(ruta_invalidos, exist_ok=True)

    try:
        df = pd.read_csv(ruta_dataset)
        total = len(df)
        logger.info(f"Dataset cargado desde Processed: {total} registros a validar.")
        
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

        logger.info("Iniciando escaneo de Reglas de Negocio registro por registro...")

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
                logger.warning(f"Fila {index} enviada a cuarentena. Motivo(s): {' | '.join(motivos_fila)}")
                
                # INSERCIÓN REAL EN BD ORACLE
                for id_r, col, val, mot in errores_detalle[-len(motivos_fila):]:
                    insertar_cuarentena(cursor, id_r, col, val, mot)

        # SEPARACIÓN Y GUARDADO
        logger.info("Separando registros Válidos e Inválidos...")
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
        
        connection.commit()
        logger.info("Transacción de CUARENTENA finalizada en BD Oracle.")

        cursor.close()
        connection.close()

        print(f"\n✅ Etapa 3 Completada: {len(df_validos)} registros válidos.")
        print(f"📁 Válidos generados en: {ruta_validos}")
        if not df_invalidos.empty:
            print(f"🔴 Rechazados (Cuarentena) en BD y en carpeta: {ruta_invalidos}")

    except Exception as e:
        logger.error(f"Error crítico en validación: {e}")
        print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    iniciar_validacion()