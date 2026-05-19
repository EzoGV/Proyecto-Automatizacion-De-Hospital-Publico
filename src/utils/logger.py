import logging
import os

# Carpeta de logs
ruta_logs = "./RegistroLogs"

if not os.path.exists(ruta_logs):
    os.makedirs(ruta_logs)

# Archivo de logs
archivo_log = os.path.join(ruta_logs, 'pipeline_ejecucion.log')

# Configuración logger centralizado
logging.basicConfig(
    filename=archivo_log,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Logger reutilizable
logger = logging.getLogger("hospital_pipeline")