# src/Validacion/validacion.py
import pandas as pd
import logging
import os
import re
from datetime import datetime

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

# ── CONEXIÓN ORACLE (placeholder) ────────────────────────────────────────────
def get_connection():
    """
    TODO: tu compañero reemplaza este bloque con la conexión real.
    Debe retornar un objeto connection compatible con cx_Oracle u oracledb.
    """
    raise NotImplementedError("Conexión Oracle pendiente de implementar.")


# ── LISTAS BLANCAS ────────────────────────────────────────────────────────────
SEXOS_VALIDOS       = {'M', 'F'}
PREVISIONES_VALIDAS = {'FONASA', 'ISAPRE', 'NINGUNA', 'DIPRECA', 'CAPREDENA'}
TIPOS_ATENCION      = {'CONSULTA', 'HOSPITALIZACION', 'PROCEDIMIENTO', 'URGENCIA'}

# ── CREAR TABLA CUARENTENA ────────────────────────────────────────────────────
def crear_tabla_cuarentena(connection):
    """
    Crea la tabla CUARENTENA en Oracle si no existe.
    Se ejecuta una sola vez al inicio del proceso de validación.
    """
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
        logging.info("Tabla CUARENTENA creada exitosamente.")
    except Exception as e:
        # En Oracle, si la tabla ya existe lanza ORA-00955
        # Lo ignoramos para que el pipeline no se rompa en la segunda ejecución
        if "ORA-00955" in str(e):
            logging.info("Tabla CUARENTENA ya existe, continuando.")
        else:
            logging.error(f"Error creando tabla CUARENTENA: {e}")
            raise

# ── FUNCIONES DE VALIDACIÓN ───────────────────────────────────────────────────

def validar_formato_rut(rut):
    """Verifica que el RUT tenga el formato XXXXXXXX-X (normalizado por limpieza)."""
    patron = r'^\d{7,8}-[\dkK]$'
    return bool(re.match(patron, str(rut).strip()))

def validar_fecha(fecha_str, formato):
    """Verifica que una fecha string sea parseable en el formato indicado."""
    try:
        datetime.strptime(str(fecha_str), formato)
        return True
    except (ValueError, TypeError):
        return False

def validar_rut_chileno(rut):
    """
    Valida el dígito verificador del RUT chileno usando módulo 11.
    Asume que el RUT ya tiene formato XXXXXXXX-X.
    """
    try:
        cuerpo, dv = str(rut).strip().split('-')
        cuerpo = cuerpo.replace('.', '')
        suma, factor = 0, 2
        for digito in reversed(cuerpo):
            suma += int(digito) * factor
            factor = 2 if factor == 7 else factor + 1
        resto = 11 - (suma % 11)
        if resto == 11:
            dv_calculado = '0'
        elif resto == 10:
            dv_calculado = 'K'
        else:
            dv_calculado = str(resto)
        return dv.upper() == dv_calculado
    except Exception:
        return False

def validar_edad(fecha_nacimiento, fecha_atencion):
    """Verifica que la edad esté entre 0 y 120 años."""
    try:
        fnac = datetime.strptime(str(fecha_nacimiento), '%Y-%m-%d')
        fat  = datetime.strptime(str(fecha_atencion)[:10], '%Y-%m-%d')
        edad = (fat - fnac).days / 365.25
        return 0 <= edad <= 120
    except Exception:
        return False

def validar_coherencia_fechas(fecha_nacimiento, fecha_atencion):
    """Verifica que la fecha de atención sea posterior a la de nacimiento."""
    try:
        fnac = datetime.strptime(str(fecha_nacimiento), '%Y-%m-%d')
        fat  = datetime.strptime(str(fecha_atencion)[:10], '%Y-%m-%d')
        return fat > fnac
    except Exception:
        return False

def validar_resultado_valor(valor):
    """Verifica que el resultado del examen sea un número positivo."""
    try:
        return float(valor) >= 0
    except (ValueError, TypeError):
        return False

def validar_dosis(dosis):
    """Verifica que la dosis tenga formato numérico + unidad. Ej: 100mg, 2.5ml."""
    patron = r'^\d+(\.\d+)?(mg|ml|g|mcg|UI)$'
    return bool(re.match(patron, str(dosis).strip(), re.IGNORECASE))

def validar_codigo_cie10(codigo, catalogo_cie10):
    """Verifica que el código CIE-10 exista en el catálogo oficial."""
    return str(codigo).strip() in catalogo_cie10

def validar_fecha_no_futura(fecha_str, formato):
    """Verifica que la fecha no sea posterior a hoy."""
    try:
        fecha = datetime.strptime(str(fecha_str), formato)
        return fecha <= datetime.now()
    except (ValueError, TypeError):
        return False

def validar_codigo_minsal(codigo):
    """Verifica que el código MINSAL tenga formato M + 3 dígitos. Ej: M002."""
    patron = r'^M\d{3}$'
    return bool(re.match(patron, str(codigo).strip()))

# ── MOTOR PRINCIPAL ───────────────────────────────────────────────────────────

def insertar_cuarentena(cursor, id_registro, campo, valor, motivo):
    """Inserta un registro fallido en la tabla CUARENTENA."""
    sql = """
        INSERT INTO CUARENTENA (id_registro, campo_fallido, valor_encontrado, motivo)
        VALUES (:1, :2, :3, :4)
    """
    cursor.execute(sql, [str(id_registro), str(campo), str(valor), str(motivo)])



def calcular_kpi_completitud(df):
    """
    KPI 1: Completitud por columna.
    Calcula el porcentaje de campos con datos (no nulos ni vacíos) por cada columna.
    """
    logging.info("--- KPI: COMPLETITUD POR COLUMNA ---")
    print("--- KPI: COMPLETITUD POR COLUMNA ---")
    total_filas = len(df)

    for columna in df.columns:
        nulos = df[columna].isna().sum()
        vacios = (df[columna].astype(str).str.strip() == '').sum()
        incompletos = nulos + vacios
        completitud = ((total_filas - incompletos) / total_filas) * 100
        logging.info(f"Completitud [{columna}]: {completitud:.2f}% ({incompletos} incompletos de {total_filas})")
        print(f"Completitud [{columna}]: {completitud:.2f}% ({incompletos} incompletos de {total_filas})")

    logging.info("--- FIN KPI: COMPLETITUD ---")
    print("--- FIN KPI: COMPLETITUD ---")



def calcular_kpi_errores(total, errores):
    logging.info("--- KPI: TASA DE ERROR ---")
    print("--- KPI: TASA DE ERROR ---")
    tasa_error = (errores / total) * 100
    tasa_ok = 100 - tasa_error
    logging.info(f"Registros válidos: {total - errores} ({tasa_ok:.2f}%)")
    print(f"Registros válidos: {total - errores} ({tasa_ok:.2f}%)")
    logging.info(f"Registros con error: {errores} ({tasa_error:.2f}%)")
    print(f"Registros con error: {errores} ({tasa_error:.2f}%)")
    logging.info("--- FIN KPI: TASA DE ERROR ---")
    print("--- FIN KPI: TASA DE ERROR ---")



def calcular_kpi_auditoria(errores_detalle):
    logging.info("--- KPI: AUDITORÍA DE ERRORES ---")
    print("--- KPI: AUDITORÍA DE ERRORES ---")
    conteo = {}
    for _, _, _, motivo in errores_detalle:
        conteo[motivo] = conteo.get(motivo, 0) + 1
    for motivo, cantidad in sorted(conteo.items(), key=lambda x: x[1], reverse=True):
        logging.info(f"{motivo}: {cantidad} registros")
        print(f"{motivo}: {cantidad} registros")
    logging.info("--- FIN KPI: AUDITORÍA ---")
    print("--- FIN KPI: AUDITORÍA ---")



def iniciar_validacion():
    logging.info("=== INICIO DE ETAPA 3: VALIDACIÓN ===")

    ruta_dataset = "./data/Processed/dataset_hospitales_limpio.csv"

    try:
        df = pd.read_csv(ruta_dataset)
        total = len(df)
        logging.info(f"Dataset cargado: {total} registros a validar.")

        # Cargar catálogo CIE-10
        df_cie10 = pd.read_csv("./data/CIE-10/codigos_cie10.csv")
        catalogo_cie10 = set(df_cie10['codigo'].str.strip())
        logging.info(f"Catálogo CIE-10 cargado: {len(catalogo_cie10)} códigos.")

        connection = get_connection()
        crear_tabla_cuarentena(connection)
        cursor = connection.cursor()

        errores = 0
        errores_detalle = []
        ids_atencion_vistos  = set()
        ids_examen_vistos    = set()

        for _, fila in df.iterrows():
            id_reg = fila['id_atencion']

            # 1. Formato RUT
            if not validar_formato_rut(fila['rut_paciente']):
                insertar_cuarentena(cursor, id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_FORMATO_INVALIDO')
                errores_detalle.append((id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_FORMATO_INVALIDO'))
                errores += 1

            # 2. Dígito verificador RUT
            elif not validar_rut_chileno(fila['rut_paciente']):
                insertar_cuarentena(cursor, id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_DIGITO_INVALIDO')
                errores_detalle.append((id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_DIGITO_INVALIDO'))
                errores += 1

            # 3. Fecha nacimiento
            if not validar_fecha(fila['fecha_nacimiento'], '%Y-%m-%d'):
                insertar_cuarentena(cursor, id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'FECHA_NACIMIENTO_INVALIDA')
                errores_detalle.append((id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'FECHA_NACIMIENTO_INVALIDA'))
                errores += 1

            # 4. Fecha atención
            if not validar_fecha(fila['fecha_atencion'], '%Y-%m-%d %H:%M:%S'):
                insertar_cuarentena(cursor, id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_INVALIDA')
                errores_detalle.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_INVALIDA'))
                errores += 1

            # 5. Coherencia fechas
            if not validar_coherencia_fechas(fila['fecha_nacimiento'], fila['fecha_atencion']):
                insertar_cuarentena(cursor, id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_ANTERIOR_NACIMIENTO')
                errores_detalle.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_ANTERIOR_NACIMIENTO'))
                errores += 1

            # 6. Edad
            if not validar_edad(fila['fecha_nacimiento'], fila['fecha_atencion']):
                insertar_cuarentena(cursor, id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'EDAD_FUERA_DE_RANGO')
                errores_detalle.append((id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'EDAD_FUERA_DE_RANGO'))
                errores += 1

            # 7. Sexo
            if fila['sexo'] not in SEXOS_VALIDOS:
                insertar_cuarentena(cursor, id_reg, 'sexo', fila['sexo'], 'SEXO_INVALIDO')
                errores_detalle.append((id_reg, 'sexo', fila['sexo'], 'SEXO_INVALIDO'))
                errores += 1

            # 8. Previsión
            if fila['prevision'] not in PREVISIONES_VALIDAS:
                insertar_cuarentena(cursor, id_reg, 'prevision', fila['prevision'], 'PREVISION_INVALIDA')
                errores_detalle.append((id_reg, 'prevision', fila['prevision'], 'PREVISION_INVALIDA'))
                errores += 1

            # 9. Tipo atención
            if fila['tipo_atencion'] not in TIPOS_ATENCION:
                insertar_cuarentena(cursor, id_reg, 'tipo_atencion', fila['tipo_atencion'], 'TIPO_ATENCION_INVALIDO')
                errores_detalle.append((id_reg, 'tipo_atencion', fila['tipo_atencion'], 'TIPO_ATENCION_INVALIDO'))
                errores += 1

            # 10. Resultado valor
            if not validar_resultado_valor(fila['resultado_valor']):
                insertar_cuarentena(cursor, id_reg, 'resultado_valor', fila['resultado_valor'], 'RESULTADO_VALOR_INVALIDO')
                errores_detalle.append((id_reg, 'resultado_valor', fila['resultado_valor'], 'RESULTADO_VALOR_INVALIDO'))
                errores += 1

            # 11. Dosis prescrita
            if not validar_dosis(fila['dosis_prescrita']):
                insertar_cuarentena(cursor, id_reg, 'dosis_prescrita', fila['dosis_prescrita'], 'DOSIS_FORMATO_INVALIDO')
                errores_detalle.append((id_reg, 'dosis_prescrita', fila['dosis_prescrita'], 'DOSIS_FORMATO_INVALIDO'))
                errores += 1

            # 12. Código CIE-10
            if not validar_codigo_cie10(fila['codigo_cie10'], catalogo_cie10):
                insertar_cuarentena(cursor, id_reg, 'codigo_cie10', fila['codigo_cie10'], 'CODIGO_CIE10_NO_EXISTE')
                errores_detalle.append((id_reg, 'codigo_cie10', fila['codigo_cie10'], 'CODIGO_CIE10_NO_EXISTE'))
                errores += 1

            # 13. Fecha atención no futura
            if not validar_fecha_no_futura(fila['fecha_atencion'], '%Y-%m-%d %H:%M:%S'):
                insertar_cuarentena(cursor, id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_FUTURA')
                errores_detalle.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_FUTURA'))
                errores += 1

            # 14. Código MINSAL
            if not validar_codigo_minsal(fila['codigo_minsal']):
                insertar_cuarentena(cursor, id_reg, 'codigo_minsal', fila['codigo_minsal'], 'CODIGO_MINSAL_FORMATO_INVALIDO')
                errores_detalle.append((id_reg, 'codigo_minsal', fila['codigo_minsal'], 'CODIGO_MINSAL_FORMATO_INVALIDO'))
                errores += 1

            # 15. Unicidad id_atencion
            if id_reg in ids_atencion_vistos:
                insertar_cuarentena(cursor, id_reg, 'id_atencion', id_reg, 'ID_ATENCION_DUPLICADO')
                errores_detalle.append((id_reg, 'id_atencion', id_reg, 'ID_ATENCION_DUPLICADO'))
                errores += 1
            else:
                ids_atencion_vistos.add(id_reg)

            # 16. Unicidad id_examen
            if fila['id_examen'] in ids_examen_vistos:
                insertar_cuarentena(cursor, id_reg, 'id_examen', fila['id_examen'], 'ID_EXAMEN_DUPLICADO')
                errores_detalle.append((id_reg, 'id_examen', fila['id_examen'], 'ID_EXAMEN_DUPLICADO'))
                errores += 1
            else:
                ids_examen_vistos.add(fila['id_examen'])

        calcular_kpi_completitud(df)
        calcular_kpi_errores(total, errores)
        calcular_kpi_auditoria(errores_detalle)
        connection.commit()

        registros_ok = total - errores
        logging.info(f"Validación completada: {total} registros procesados, {errores} errores enviados a CUARENTENA.")
        logging.info("=== FIN DE ETAPA 3: VALIDACIÓN ===")
        print(f"Etapa 3 completada: {registros_ok}/{total} registros válidos. {errores} errores en CUARENTENA.")

    except NotImplementedError as e:
        logging.warning(f"Conexión Oracle no disponible: {e}")
        print("⚠️  Validación lógica lista, pero la conexión Oracle está pendiente.")
    except Exception as e:
        logging.error(f"Error crítico en validación: {e}")
        print("Ocurrió un error. Revisa el archivo de logs.")



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo prueba: sin Oracle, solo lógica y KPIs en consola
        import pandas as pd
        from datetime import datetime

        print("=== MODO PRUEBA (sin Oracle) ===")
        df = pd.read_csv("./data/Processed/dataset_hospitales_limpio.csv")
        df_cie10 = pd.read_csv("./data/CIE-10/codigos_cie10.csv")
        catalogo_cie10 = set(df_cie10['codigo'].str.strip())

        errores = []
        ids_atencion_vistos = set()
        ids_examen_vistos = set()

        for _, fila in df.iterrows():
            id_reg = fila['id_atencion']

            if not validar_formato_rut(fila['rut_paciente']):
                errores.append((id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_FORMATO_INVALIDO'))
            elif not validar_rut_chileno(fila['rut_paciente']):
                errores.append((id_reg, 'rut_paciente', fila['rut_paciente'], 'RUT_DIGITO_INVALIDO'))
            if not validar_fecha(fila['fecha_nacimiento'], '%Y-%m-%d'):
                errores.append((id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'FECHA_NACIMIENTO_INVALIDA'))
            if not validar_fecha(fila['fecha_atencion'], '%Y-%m-%d %H:%M:%S'):
                errores.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_INVALIDA'))
            if not validar_coherencia_fechas(fila['fecha_nacimiento'], fila['fecha_atencion']):
                errores.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_ANTERIOR_NACIMIENTO'))
            if not validar_edad(fila['fecha_nacimiento'], fila['fecha_atencion']):
                errores.append((id_reg, 'fecha_nacimiento', fila['fecha_nacimiento'], 'EDAD_FUERA_DE_RANGO'))
            if fila['sexo'] not in SEXOS_VALIDOS:
                errores.append((id_reg, 'sexo', fila['sexo'], 'SEXO_INVALIDO'))
            if fila['prevision'] not in PREVISIONES_VALIDAS:
                errores.append((id_reg, 'prevision', fila['prevision'], 'PREVISION_INVALIDA'))
            if fila['tipo_atencion'] not in TIPOS_ATENCION:
                errores.append((id_reg, 'tipo_atencion', fila['tipo_atencion'], 'TIPO_ATENCION_INVALIDO'))
            if not validar_resultado_valor(fila['resultado_valor']):
                errores.append((id_reg, 'resultado_valor', fila['resultado_valor'], 'RESULTADO_VALOR_INVALIDO'))
            if not validar_dosis(fila['dosis_prescrita']):
                errores.append((id_reg, 'dosis_prescrita', fila['dosis_prescrita'], 'DOSIS_FORMATO_INVALIDO'))
            if not validar_codigo_cie10(fila['codigo_cie10'], catalogo_cie10):
                errores.append((id_reg, 'codigo_cie10', fila['codigo_cie10'], 'CODIGO_CIE10_NO_EXISTE'))
            if not validar_fecha_no_futura(fila['fecha_atencion'], '%Y-%m-%d %H:%M:%S'):
                errores.append((id_reg, 'fecha_atencion', fila['fecha_atencion'], 'FECHA_ATENCION_FUTURA'))
            if not validar_codigo_minsal(fila['codigo_minsal']):
                errores.append((id_reg, 'codigo_minsal', fila['codigo_minsal'], 'CODIGO_MINSAL_FORMATO_INVALIDO'))
            if id_reg in ids_atencion_vistos:
                errores.append((id_reg, 'id_atencion', id_reg, 'ID_ATENCION_DUPLICADO'))
            else:
                ids_atencion_vistos.add(id_reg)
            if fila['id_examen'] in ids_examen_vistos:
                errores.append((id_reg, 'id_examen', fila['id_examen'], 'ID_EXAMEN_DUPLICADO'))
            else:
                ids_examen_vistos.add(fila['id_examen'])

        print(f"\nTotal registros: {len(df)}")
        print(f"Total errores detectados: {len(errores)}")
        print("\nDetalle de errores:")
        for e in errores:
            print(f"  ID: {e[0]} | Campo: {e[1]} | Valor: {e[2]} | Motivo: {e[3]}")

        print()
        print()
        print(f"Filas en df: {len(df)}")
        calcular_kpi_completitud(df)
        calcular_kpi_completitud(df)
        calcular_kpi_errores(len(df), len(errores))
        calcular_kpi_auditoria(errores)
    else:
        iniciar_validacion()