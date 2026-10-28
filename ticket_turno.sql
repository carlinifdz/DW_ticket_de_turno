
CREATE DATABASE IF NOT EXISTS ticket_turno
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE ticket_turno;

-- ==========================================
-- 1. TABLA DE USUARIOS ADMINISTRADORES
-- ==========================================
CREATE TABLE usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ==========================================
-- 2. TABLA DE MUNICIPIOS
-- ==========================================
CREATE TABLE municipios (
    id_municipio INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    ultimo_turno INT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_ultimo_turno
        CHECK (ultimo_turno >= 0)
) ENGINE=InnoDB;

-- ==========================================
-- 3. TABLA DE NIVELES EDUCATIVOS
-- ==========================================
CREATE TABLE niveles_educativos (
    id_nivel INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- ==========================================
-- 4. TABLA DE ASUNTOS
-- ==========================================
CREATE TABLE asuntos (
    id_asunto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
) ENGINE=InnoDB;

-- ==========================================
-- 5. TABLA DE SOLICITUDES
-- ==========================================
CREATE TABLE solicitudes (
    id_solicitud INT AUTO_INCREMENT PRIMARY KEY,

    responsable VARCHAR(150) NOT NULL,
    curp CHAR(18) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    paterno VARCHAR(100) NOT NULL,
    materno VARCHAR(100),

    telefono VARCHAR(10),
    celular VARCHAR(10),
    correo VARCHAR(150),

    id_nivel INT NOT NULL,
    id_asunto INT NOT NULL,
    id_municipio INT NOT NULL,

    estatus ENUM('Pendiente', 'Resuelto')
        NOT NULL DEFAULT 'Pendiente',

    fecha_solicitud DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    fecha_actualizacion DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_solicitud_nivel
        FOREIGN KEY (id_nivel)
        REFERENCES niveles_educativos(id_nivel),

    CONSTRAINT fk_solicitud_asunto
        FOREIGN KEY (id_asunto)
        REFERENCES asuntos(id_asunto),

    CONSTRAINT fk_solicitud_municipio
        FOREIGN KEY (id_municipio)
        REFERENCES municipios(id_municipio),

    INDEX idx_curp (curp),
    INDEX idx_nombre (nombre, paterno, materno),
    INDEX idx_municipio_estatus (id_municipio, estatus),

    UNIQUE KEY uq_solicitud_municipio
        (id_solicitud, id_municipio)
) ENGINE=InnoDB;

-- ==========================================
-- 6. TABLA DE TURNOS
-- ==========================================
CREATE TABLE turnos (
    id_turno INT AUTO_INCREMENT PRIMARY KEY,

    id_solicitud INT NOT NULL UNIQUE,
    id_municipio INT NOT NULL,

    numero_turno INT NOT NULL,
    folio VARCHAR(30) NOT NULL UNIQUE,

    fecha_asignacion DATETIME NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_turno_solicitud_municipio
        FOREIGN KEY (id_solicitud, id_municipio)
        REFERENCES solicitudes(id_solicitud, id_municipio),

    CONSTRAINT fk_turno_municipio
        FOREIGN KEY (id_municipio)
        REFERENCES municipios(id_municipio),

    CONSTRAINT uq_turno_municipio
        UNIQUE (id_municipio, numero_turno),

    CONSTRAINT chk_numero_turno
        CHECK (numero_turno >= 1)
) ENGINE=InnoDB;

-- ==========================================
-- 7. DATOS INICIALES: MUNICIPIOS
-- ==========================================
INSERT INTO municipios (nombre)
VALUES
('Saltillo'),
('Torreón'),
('Ramos Arizpe');

-- ==========================================
-- 8. DATOS INICIALES: NIVELES
-- ==========================================
INSERT INTO niveles_educativos (nombre)
VALUES
('Preescolar'),
('Primaria'),
('Secundaria'),
('Preparatoria');

-- ==========================================
-- 9. DATOS INICIALES: ASUNTOS
-- ==========================================
INSERT INTO asuntos (nombre)
VALUES
('Inscripción'),
('Cambio de escuela'),
('Documentación'),
('Información general');
