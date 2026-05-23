-- =====================================================
-- TABLA USUARIOS
-- =====================================================

CREATE TABLE USUARIOS (
    id_usuario NUMBER GENERATED ALWAYS AS IDENTITY,
    username VARCHAR2(50) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    rol VARCHAR2(30) NOT NULL,
    PRIMARY KEY(id_usuario)
);

-- =====================================================
-- TABLA LOG ACCESOS
-- =====================================================

CREATE TABLE LOG_ACCESOS (
    id_log NUMBER GENERATED ALWAYS AS IDENTITY,
    usuario VARCHAR2(50),
    accion VARCHAR2(200),
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id_log)
);

-- =====================================================
-- TABLA KPI PIPELINE
-- =====================================================

CREATE TABLE KPI_PIPELINE (
    id_kpi NUMBER GENERATED ALWAYS AS IDENTITY,
    fecha_ejecucion TIMESTAMP,
    total_registros NUMBER,
    registros_validos NUMBER,
    registros_invalidos NUMBER,
    tasa_error NUMBER,
    PRIMARY KEY(id_kpi)
);