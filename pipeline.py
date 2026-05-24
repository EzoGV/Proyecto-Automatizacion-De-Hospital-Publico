# pipeline.py
import logging
import os
from datetime import datetime

from src.Ingesta.ingesta import iniciar_ingesta
from src.Limpieza.limpieza import iniciar_limpieza
from src.Validacion.validacion import iniciar_validacion
from src.Carga.carga_bd import iniciar_carga

# ── LOGGING ──────────────────────────────────────────────────────────────────
ruta_logs = "./RegistroLogs"
os.makedirs(ruta_logs, exist_ok=True)
archivo_log = os.path.join(ruta_logs, 'pipeline_ejecucion.log')

logging.basicConfig(
    filename=archivo_log,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def ejecutar_pipeline():
    print("=" * 50)
    print("   PIPELINE HOSPITAL PUBLICO — INICIO")
    print("=" * 50)

    inicio_total = datetime.now()
    logging.info("=== INICIO DEL PIPELINE COMPLETO ===")

    etapas = [
        ("Ingesta",     iniciar_ingesta),
        ("Limpieza",    iniciar_limpieza),
        ("Validacion",  iniciar_validacion),
        ("Carga",       iniciar_carga),
    ]

    for nombre, funcion in etapas:
        print(f"\n▶ Ejecutando etapa: {nombre}...")
        inicio_etapa = datetime.now()
        try:
            funcion()
            duracion_etapa = (datetime.now() - inicio_etapa).total_seconds()
            logging.info(f"Etapa '{nombre}' completada en {duracion_etapa:.2f} segundos.")
            print(f"✅ {nombre} completada en {duracion_etapa:.2f} segundos.")
        except Exception as e:
            duracion_etapa = (datetime.now() - inicio_etapa).total_seconds()
            logging.error(f"Etapa '{nombre}' fallo después de {duracion_etapa:.2f} segundos. Error: {e}")
            print(f"\n❌ Error en etapa '{nombre}': {e}")
            print(f"   El pipeline se detuvo. Revisa el log para mas detalles.")
            print(f"   Archivo: {archivo_log}")
            return

    # KPI: LATENCIA TOTAL
    duracion_total = (datetime.now() - inicio_total).total_seconds()
    logging.info("--- KPI: LATENCIA ---")
    logging.info(f"Duracion total del pipeline: {duracion_total:.2f} segundos.")
    logging.info("--- FIN KPI: LATENCIA ---")

    print("\n" + "=" * 50)
    print(f"   PIPELINE COMPLETADO EN {duracion_total:.2f} SEGUNDOS")
    print("=" * 50)
    logging.info("=== FIN DEL PIPELINE COMPLETO ===")

if __name__ == "__main__":
    ejecutar_pipeline()