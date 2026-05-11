import pandas as pd
import os
import logging

# 1. CONFIGURACIÓN DE CARPETA DE LOGS (Mantenemos la trazabilidad)
ruta_logs = "./RegistroLogs"
os.makedirs(ruta_logs, exist_ok=True)
archivo_log = os.path.join(ruta_logs, 'pipeline_ejecucion.log')

logging.basicConfig(
    filename=archivo_log,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def limpiar_rut(rut):
    """
    Normaliza el RUT: quita puntos, espacios y guiones, y luego 
    le vuelve a poner el guion antes del dígito verificador.
    Ejemplo: '12.345.6789' -> '12345678-9'
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
    logging.info("=== INICIO DE ETAPA 2: LIMPIEZA Y TRANSFORMACIÓN ===")
    
    ruta_raw = "./data/raw"
    ruta_processed = "./data/processed"
    
    # Aseguramos que exista la carpeta processed
    os.makedirs(ruta_processed, exist_ok=True)
    
    archivo_csv = os.path.join(ruta_raw, 'datos_hospital_san_jose.csv')
    archivo_excel = os.path.join(ruta_raw, 'datos_hospital_regional_sur.xlsx')
    
    try:
        # 1. LECTURA Y CONSOLIDACIÓN
        # Juntamos los datos de ambos hospitales en un solo DataFrame gigante
        df_csv = pd.read_csv(archivo_csv)
        df_excel = pd.read_excel(archivo_excel)
        
        df_consolidado = pd.concat([df_csv, df_excel], ignore_index=True)
        total_inicial = len(df_consolidado)
        logging.info(f"Lectura exitosa. Registros consolidados: {total_inicial}")
        
        # 2. ELIMINAR DUPLICADOS EXACTOS
        df_consolidado.drop_duplicates(inplace=True)
        total_sin_duplicados = len(df_consolidado)
        duplicados_eliminados = total_inicial - total_sin_duplicados
        logging.info(f"Limpieza: {duplicados_eliminados} filas duplicadas eliminadas.")
        
        # 3. TRATAMIENTO DE NULOS Y NORMALIZACIÓN DE NOMBRES
        # Si el nombre viene nulo, le ponemos DESCONOCIDO
        df_consolidado['nombre_completo'] = df_consolidado['nombre_completo'].fillna('DESCONOCIDO')
        # Limpiamos espacios extra y aplicamos formato Título (Ej: "juan perez" -> "Juan Perez")
        df_consolidado['nombre_completo'] = df_consolidado['nombre_completo'].str.strip().str.title()
        
        # 4. NORMALIZACIÓN DE RUT
        df_consolidado['rut_paciente'] = df_consolidado['rut_paciente'].apply(limpiar_rut)
        
        # 5. ESTANDARIZACIÓN DE FECHAS
        # Convertimos forzosamente a formato YYYY-MM-DD para evitar problemas en SQL
        df_consolidado['fecha_nacimiento'] = pd.to_datetime(df_consolidado['fecha_nacimiento'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_consolidado['fecha_atencion'] = pd.to_datetime(df_consolidado['fecha_atencion'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 6. TRATAMIENTO DE NULOS EN ALERGIAS Y EXÁMENES
        df_consolidado['alergia_principio'] = df_consolidado['alergia_principio'].fillna('Ninguna')
        
        # 7. ESTANDARIZAR VARIABLES CATEGÓRICAS (Mayúsculas sin espacios)
        df_consolidado['prevision'] = df_consolidado['prevision'].str.strip().str.upper()
        df_consolidado['tipo_atencion'] = df_consolidado['tipo_atencion'].str.strip().str.upper()

        # 8. EXPORTAR RESULTADO LIMPIO
        archivo_salida = os.path.join(ruta_processed, 'dataset_hospitales_limpio.csv')
        df_consolidado.to_csv(archivo_salida, index=False)
        
        logging.info(f"Exportación exitosa a: {archivo_salida} con {total_sin_duplicados} registros finales.")
        logging.info("=== FIN DE ETAPA 2: LIMPIEZA Y TRANSFORMACIÓN ===")
        print(f"Etapa 2 Completada: Limpieza aplicada. Dataset unificado guardado en {ruta_processed}")
        
    except Exception as e:
        logging.error(f"Error crítico en la limpieza: {e}")
        print(f" Ocurrió un error. Revisa el archivo de logs.")

if __name__ == "__main__":
    iniciar_limpieza()