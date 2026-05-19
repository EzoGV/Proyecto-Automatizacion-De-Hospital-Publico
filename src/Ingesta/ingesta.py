import pandas as pd
import shutil
import os
import logging
from datetime import datetime

# 1. CONFIGURACIÓN DE CARPETA DE LOGS (Mantenemos la trazabilidad)
from utils.logger import logger
from utils.logger import ruta_logs

# Primero aseguramos que la carpeta RegistroLogs exista
def iniciar_ingesta():
    logger.info("=== INICIO DE ETAPA 1: INGESTA DE DATOS ===")
    
    # Definición de rutas (usando el punto para que sea ruta relativa)
    ruta_origen = "data/origen" 
    ruta_destino = "./data/raw" 
    
    # Aseguramos que la carpeta de destino exista
    if not os.path.exists(ruta_logs):
        os.makedirs(ruta_logs)
        logging.info(f"Carpeta creada: {ruta_logs}")

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
                
                # Movimiento archivo
                path_destino_final = os.path.join(
                    ruta_destino,
                    nombre_archivo
                )

                shutil.copy(
                    path_completo_origen,
                    path_destino_final
                )
                
                logger.info(
                    f"Captura exitosa: {nombre_archivo} | "
                    f"Registros: {cantidad_filas} | "
                    f"Destino: {ruta_destino}"
                )

                print(
                    f"✅ Procesado: "
                    f"{nombre_archivo} "
                    f"({cantidad_filas} registros)"
                )


            except Exception as e:

                logger.error(
                    f"Error procesando "
                    f"{nombre_archivo}: {e}"
                )
        else:

            logger.warning(
                f"Archivo no encontrado en origen: "
                f"{nombre_archivo}"
            )

    logger.info(
        f"=== FIN DE INGESTA: "
        f"{total_registros_dia} registros totales capturados ==="
    )
    print(
        f"\n🚀 Ingesta terminada. "
        f"Revisa la carpeta 'RegistroLogs' para ver los detalles."
    )

if __name__ == "__main__":
    iniciar_ingesta()