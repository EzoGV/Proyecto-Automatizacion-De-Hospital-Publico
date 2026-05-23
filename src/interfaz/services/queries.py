BUSCAR_PACIENTE = """
SELECT
    p.rut_paciente,
    p.nombre_completo,
    p.fecha_nacimiento,
    p.sexo,
    p.prevision
FROM PACIENTES p
WHERE p.rut_paciente = :rut
"""

BUSCAR_ATENCIONES = """
SELECT
    id_atencion,
    fecha_atencion,
    tipo_atencion,
    codigo_cie10
FROM ATENCIONES
WHERE rut_paciente = :rut
ORDER BY fecha_atencion DESC
"""

BUSCAR_ALERGIAS = """
SELECT
    alergia_principio
FROM ALERGIAS
WHERE rut_paciente = :rut
"""

BUSCAR_MEDICAMENTOS = """
SELECT
    m.codigo_minsal,
    m.dosis_prescrita,
    a.fecha_atencion
FROM MEDICAMENTOS m
JOIN ATENCIONES a
ON m.id_atencion = a.id_atencion
WHERE a.rut_paciente = :rut
"""

BUSCAR_EXAMENES = """
SELECT
    e.codigo_examen,
    e.resultado_valor,
    e.unidad_medida
FROM EXAMENES e
JOIN ATENCIONES a
ON e.id_atencion = a.id_atencion
WHERE a.rut_paciente = :rut
"""

# =========================
# AUDITORÍA
# =========================

OBTENER_CUARENTENA = """
SELECT
    id_registro,
    campo_fallido,
    valor_encontrado,
    motivo_rechazo,
    timestamp_validacion
FROM CUARENTENA
ORDER BY timestamp_validacion DESC
"""

OBTENER_ERRORES_VALIDACION = """
SELECT
    campo,
    valor_incorrecto,
    fila_id,
    motivo_rechazo
FROM errores_validacion
"""

KPI_TOTAL_PACIENTES = """
SELECT COUNT(*) AS total
FROM PACIENTES
"""

KPI_TOTAL_ATENCIONES = """
SELECT COUNT(*) AS total
FROM ATENCIONES
"""

KPI_TOTAL_ERRORES = """
SELECT COUNT(*) AS total
FROM errores_validacion
"""

KPI_TOTAL_CUARENTENA = """
SELECT COUNT(*) AS total
FROM CUARENTENA
"""