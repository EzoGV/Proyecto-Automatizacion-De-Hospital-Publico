import pandas as pd
import os
import logging


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
    
    archivo_csv = os.path.join(ruta_raw, 'datos_hospital_san_jose.csv')
    archivo_excel = os.path.join(ruta_raw, 'datos_hospital_regional_sur.xlsx')
    
    try:
        # 1. LECTURA Y CONSOLIDACIÓN
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


        # KPI: DUPLICADOS
        tasa_duplicados = (duplicados_eliminados / total_inicial) * 100
        logging.info("--- KPI: DUPLICADOS ---")
        logging.info(f"Registros antes de limpieza: {total_inicial}")
        logging.info(f"Duplicados eliminados: {duplicados_eliminados} ({tasa_duplicados:.2f}%)")
        logging.info(f"Registros finales: {total_sin_duplicados}")
        logging.info("--- FIN KPI: DUPLICADOS ---")
        print("--- KPI: DUPLICADOS ---")
        print(f"Registros antes de limpieza: {total_inicial}")
        print(f"Duplicados eliminados: {duplicados_eliminados} ({tasa_duplicados:.2f}%)")
        print(f"Registros finales: {total_sin_duplicados}")
        print("--- FIN KPI: DUPLICADOS ---")
        
        # 3. TRATAMIENTO DE NULOS Y NORMALIZACIÓN DE NOMBRES
        df_consolidado['nombre_completo'] = df_consolidado['nombre_completo'].fillna('DESCONOCIDO')
        df_consolidado['nombre_completo'] = df_consolidado['nombre_completo'].str.strip().str.title()
        
        # 4. NORMALIZACIÓN DE RUT
        df_consolidado['rut_paciente'] = df_consolidado['rut_paciente'].apply(limpiar_rut)
        
        # 5. ESTANDARIZACIÓN DE FECHAS
        df_consolidado['fecha_nacimiento'] = pd.to_datetime(df_consolidado['fecha_nacimiento'], errors='coerce').dt.strftime('%Y-%m-%d')
        df_consolidado['fecha_atencion'] = pd.to_datetime(df_consolidado['fecha_atencion'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 6. TRATAMIENTO DE NULOS EN ALERGIAS
        df_consolidado['alergia_principio'] = df_consolidado['alergia_principio'].fillna('Ninguna')
        
        # 7. ESTANDARIZAR VARIABLES CATEGÓRICAS
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
        
    except Exception as e:
        logging.error(f"Error critico en la limpieza: {e}")
        print(f"Ocurrio un error. Revisa el archivo de logs:")

if __name__ == "__main__":
    iniciar_limpieza()