-- Borra las tablas existentes para empezar de cero (opcional, pero recomendado para esta nueva versión)
DROP TABLE IF EXISTS reportes, alertas, medicamentos, usuarios;

-- Tabla de Usuarios con roles
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'cliente')) -- 'admin' o 'cliente'
);

-- Tabla de Medicamentos
CREATE TABLE medicamentos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    composicion TEXT,
    sintomas_secundarios TEXT,
    indicaciones TEXT,
    rango_edad VARCHAR(50)
);

-- Tabla de Alertas (conecta usuarios con medicamentos)
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    medicamento_id INT NOT NULL REFERENCES medicamentos(id) ON DELETE CASCADE,
    dosis VARCHAR(100),
    frecuencia VARCHAR(100),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    estado VARCHAR(20) DEFAULT 'activa' -- 'activa', 'inactiva', 'completada'
);

-- Tabla de Reportes/Auditoría
CREATE TABLE reportes (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMPTZ DEFAULT NOW(),
    accion VARCHAR(255),
    detalle TEXT,
    realizado_por INT REFERENCES usuarios(id) -- Quién hizo el cambio
);