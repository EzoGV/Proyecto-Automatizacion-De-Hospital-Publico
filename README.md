README.md

# Pipeline DataOps — Gestión de Registros de Pacientes
**Hospital Público | Proyecto ITY1101**

Proyecto académico desarrollado bajo la metodología DataOps para la consolidación, limpieza, validación y carga de registros médicos desde fuentes heterogéneas hacia un repositorio centralizado en Oracle Database (Autonomous Database Cloud).

---

## Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Pipeline](#arquitectura-del-pipeline)
3. [Estructura del Repositorio](#estructura-del-repositorio)
4. [Tecnologías Utilizadas](#tecnologías-utilizadas)
5. [Requisitos Previos](#requisitos-previos)
6. [Instalación y Configuración](#instalación-y-configuración)
7. [Ejecución del Pipeline](#ejecución-del-pipeline)
8. [KPIs y Métricas de Calidad](#kpis-y-métricas-de-calidad)
9. [Modelo de Datos](#modelo-de-datos)

---

## Descripción del Proyecto

Este proyecto implementa un pipeline de datos automatizado para un hospital público, con el objetivo de centralizar y garantizar la calidad de los registros de atención médica. El sistema procesa datos provenientes de múltiples fuentes (archivos CSV y Excel), aplica reglas de negocio del dominio de salud, y carga los registros validados en una base de datos Oracle Autonomous Database en la nube.

El proyecto se enmarca en la metodología **DataOps**, integrando prácticas de trazabilidad, auditoría continua y control de calidad en cada etapa del flujo de datos.

**Contexto académico:** ITY1101 — Gestion de Datos para IA.

---

## Arquitectura del Pipeline

El pipeline se compone de cuatro etapas secuenciales:

```
[Fuentes de Origen]
        |
        | CSV / XLSX
        v
+------------------+
|   1. INGESTA     |  Lee archivos desde data/origen y los mueve a data/raw
+------------------+
        |
        v
+------------------+
|   2. LIMPIEZA    |  Normaliza RUTs, fechas, nulos y duplicados
+------------------+
        |
        v
+------------------+
|   3. VALIDACION  |  Aplica 14 reglas de negocio. Separa validos/rechazados
+------------------+     |
        |                 +---> [CUARENTENA] (Oracle BD)
        v
+------------------+
|   4. CARGA       |  Inserta registros validos en Oracle con cifrado AES-256
+------------------+
        |
        v
[Oracle Autonomous Database Cloud]
  - PACIENTES
  - ATENCIONES
  - MEDICAMENTOS
  - ALERGIAS
  - EXAMENES
  - CUARENTENA
  - AUDIT_LOG
```

---

## Estructura del Repositorio

```
Proyecto-Automatizacion-De-Hospital-Publico/
|
|-- data/
|   |-- CIE-10/             # Catalogo oficial de codigos diagnosticos
|   |-- origen/             # Archivos fuente originales (CSV / XLSX)
|   |-- raw/                # Datos copiados por la etapa de Ingesta
|   |-- processed/          # Datos limpios generados por Limpieza
|   |-- validated/          # Registros aprobados por Validacion
|   |-- invalidated/        # Registros rechazados con motivo de rechazo
|
|-- src/
|   |-- Ingesta/
|   |   |-- ingesta.py      # Etapa 1: captura de archivos fuente
|   |-- Limpieza/
|   |   |-- limpieza.py     # Etapa 2: normalizacion y transformacion
|   |-- Validacion/
|   |   |-- validacion.py   # Etapa 3: validacion estructural y semantica
|   |-- Carga/
|   |   |-- carga_bd.py     # Etapa 4: insercion en Oracle con cifrado
|   |-- interfaz.py         # Panel de control GUI (customtkinter)
|
|-- wallet/                 # Wallet de conexion Oracle Cloud (no subir a git publico)
|-- RegistroLogs/           # Logs de ejecucion del pipeline
|-- .env                    # Variables de entorno (no subir a git publico)
|-- .env.example            # Plantilla de variables de entorno
|-- docker-compose.yml      # Configuracion del contenedor Oracle local
|-- requirements.txt        # Dependencias Python
|-- test.py                 # Test unitario de conexion y escritura en BD
|-- README.md
```

---

## Tecnologías Utilizadas

| Componente | Tecnologia |
|---|---|
| Base de datos | Oracle Autonomous Database (OCI) |
| Contenedor local | Docker + imagen `gvenzl/oracle-free` |
| Lenguaje | Python 3.10+ |
| Interfaz grafica | customtkinter |
| Cifrado de datos | AES-256 mediante Fernet (cryptography) |
| Procesamiento de datos | pandas, openpyxl |
| Conexion Oracle | oracledb (modo Thin) |
| Variables de entorno | python-dotenv |
| Gestion de proyecto | PMBOK + Sprints Agiles |

---

## Requisitos Previos

- Docker Desktop instalado y en ejecucion
- Python 3.10 o superior
- Git instalado
- Acceso a Oracle Cloud con wallet descargada (o instancia local via Docker)

---

## Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/Proyecto-Automatizacion-De-Hospital-Publico.git
cd Proyecto-Automatizacion-De-Hospital-Publico
```

### 2. Configurar variables de entorno

Copiar el archivo de ejemplo y completar con las credenciales reales:

```bash
cp .env.example .env
```

Editar `.env` con los valores correspondientes:

```
DB_USER=ADMIN
DB_PASSWORD=tu_password
DB_ENCRYPTION_KEY=tu_clave_fernet_base64
DB_HOST=127.0.0.1
DB_PORT=1521
DB_SERVICE=FREEPDB1
```

> La clave `DB_ENCRYPTION_KEY` debe ser una clave Fernet valida de 32 bytes en base64. Se puede generar con `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

### 3. Levantar la base de datos local (Docker)

```bash
docker compose up -d
docker ps   # Verificar que el contenedor este activo
```

### 4. Crear el entorno virtual e instalar dependencias

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```


## Ejecución del Pipeline

Cada etapa se ejecuta de forma independiente desde la raiz del proyecto. Se recomienda ejecutarlas en orden secuencial.

```bash
# Etapa 1: Ingesta
python src/Ingesta/ingesta.py

# Etapa 2: Limpieza
python src/Limpieza/limpieza.py

# Etapa 3: Validacion
python src/Validacion/validacion.py

# Etapa 4: Carga a Oracle
python src/Carga/carga_bd.py
```

Los logs de cada ejecucion quedan registrados en `RegistroLogs/pipeline_ejecucion.log`.

Para acceder al panel de control grafico:

```bash
python src/interfaz.py
```

---

## KPIs y Métricas de Calidad

El pipeline registra 14 indicadores clave de rendimiento (KPIs) distribuidos en tres etapas. Los KPIs persisten en la tabla `AUDIT_LOG` de Oracle, permitiendo trazabilidad historica de cada ejecucion.

### Etapa 2 — Limpieza

| KPI | Descripcion | Umbral |
|---|---|---|
| `REGISTROS_ENTRADA` | Total de registros consolidados antes de limpiar | Referencia |
| `DUPLICADOS_ELIMINADOS` | Cantidad de filas duplicadas removidas | 0 = OK |
| `REGISTROS_LIMPIOS` | Registros resultantes tras la limpieza | Referencia |
| `TASA_RETENCION` | Porcentaje de registros conservados | >= 95% |

### Etapa 3 — Validacion

| KPI | Descripcion | Umbral |
|---|---|---|
| `TOTAL_PROCESADOS` | Total de registros enviados a validacion | Referencia |
| `REGISTROS_VALIDOS` | Registros que superaron todas las reglas | Referencia |
| `REGISTROS_RECHAZADOS` | Registros enviados a cuarentena | 0 = OK |
| `TASA_VALIDEZ` | Porcentaje de registros validos sobre el total | >= 90% |

Adicionalmente, se calculan en logs (sin persistencia en BD):

- Completitud por columna (alerta si < 99%)
- Tasa de error general
- Auditoria de errores por tipo de motivo de rechazo

### Etapa 4 — Carga

| KPI | Descripcion | Umbral |
|---|---|---|
| `REGISTROS_INSERTADOS` | Registros cargados exitosamente en Oracle | Referencia |
| `ERRORES_BD` | Registros con fallo de integridad referencial | 0 = OK |
| `TASA_CARGA_EXITOSA` | Porcentaje de registros insertados sobre el total | >= 95% |

### Reglas de validacion aplicadas (Etapa 3)

El modulo de validacion aplica las siguientes 14 reglas sobre cada registro:

1. Formato de RUT (patron `XXXXXXXX-X`)
2. Digito verificador del RUT chileno (algoritmo Modulo 11)
3. Formato de fecha de nacimiento
4. Formato de fecha de atencion
5. Coherencia entre fecha de nacimiento y fecha de atencion
6. Edad del paciente dentro de rango valido (0-120 anos)
7. Sexo dentro de valores permitidos (M / F)
8. Prevision dentro de catalogo valido (FONASA, ISAPRE, CAPREDENA, DIPRECA, NINGUNA)
9. Tipo de atencion dentro de catalogo valido (CONSULTA, HOSPITALIZACION, PROCEDIMIENTO, URGENCIA)
10. Resultado de examen con valor numerico no negativo
11. Formato de dosis prescrita (ej: `100mg`, `5ml`)
12. Codigo CIE-10 existente en el catalogo oficial
13. Fecha de atencion no futura respecto a la fecha de ejecucion
14. Formato de codigo MINSAL (patron `MXXX`)

Los registros que fallan una o mas reglas son almacenados en la tabla `CUARENTENA` con el detalle del campo fallido y el motivo de rechazo.

---

## Modelo de Datos

Las tablas principales en Oracle son:

```
PACIENTES           ATENCIONES          MEDICAMENTOS
-----------         ----------          ------------
rut_paciente (PK)   id_atencion (PK)    id_med (PK, auto)
nombre_completo     rut_paciente (FK)   id_atencion (FK)
fecha_nacimiento    fecha_atencion      codigo_minsal
sexo                tipo_atencion       dosis_prescrita
prevision           codigo_cie10

ALERGIAS            EXAMENES            CUARENTENA
--------            --------            ----------
id_alergia (PK)     id_examen (PK)      id_registro
rut_paciente (FK)   id_atencion (FK)    campo_fallido
alergia_principio   codigo_examen       valor_encontrado
                    resultado_valor     motivo_rechazo
                    unidad_medida       timestamp_validacion

AUDIT_LOG
---------
id_log (PK, auto)
etapa_pipeline
kpi_nombre
valor_calculado
estado
timestamp_ejecucion
```

---

> Este repositorio es de uso academico. Las credenciales reales no deben subirse al repositorio. Utilizar siempre el archivo `.env` local y asegurarse de que `.gitignore` lo excluya correctamente.
