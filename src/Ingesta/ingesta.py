import pandas as pd
import shutil
import os
import logging
from datetime import datetime

# 1. CONFIGURACIÓN DE CARPETA DE LOGS
# Primero aseguramos que la carpeta RegistroLogs exista
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

def iniciar_ingesta():
    logging.info("=== INICIO DE ETAPA 1: INGESTA DE DATOS ===")
    
    # Definición de rutas (usando el punto para que sea ruta relativa)
    ruta_origen = "data/origen" 
    ruta_destino = "./data/raw" 
    
    # Aseguramos que la carpeta de destino exista
    if not os.path.exists(ruta_destino):
        os.makedirs(ruta_destino)
        logging.info(f"Carpeta creada: {ruta_destino}")

    # Lista de archivos a procesar
    archivos_hospitales = [
        'datos_hospital_san_jose.csv',
        'datos_hospital_regional_sur.xlsx'
    ]

    total_registros_dia = 0

    for nombre_archivo in archivos_hospitales:
        path_completo_origen = os.path.join(ruta_origen, nombre_archivo)
        
        if os.path.exists(path_completo_origen):
            try:
                # Contar registros según el tipo de archivo
                if nombre_archivo.endswith('.csv'):
                    df_temp = pd.read_csv(path_completo_origen)
                else:
                    df_temp = pd.read_excel(path_completo_origen)
                
                cantidad_filas = len(df_temp)
                total_registros_dia += cantidad_filas
                
                # Movimiento del archivo (Captura)
                path_destino_final = os.path.join(ruta_destino, nombre_archivo)
                shutil.copy(path_completo_origen, path_destino_final)
                
                logging.info(f"Captura exitosa: {nombre_archivo} | Registros: {cantidad_filas} | Destino: {ruta_destino}")
                print(f"✅ Procesado: {nombre_archivo} ({cantidad_filas} registros)")

            except Exception as e:
                logging.error(f"Error procesando {nombre_archivo}: {e}")
        else:
            logging.warning(f"Archivo no encontrado en origen: {nombre_archivo}")

    logging.info(f"=== FIN DE INGESTA: {total_registros_dia} registros totales capturados ===")
    print(f"\n🚀 Ingesta terminada. Revisa la carpeta '{ruta_logs}' para ver los detalles.")

if __name__ == "__main__":
    iniciar_ingesta()