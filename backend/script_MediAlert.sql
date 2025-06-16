-- =====================================================================
-- Script para la Creación de la Estructura de la Base de Datos MediAlert
-- =====================================================================

-- ** SECCIÓN 1: LIMPIEZA INICIAL **
DROP TRIGGER IF EXISTS trg_usuarios_auditoria ON usuarios;
DROP TRIGGER IF EXISTS trg_medicamentos_auditoria ON medicamentos;
DROP TRIGGER IF EXISTS trg_alertas_auditoria ON alertas;
DROP TRIGGER IF EXISTS trg_usuarios_prevenir_delete_cliente ON usuarios;
DROP TRIGGER IF EXISTS trg_medicamentos_prevenir_delete ON medicamentos;
DROP TRIGGER IF EXISTS trg_desactivar_alertas_usuario_inactivo ON usuarios;
DROP TRIGGER IF EXISTS trg_desactivar_alertas_medicamento_discontinuado ON medicamentos;

DROP FUNCTION IF EXISTS sp_registrar_evento_auditoria(INTEGER, TEXT, NAME, TEXT, JSONB, JSONB, JSONB);
DROP FUNCTION IF EXISTS func_disparador_auditoria_generico();
DROP FUNCTION IF EXISTS func_prevenir_borrado_fisico_cliente();
DROP FUNCTION IF EXISTS func_prevenir_borrado_fisico_medicamento();
DROP FUNCTION IF EXISTS func_desactivar_alertas_usuario_inactivo();
DROP FUNCTION IF EXISTS func_desactivar_alertas_medicamento_discontinuado();

DROP TABLE IF EXISTS reportes_log CASCADE;
DROP TABLE IF EXISTS auditoria CASCADE;
DROP TABLE IF EXISTS alertas CASCADE;
DROP TABLE IF EXISTS medicamentos CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS eps CASCADE;

DROP SEQUENCE IF EXISTS eps_id_seq;
DROP SEQUENCE IF EXISTS usuarios_id_seq;
DROP SEQUENCE IF EXISTS medicamentos_id_seq;
DROP SEQUENCE IF EXISTS alertas_id_seq;
DROP SEQUENCE IF EXISTS reportes_log_id_seq;
DROP SEQUENCE IF EXISTS auditoria_id_seq;


-- ** SECCIÓN 2: CREACIÓN DE SECUENCIAS **
CREATE SEQUENCE eps_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE usuarios_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE medicamentos_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE alertas_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE auditoria_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE reportes_log_id_seq START WITH 1 INCREMENT BY 1;


-- ** SECCIÓN 3: CREACIÓN DE TABLAS **
CREATE TABLE eps (
    id INTEGER PRIMARY KEY DEFAULT nextval('eps_id_seq'),
    nombre VARCHAR(100) UNIQUE NOT NULL,
    nit VARCHAR(20) NOT NULL UNIQUE,
    logo_url VARCHAR(255) NULL,
    estado VARCHAR(10) DEFAULT 'activo' NOT NULL CHECK (estado IN ('activo', 'inactivo'))
);

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY DEFAULT nextval('usuarios_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'cliente')),
    estado_usuario VARCHAR(10) DEFAULT 'activo' NOT NULL CHECK (estado_usuario IN ('activo', 'inactivo')),
    fecha_nacimiento DATE,
    telefono VARCHAR(20),
    ciudad VARCHAR(100),
    genero VARCHAR(20) CHECK (genero IN ('Masculino', 'Femenino', 'Otro', 'Prefiero no decirlo')),
    fecha_registro DATE DEFAULT CURRENT_DATE,
    eps_id INTEGER,
    tipo_regimen VARCHAR(20) CHECK (tipo_regimen IN ('Contributivo', 'Subsidiado', 'Especial')),
    CONSTRAINT fk_usuarios_eps FOREIGN KEY (eps_id) REFERENCES eps(id) ON DELETE SET NULL
);

CREATE TABLE medicamentos (
    id INTEGER PRIMARY KEY DEFAULT nextval('medicamentos_id_seq'),
    nombre VARCHAR(150) UNIQUE NOT NULL,
    descripcion TEXT,
    composicion TEXT,
    sintomas_secundarios TEXT,
    indicaciones TEXT,
    rango_edad VARCHAR(50),
    estado_medicamento VARCHAR(15) DEFAULT 'disponible' NOT NULL CHECK (estado_medicamento IN ('disponible', 'discontinuado'))
);

CREATE TABLE alertas (
    id INTEGER PRIMARY KEY DEFAULT nextval('alertas_id_seq'),
    usuario_id INT NOT NULL,
    medicamento_id INT NOT NULL,
    dosis VARCHAR(100),
    frecuencia VARCHAR(100),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    hora_preferida TIME,
    ultima_notificacion_enviada TIMESTAMP WITH TIME ZONE,
    estado VARCHAR(20) DEFAULT 'activa' NOT NULL CHECK (estado IN ('activa', 'inactiva', 'completada', 'fallida')),
    asignado_por_usuario_id INTEGER,
    CONSTRAINT fk_alertas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    CONSTRAINT fk_alertas_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE CASCADE,
    CONSTRAINT fk_alertas_asignador FOREIGN KEY (asignado_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);

CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY DEFAULT nextval('auditoria_id_seq'),
    usuario_id_app INTEGER,
    usuario_db NAME DEFAULT current_user,
    accion TEXT NOT NULL,
    tabla_afectada NAME,
    registro_id_afectado TEXT,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    detalles_adicionales JSONB,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reportes_log (
    id INTEGER PRIMARY KEY DEFAULT nextval('reportes_log_id_seq'),
    tipo_reporte VARCHAR(100) NOT NULL,
    nombre_reporte VARCHAR(255) NOT NULL,
    pdf_filename VARCHAR(255) UNIQUE NOT NULL,
    generado_por_usuario_id INTEGER,
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reportes_log_usuario FOREIGN KEY (generado_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);


-- ** SECCIÓN 4: ÍNDICES **
CREATE INDEX idx_usuarios_eps_id ON usuarios(eps_id);
CREATE INDEX idx_alertas_usuario_id ON alertas(usuario_id);
CREATE INDEX idx_alertas_medicamento_id ON alertas(medicamento_id);
CREATE INDEX idx_alertas_asignado_por_id ON alertas(asignado_por_usuario_id);
CREATE INDEX idx_reportes_log_generado_por_id ON reportes_log(generado_por_usuario_id);
CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_alertas_estado ON alertas(estado);


-- ** SECCIÓN 5: FUNCIONES Y LÓGICA DE NEGOCIO **
CREATE OR REPLACE FUNCTION sp_registrar_evento_auditoria(
    p_usuario_id_app INTEGER, p_accion TEXT, p_tabla_afectada NAME DEFAULT NULL,
    p_registro_id_afectado TEXT DEFAULT NULL, p_datos_anteriores JSONB DEFAULT NULL,
    p_datos_nuevos JSONB DEFAULT NULL, p_detalles_adicionales JSONB DEFAULT NULL
) RETURNS VOID LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    INSERT INTO auditoria (
        usuario_id_app, accion, tabla_afectada, registro_id_afectado,
        datos_anteriores, datos_nuevos, detalles_adicionales
    ) VALUES (
        p_usuario_id_app, p_accion, p_tabla_afectada, p_registro_id_afectado,
        p_datos_anteriores, p_datos_nuevos, p_detalles_adicionales
    );
END;
$$;

CREATE OR REPLACE FUNCTION func_disparador_auditoria_generico()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    v_usuario_id_app INTEGER;
    v_registro_id_afectado TEXT;
    v_datos_anteriores JSONB := NULL;
    v_datos_nuevos JSONB := NULL;
BEGIN
    BEGIN
        v_usuario_id_app := current_setting('medialert.app_user_id', true)::INTEGER;
    EXCEPTION WHEN OTHERS THEN
        v_usuario_id_app := NULL;
    END;

    IF (TG_OP = 'INSERT') THEN
        v_datos_nuevos := to_jsonb(NEW);
        v_registro_id_afectado := NEW.id::TEXT;
    ELSIF (TG_OP = 'UPDATE') THEN
        v_datos_anteriores := to_jsonb(OLD);
        v_datos_nuevos := to_jsonb(NEW);
        v_registro_id_afectado := NEW.id::TEXT;
    ELSIF (TG_OP = 'DELETE') THEN
        v_datos_anteriores := to_jsonb(OLD);
        v_registro_id_afectado := OLD.id::TEXT;
    END IF;

    PERFORM sp_registrar_evento_auditoria(
        p_usuario_id_app       := v_usuario_id_app,
        p_accion               := TG_OP::TEXT,
        p_tabla_afectada       := TG_TABLE_NAME::NAME,
        p_registro_id_afectado := v_registro_id_afectado,
        p_datos_anteriores     := v_datos_anteriores,
        p_datos_nuevos         := v_datos_nuevos
    );
    RETURN COALESCE(NEW, OLD);
END;
$$;

CREATE OR REPLACE FUNCTION func_prevenir_borrado_fisico_cliente()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    IF OLD.rol = 'cliente' THEN
        RAISE NOTICE 'El borrado físico de clientes (ID: %) está prevenido. Actualice su estado a "inactivo" en su lugar.', OLD.id;
        RETURN NULL;
    END IF;
    RETURN OLD;
END;
$$;

CREATE OR REPLACE FUNCTION func_prevenir_borrado_fisico_medicamento()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    RAISE NOTICE 'El borrado físico de medicamentos (ID: %) está prevenido. Actualice su estado a "discontinuado" en su lugar.', OLD.id;
    RETURN NULL;
END;
$$;

CREATE OR REPLACE FUNCTION func_desactivar_alertas_usuario_inactivo()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    IF NEW.rol = 'cliente' AND NEW.estado_usuario = 'inactivo' AND OLD.estado_usuario = 'activo' THEN
        UPDATE alertas SET estado = 'inactiva' WHERE usuario_id = NEW.id AND estado = 'activa';
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION func_desactivar_alertas_medicamento_discontinuado()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
    IF NEW.estado_medicamento = 'discontinuado' AND OLD.estado_medicamento = 'disponible' THEN
        UPDATE alertas SET estado = 'inactiva' WHERE medicamento_id = NEW.id AND estado = 'activa';
    END IF;
    RETURN NEW;
END;
$$;

-- ** SECCIÓN 6: DISPARADORES (TRIGGERS) **
CREATE TRIGGER trg_usuarios_auditoria
AFTER INSERT OR UPDATE OR DELETE ON usuarios
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

CREATE TRIGGER trg_medicamentos_auditoria
AFTER INSERT OR UPDATE OR DELETE ON medicamentos
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

CREATE TRIGGER trg_alertas_auditoria
AFTER INSERT OR UPDATE OR DELETE ON alertas
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

CREATE TRIGGER trg_usuarios_prevenir_delete_cliente
BEFORE DELETE ON usuarios
FOR EACH ROW EXECUTE FUNCTION func_prevenir_borrado_fisico_cliente();

CREATE TRIGGER trg_medicamentos_prevenir_delete
BEFORE DELETE ON medicamentos
FOR EACH ROW EXECUTE FUNCTION func_prevenir_borrado_fisico_medicamento();

CREATE TRIGGER trg_desactivar_alertas_usuario_inactivo
AFTER UPDATE OF estado_usuario ON usuarios
FOR EACH ROW EXECUTE FUNCTION func_desactivar_alertas_usuario_inactivo();

CREATE TRIGGER trg_desactivar_alertas_medicamento_discontinuado
AFTER UPDATE OF estado_medicamento ON medicamentos
FOR EACH ROW EXECUTE FUNCTION func_desactivar_alertas_medicamento_discontinuado();
