# backend/init_db.py
import psycopg2
import os
import random # Importar random para la selección aleatoria de EPS
from datetime import date, datetime, timedelta # Importar date

# --- Configuración de la Conexión a la Base de Datos ---
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_DB = os.getenv('PG_DB', 'medialert')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASS = os.getenv('PG_PASS', '0102')  # ¡Usa tu contraseña real o una variable de entorno!
PG_PORT = os.getenv('PG_PORT', '5432')

# --- Comandos SQL para crear la estructura de la base de datos ---
SQL_COMMANDS = """
-- Borra las tablas y secuencias existentes para empezar de cero
DROP TABLE IF EXISTS reportes, alertas, medicamentos, usuarios, auditoria, reportes_log, eps CASCADE; /* MODIFICADO: Añadido eps */
DROP SEQUENCE IF EXISTS usuarios_id_seq, medicamentos_id_seq, alertas_id_seq, auditoria_id_seq, reportes_log_id_seq, eps_id_seq; /* MODIFICADO: Añadido eps_id_seq */

--------------------------------------------------------------------------------
-- SECCIÓN: SECUENCIAS
-- Descripción: Secuencias para la generación de IDs autonuméricos.
--------------------------------------------------------------------------------
CREATE SEQUENCE usuarios_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE medicamentos_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE alertas_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE auditoria_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE reportes_log_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE eps_id_seq START WITH 1 INCREMENT BY 1; /* NUEVO */

--------------------------------------------------------------------------------
-- SECCIÓN: TABLAS
--------------------------------------------------------------------------------

-- Tabla: eps
-- Descripción: Listado de Entidades Promotoras de Salud (EPS) colombianas.
CREATE TABLE eps ( /* NUEVO */
    id INTEGER PRIMARY KEY DEFAULT nextval('eps_id_seq'),
    nombre VARCHAR(100) UNIQUE NOT NULL,
    nit VARCHAR(20) UNIQUE,
    estado VARCHAR(10) DEFAULT 'activo' NOT NULL CHECK (estado IN ('activo', 'inactivo'))
);
COMMENT ON TABLE eps IS 'Listado de Entidades Promotoras de Salud (EPS) colombianas.';
COMMENT ON COLUMN eps.id IS 'Identificador único de la EPS (autonumérico).';
COMMENT ON COLUMN eps.nombre IS 'Nombre de la EPS.';
COMMENT ON COLUMN eps.nit IS 'Número de Identificación Tributaria de la EPS.';
COMMENT ON COLUMN eps.estado IS 'Estado de la EPS (activo o inactivo).';


-- Tabla: usuarios
-- Descripción: Almacena la información de los usuarios del sistema.
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY DEFAULT nextval('usuarios_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'cliente')),
    estado_usuario VARCHAR(10) DEFAULT 'activo' NOT NULL CHECK (estado_usuario IN ('activo', 'inactivo')),
    fecha_nacimiento DATE,          -- NUEVO CAMPO
    telefono VARCHAR(20),           -- NUEVO CAMPO
    ciudad VARCHAR(100),            -- NUEVO CAMPO (o localidad si prefieres ese nombre)
    fecha_registro DATE DEFAULT CURRENT_DATE, -- NUEVO CAMPO (con valor por defecto)
    eps_id INTEGER, /* NUEVO */
    CONSTRAINT fk_usuarios_eps FOREIGN KEY (eps_id) REFERENCES eps(id) ON DELETE SET NULL /* NUEVO */
);
COMMENT ON TABLE usuarios IS 'Almacena la información de los usuarios del sistema, incluyendo administradores y clientes.';
COMMENT ON COLUMN usuarios.id IS 'Identificador único del usuario (autonumérico).';
COMMENT ON COLUMN usuarios.rol IS 'Define el rol del usuario dentro del sistema (admin o cliente).';
COMMENT ON COLUMN usuarios.cedula IS 'Número de cédula del usuario, debe ser único.';
COMMENT ON COLUMN usuarios.estado_usuario IS 'Estado del usuario. Para clientes, "inactivo" significa borrado lógico y cesarán sus notificaciones de alerta.';
COMMENT ON COLUMN usuarios.fecha_nacimiento IS 'Fecha de nacimiento del usuario.';
COMMENT ON COLUMN usuarios.telefono IS 'Número de teléfono del usuario.';
COMMENT ON COLUMN usuarios.ciudad IS 'Ciudad de residencia del usuario.';
COMMENT ON COLUMN usuarios.fecha_registro IS 'Fecha en que el usuario fue registrado en el sistema.';
COMMENT ON COLUMN usuarios.eps_id IS 'Referencia a la EPS a la que pertenece el usuario.'; /* NUEVO */


-- Tabla: medicamentos
-- Descripción: Catálogo de medicamentos disponibles.
CREATE TABLE medicamentos (
    id INTEGER PRIMARY KEY DEFAULT nextval('medicamentos_id_seq'),
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    composicion TEXT,
    sintomas_secundarios TEXT,
    indicaciones TEXT,
    rango_edad VARCHAR(50),
    estado_medicamento VARCHAR(15) DEFAULT 'disponible' NOT NULL CHECK (estado_medicamento IN ('disponible', 'discontinuado'))
);
COMMENT ON TABLE medicamentos IS 'Catálogo de todos los medicamentos registrados en el sistema. Incluye estado para borrado lógico o discontinuación.';
COMMENT ON COLUMN medicamentos.id IS 'Identificador único del medicamento (autonumérico).';
COMMENT ON COLUMN medicamentos.nombre IS 'Nombre comercial del medicamento, debe ser único.';
COMMENT ON COLUMN medicamentos.estado_medicamento IS 'Estado actual del medicamento. "discontinuado" implica que no se generarán nuevas alertas y las existentes se inactivarán.';


-- Tabla: alertas
-- Descripción: Define las alertas de medicamentos para los usuarios.
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY DEFAULT nextval('alertas_id_seq'),
    usuario_id INT NOT NULL,
    medicamento_id INT NOT NULL,
    dosis VARCHAR(100),
    frecuencia VARCHAR(100),        -- Ej: 'Cada 8 horas', 'Una vez al día antes de dormir'
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,                 -- NULL si la alerta es indefinida
    hora_preferida TIME,            -- Hora específica para la notificación (opcional)
    ultima_notificacion_enviada TIMESTAMP WITH TIME ZONE, -- Para control de envío de notificaciones
    estado VARCHAR(20) DEFAULT 'activa' NOT NULL CHECK (estado IN ('activa', 'inactiva', 'completada', 'fallida')), -- 'fallida' si no se pudo notificar
    asignado_por_usuario_id INTEGER, /* NUEVO */
    CONSTRAINT fk_alertas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE NO ACTION,
    CONSTRAINT fk_alertas_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE NO ACTION,
    CONSTRAINT fk_alertas_asignador FOREIGN KEY (asignado_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL /* NUEVO */
);
COMMENT ON TABLE alertas IS 'Registra las alertas de medicamentos programadas para cada usuario cliente.';
COMMENT ON COLUMN alertas.id IS 'Identificador único de la alerta (autonumérico).';
COMMENT ON COLUMN alertas.usuario_id IS 'Referencia al usuario que recibe la alerta.';
COMMENT ON COLUMN alertas.medicamento_id IS 'Referencia al medicamento de la alerta.';
COMMENT ON COLUMN alertas.estado IS 'Estado actual de la alerta (activa, inactiva por usuario/medicamento, completada, fallida).';
COMMENT ON COLUMN alertas.hora_preferida IS 'Hora específica del día en que el usuario prefiere recibir la notificación para esta alerta.';
COMMENT ON COLUMN alertas.ultima_notificacion_enviada IS 'Timestamp de la última vez que se intentó enviar una notificación para esta alerta.';
COMMENT ON COLUMN alertas.asignado_por_usuario_id IS 'ID del usuario (administrador) que asignó o modificó la alerta.'; /* NUEVO */


-- Tabla: auditoria
-- Descripción: Registra todas las acciones y cambios importantes en el sistema.
CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY DEFAULT nextval('auditoria_id_seq'),
    usuario_id_app INTEGER,
    usuario_db NAME DEFAULT current_user,
    accion TEXT NOT NULL, -- Cambiado a TEXT para ser consistente con la función
    tabla_afectada NAME, -- Cambiado a NAME para ser consistente con la función
    registro_id_afectado TEXT,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    detalles_adicionales JSONB,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE auditoria IS 'Tabla centralizada para registrar eventos de auditoría del sistema.';

-- Tabla: reportes_log
-- Descripción: Registra los eventos de generación de reportes y el PDF almacenado.
CREATE TABLE reportes_log (
    id INTEGER PRIMARY KEY DEFAULT nextval('reportes_log_id_seq'),
    tipo_reporte VARCHAR(100) NOT NULL,
    nombre_reporte VARCHAR(255) NOT NULL,
    pdf_filename VARCHAR(255) UNIQUE NOT NULL, -- Nombre de archivo único del PDF almacenado
    generado_por_usuario_id INTEGER,
    fecha_generacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reportes_log_usuario FOREIGN KEY (generado_por_usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);
COMMENT ON TABLE reportes_log IS 'Registra los eventos de generación de reportes y la referencia al PDF almacenado en el servidor.';
COMMENT ON COLUMN reportes_log.tipo_reporte IS 'Identificador programático del tipo de reporte, ej: "usuarios", "medicamentos".';
COMMENT ON COLUMN reportes_log.nombre_reporte IS 'Nombre descriptivo del reporte generado, ej: "Reporte de Usuarios del Sistema".';
COMMENT ON COLUMN reportes_log.pdf_filename IS 'Nombre de archivo único (UUID.pdf) del PDF almacenado en el servidor.';
COMMENT ON COLUMN reportes_log.generado_por_usuario_id IS 'ID del usuario administrador que generó el reporte.';
--------------------------------------------------------------------------------
-- SECCIÓN: FUNCIONES DE POSTGRESQL
--------------------------------------------------------------------------------

-- Función: sp_registrar_evento_auditoria
-- Descripción: Función genérica para insertar registros en la tabla de auditoría.
CREATE OR REPLACE FUNCTION sp_registrar_evento_auditoria(
    p_usuario_id_app INTEGER,
    p_accion TEXT, -- Tipo consistente con la tabla auditoria.accion
    p_tabla_afectada NAME DEFAULT NULL, -- Tipo consistente con la tabla auditoria.tabla_afectada
    p_registro_id_afectado TEXT DEFAULT NULL,
    p_datos_anteriores JSONB DEFAULT NULL,
    p_datos_nuevos JSONB DEFAULT NULL,
    p_detalles_adicionales JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO auditoria (
        usuario_id_app,
        accion,
        tabla_afectada,
        registro_id_afectado,
        datos_anteriores,
        datos_nuevos,
        detalles_adicionales
    )
    VALUES (
        p_usuario_id_app,
        p_accion,
        p_tabla_afectada,
        p_registro_id_afectado,
        p_datos_anteriores,
        p_datos_nuevos,
        p_detalles_adicionales
    );
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION sp_registrar_evento_auditoria IS 'Inserta un nuevo registro en la tabla de auditoría. Puede ser invocada desde la aplicación o desde triggers/funciones de base de datos.';


-- Función: func_disparador_auditoria_generico
-- Descripción: Función de trigger genérica para auditar operaciones INSERT, UPDATE, DELETE.
CREATE OR REPLACE FUNCTION func_disparador_auditoria_generico()
RETURNS TRIGGER AS $$
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
        p_accion               := TG_OP::TEXT, -- Cast TG_OP to TEXT
        p_tabla_afectada       := TG_TABLE_NAME::NAME, -- Cast TG_TABLE_NAME to NAME
        p_registro_id_afectado := v_registro_id_afectado,
        p_datos_anteriores     := v_datos_anteriores,
        p_datos_nuevos         := v_datos_nuevos,
        p_detalles_adicionales := NULL::JSONB
    );

    RETURN NULL; 
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION func_disparador_auditoria_generico IS 'Función de trigger reutilizable para registrar cambios (INSERT, UPDATE, DELETE) en tablas auditadas.';


-- Función: func_prevenir_borrado_fisico_cliente
-- Descripción: Previene el borrado físico de usuarios con rol 'cliente'.
CREATE OR REPLACE FUNCTION func_prevenir_borrado_fisico_cliente()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.rol = 'cliente' THEN
        PERFORM sp_registrar_evento_auditoria(
            p_usuario_id_app       := current_setting('medialert.app_user_id', true)::INTEGER,
            p_accion               := 'INTENTO_BORRADO_FISICO_CLIENTE_PREVENIDO'::TEXT,
            p_tabla_afectada       := TG_TABLE_NAME::NAME,
            p_registro_id_afectado := OLD.id::TEXT,
            p_datos_anteriores     := to_jsonb(OLD),
            p_datos_nuevos         := NULL::JSONB,
            p_detalles_adicionales := NULL::JSONB
        );
        RAISE NOTICE 'El borrado físico de clientes (ID: %) está prevenido. Actualice su estado a "inactivo" en su lugar.', OLD.id;
        RETURN NULL; 
    END IF;
    RETURN OLD; 
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION func_prevenir_borrado_fisico_cliente IS 'Previene el DELETE físico de usuarios con rol "cliente".';


-- Función: func_prevenir_borrado_fisico_medicamento
-- Descripción: Previene el borrado físico de medicamentos.
CREATE OR REPLACE FUNCTION func_prevenir_borrado_fisico_medicamento()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM sp_registrar_evento_auditoria(
        p_usuario_id_app       := current_setting('medialert.app_user_id', true)::INTEGER,
        p_accion               := 'INTENTO_BORRADO_FISICO_MEDICAMENTO_PREVENIDO'::TEXT,
        p_tabla_afectada       := TG_TABLE_NAME::NAME,
        p_registro_id_afectado := OLD.id::TEXT,
        p_datos_anteriores     := to_jsonb(OLD),
        p_datos_nuevos         := NULL::JSONB,
        p_detalles_adicionales := NULL::JSONB
    );
    RAISE NOTICE 'El borrado físico de medicamentos (ID: %) está prevenido. Actualice su estado a "discontinuado" en su lugar.', OLD.id;
    RETURN NULL; 
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION func_prevenir_borrado_fisico_medicamento IS 'Previene el DELETE físico de medicamentos.';

-- Función: func_desactivar_alertas_usuario_inactivo
-- Descripción: Cuando un usuario cliente se marca como 'inactivo', sus alertas 'activas' se marcan como 'inactivas'.
CREATE OR REPLACE FUNCTION func_desactivar_alertas_usuario_inactivo()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.rol = 'cliente' AND NEW.estado_usuario = 'inactivo' AND OLD.estado_usuario = 'activo' THEN
        UPDATE alertas
        SET estado = 'inactiva'
        WHERE usuario_id = NEW.id AND estado = 'activa';

        PERFORM sp_registrar_evento_auditoria(
            p_usuario_id_app       := current_setting('medialert.app_user_id', true)::INTEGER,
            p_accion               := 'DESACTIVACION_MASIVA_ALERTAS_POR_USUARIO_INACTIVO'::TEXT,
            p_tabla_afectada       := 'alertas'::NAME, 
            p_registro_id_afectado := NEW.id::TEXT, 
            p_datos_anteriores     := NULL::JSONB, 
            p_datos_nuevos         := NULL::JSONB, 
            p_detalles_adicionales := jsonb_build_object('usuario_inactivado_id', NEW.id, 'usuario_nombre', NEW.nombre)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION func_desactivar_alertas_usuario_inactivo IS 'Desactiva alertas pendientes cuando un usuario cliente se marca como inactivo.';

-- Función: func_desactivar_alertas_medicamento_discontinuado
-- Descripción: Cuando un medicamento se marca como 'discontinuado', sus alertas 'activas' se marcan como 'inactivas'.
CREATE OR REPLACE FUNCTION func_desactivar_alertas_medicamento_discontinuado()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.estado_medicamento = 'discontinuado' AND OLD.estado_medicamento = 'disponible' THEN
        UPDATE alertas
        SET estado = 'inactiva'
        WHERE medicamento_id = NEW.id AND estado = 'activa';

        PERFORM sp_registrar_evento_auditoria(
            p_usuario_id_app       := current_setting('medialert.app_user_id', true)::INTEGER,
            p_accion               := 'DESACTIVACION_MASIVA_ALERTAS_POR_MEDICAMENTO_DISCONTINUADO'::TEXT,
            p_tabla_afectada       := 'alertas'::NAME,
            p_registro_id_afectado := NEW.id::TEXT, 
            p_datos_anteriores     := NULL::JSONB, 
            p_datos_nuevos         := NULL::JSONB, 
            p_detalles_adicionales := jsonb_build_object('medicamento_discontinuado_id', NEW.id, 'medicamento_nombre', NEW.nombre)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION func_desactivar_alertas_medicamento_discontinuado IS 'Desactiva alertas pendientes cuando un medicamento se marca como discontinuado.';


--------------------------------------------------------------------------------
-- SECCIÓN: DISPARADORES (TRIGGERS)
--------------------------------------------------------------------------------

CREATE TRIGGER trg_usuarios_auditoria
AFTER INSERT OR UPDATE ON usuarios
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

CREATE TRIGGER trg_medicamentos_auditoria
AFTER INSERT OR UPDATE ON medicamentos
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
FOR EACH ROW
EXECUTE FUNCTION func_desactivar_alertas_usuario_inactivo();

CREATE TRIGGER trg_desactivar_alertas_medicamento_discontinuado
AFTER UPDATE OF estado_medicamento ON medicamentos 
FOR EACH ROW
EXECUTE FUNCTION func_desactivar_alertas_medicamento_discontinuado();

--------------------------------------------------------------------------------
-- SECCIÓN: DATOS INICIALES (PARA PRUEBAS)
--------------------------------------------------------------------------------

-- Datos iniciales de EPS
INSERT INTO eps (nombre, nit, estado) VALUES
('Nueva EPS', '8301086054', 'activo'),
('Sura EPS', '8909031357', 'activo'),
('Sanitas EPS', '8605136814', 'activo'),
('Compensar EPS', '8600667017', 'activo'),
('Coosalud EPS', '8002047247', 'activo'),
('Salud Total EPS', '8001021464', 'activo'),
('Famisanar EPS', '8605330366', 'activo')
ON CONFLICT (nombre) DO NOTHING;


INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario) VALUES
('Administrador Principal', 'admin001', 'admin@medialert.co', 'hash_contrasena_admin', 'admin', 'activo'),
('Cliente Activo Ejemplo', 'user001', 'cliente1@example.com', 'hash_contrasena_cliente1', 'cliente', 'activo'),
('Cliente Para Inactivar', 'user002', 'cliente2@example.com', 'hash_contrasena_cliente2', 'cliente', 'activo'),
('Cliente Ya Inactivo', 'user003', 'cliente3@example.com', 'hash_contrasena_cliente3', 'cliente', 'inactivo')
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO medicamentos (nombre, descripcion, estado_medicamento) VALUES
('Analgex 500mg', 'Alivio del dolor y fiebre.', 'disponible'),
('CardioVital 10mg', 'Tratamiento hipertensión.', 'disponible'),
('Resfriol Forte', 'Para síntomas de resfrío.', 'disponible'),
('Antibiotix Max (Obsoleto)', 'Antibiótico de amplio espectro.', 'discontinuado')
ON CONFLICT (nombre) DO NOTHING;

DO $$
DECLARE
    v_usuario_activo_id INTEGER;
    v_usuario_a_inactivar_id INTEGER;
    v_medicamento_analgex_id INTEGER;
    v_medicamento_cardio_id INTEGER;
    v_admin_id INTEGER; /* NUEVO: Para la firma */
BEGIN
    SELECT id INTO v_usuario_activo_id FROM usuarios WHERE cedula = 'user001';
    SELECT id INTO v_usuario_a_inactivar_id FROM usuarios WHERE cedula = 'user002';
    SELECT id INTO v_medicamento_analgex_id FROM medicamentos WHERE nombre = 'Analgex 500mg';
    SELECT id INTO v_medicamento_cardio_id FROM medicamentos WHERE nombre = 'CardioVital 10mg';
    SELECT id INTO v_admin_id FROM usuarios WHERE rol = 'admin' LIMIT 1; /* NUEVO: Obtener un admin ID */

    IF v_usuario_activo_id IS NOT NULL AND v_medicamento_analgex_id IS NOT NULL AND v_admin_id IS NOT NULL THEN
        INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, hora_preferida, estado, asignado_por_usuario_id) VALUES /* MODIFICADO */
        (v_usuario_activo_id, v_medicamento_analgex_id, '1 comprimido', 'Cada 8 horas', CURRENT_DATE + INTERVAL '1 day', '08:00:00', 'activa', v_admin_id) /* MODIFICADO */
        ON CONFLICT DO NOTHING;
    END IF;

    IF v_usuario_a_inactivar_id IS NOT NULL AND v_medicamento_cardio_id IS NOT NULL AND v_admin_id IS NOT NULL THEN
        INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, hora_preferida, estado, asignado_por_usuario_id) VALUES /* MODIFICADO */
        (v_usuario_a_inactivar_id, v_medicamento_cardio_id, '1 tableta', 'Cada 12 horas', CURRENT_DATE + INTERVAL '1 day', '09:00:00', 'activa', v_admin_id) /* MODIFICADO */
        ON CONFLICT DO NOTHING;
    END IF;
     IF v_usuario_a_inactivar_id IS NOT NULL AND v_medicamento_analgex_id IS NOT NULL AND v_admin_id IS NOT NULL THEN
        INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, hora_preferida, estado, asignado_por_usuario_id) VALUES /* MODIFICADO */
        (v_usuario_a_inactivar_id, v_medicamento_analgex_id, '2 tabletas', 'Cada 24 horas', CURRENT_DATE + INTERVAL '1 day', '21:00:00', 'activa', v_admin_id) /* MODIFICADO */
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

SELECT 'Esquema MediAlert con borrado lógico, auditoría y desactivación automática de alertas listo.' AS estado;
"""

# --- Lista de Medicamentos para insertar ---
lista_medicamentos = [
    {"nombre": "Paracetamol 500mg", "descripcion": "Analgésico y antipirético.", "composicion": "Paracetamol 500mg", "sintomas_secundarios": "náuseas, hepatotoxicidad en sobredosis", "indicaciones": "fiebre, dolor leve a moderado", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Ibuprofeno 400mg", "descripcion": "Antiinflamatorio no esteroideo.", "composicion": "Ibuprofeno 400mg", "sintomas_secundarios": "gastritis, dolor abdominal", "indicaciones": "dolor, inflamación, fiebre", "rango_edad": "Mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Aspirina 100mg", "descripcion": "Antiplaquetario y antiinflamatorio.", "composicion": "Ácido acetilsalicílico 100mg", "sintomas_secundarios": "sangrado gastrointestinal", "indicaciones": "prevención trombosis, dolor leve", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Amoxicilina 500mg", "descripcion": "Antibiótico β-lactámico.", "composicion": "Amoxicilina trihidrato 500mg", "sintomas_secundarios": "diarrea, candidiasis", "indicaciones": "infecciones respiratorias, urinarias", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Azitromicina 500mg", "descripcion": "Antibiótico macrólido.", "composicion": "Azitromicina dihidrato 500mg", "sintomas_secundarios": "dolor abdominal, diarrea", "indicaciones": "infecciones respiratorias, otitis", "rango_edad": "Adultos y niños mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Ciprofloxacino 500mg", "descripcion": "Antibiótico fluoroquinolónico.", "composicion": "Ciprofloxacino clorhidrato 500mg", "sintomas_secundarios": "tendinitis, fotosensibilidad", "indicaciones": "ITU, gastroenteritis", "rango_edad": "Adultos y niños mayores de 18 años", "estado_medicamento": "disponible"},
    {"nombre": "Metformina 850mg", "descripcion": "Antidiabético oral, biguanida.", "composicion": "Metformina clorhidrato 850mg", "sintomas_secundarios": "diarrea, acidosis láctica (raro)", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Atorvastatina 20mg", "descripcion": "Reductor de lípidos, estatina.", "composicion": "Atorvastatina cálcica 20mg", "sintomas_secundarios": "mialgias, elevación de transaminasas", "indicaciones": "hipercolesterolemia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Omeprazol 20mg", "descripcion": "Inhibidor de bomba de protones.", "composicion": "Omeprazol 20mg", "sintomas_secundarios": "dolor de cabeza, diarrea", "indicaciones": "reflujo gastroesofágico, úlcera péptica", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Ranitidina 150mg", "descripcion": "Antagonista H2, reduce producción de ácido.", "composicion": "Ranitidina 150mg", "sintomas_secundarios": "constipación, somnolencia", "indicaciones": "úlcera gástrica, reflujo", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Loratadina 10mg", "descripcion": "Antihistamínico H1 de segunda generación.", "composicion": "Loratadina 10mg", "sintomas_secundarios": "cefalea, somnolencia (raro)", "indicaciones": "alergias, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Cetirizina 10mg", "descripcion": "Antihistamínico H1 de segunda generación.", "composicion": "Cetirizina 10mg", "sintomas_secundarios": "somnolencia, boca seca", "indicaciones": "urticaria, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Salbutamol 100mcg", "descripcion": "Broncodilatador β2 agonista de acción corta.", "composicion": "Salbutamol sulfato 100mcg por dosis", "sintomas_secundarios": "temblor, taquicardia", "indicaciones": "asma, EPOC", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Prednisona 5mg", "descripcion": "Corticosteroide oral de acción intermedia.", "composicion": "Prednisona 5mg", "sintomas_secundarios": "aumento de peso, hipertensión", "indicaciones": "inflamación, alergias severas", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Metoclopramida 10mg", "descripcion": "Procinético y antiemético.", "composicion": "Metoclopramida 10mg", "sintomas_secundarios": "somnolencia, espasmos musculares", "indicaciones": "náuseas, gastroparesia", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Omeprazol 40mg", "descripcion": "IBP para tratamiento de úlceras más severas.", "composicion": "Omeprazol 40mg", "sintomas_secundarios": "insomnio, mareo", "indicaciones": "síndrome de Zollinger-Ellison", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Naproxeno 500mg", "descripcion": "AINE de larga acción.", "composicion": "Naproxeno 500mg", "sintomas_secundarios": "ulceración GI, retención de líquidos", "indicaciones": "artritis, dolor crónico", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Clonazepam 0.5mg", "descripcion": "Benzodiacepina de acción prolongada.", "composicion": "Clonazepam 0.5mg", "sintomas_secundarios": "somnolencia, dependencia", "indicaciones": "ansiedad, epilepsia", "rango_edad": "Adultos y niños mayores de 18 años", "estado_medicamento": "disponible"},
    {"nombre": "Diazepam 10mg", "descripcion": "Benzodiacepina de acción larga.", "composicion": "Diazepam 10mg", "sintomas_secundarios": "sedación, ataxia", "indicaciones": "ansiedad, espasmos musculares", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Tramadol 50mg", "descripcion": "Analgesico opioide de moderada potencia.", "composicion": "Tramadol clorhidrato 50mg", "sintomas_secundarios": "mareo, náuseas", "indicaciones": "dolor moderado a severo", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Codeína 30mg", "descripcion": "Opioide leve, antitúsivo ocasional.", "composicion": "Codeína fosfato 30mg", "sintomas_secundarios": "estreñimiento, somnolencia", "indicaciones": "dolor leve, tos seca", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Metamizol 575mg", "descripcion": "Analgésico y antipirético no opioide.", "composicion": "Metamizol sódico 575mg", "sintomas_secundarios": "agranulocitosis (raro), hipotensión", "indicaciones": "dolor agudo, fiebre alta", "rango_edad": "Adultos y niños mayores de 3 meses", "estado_medicamento": "disponible"},
    {"nombre": "Ondansetrón 4mg", "descripcion": "Antiemético 5-HT3 receptor antagonista.", "composicion": "Ondansetrón 4mg", "sintomas_secundarios": "estreñimiento, cefalea", "indicaciones": "náuseas por quimioterapia", "rango_edad": "Adultos y niños mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Fluconazol 150mg", "descripcion": "Antifúngico azólico de amplio espectro.", "composicion": "Fluconazol 150mg", "sintomas_secundarios": "náuseas, hepatotoxicidad", "indicaciones": "candidiasis vaginal", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Ketoconazol 200mg", "descripcion": "Antifúngico azólico sistémico.", "composicion": "Ketoconazol 200mg", "sintomas_secundarios": "alteraciones hepáticas", "indicaciones": "dermatofitosis, candidiasis", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Metronidazol 500mg", "descripcion": "Antibacteriano y antiprotozoario nitroimidazol.", "composicion": "Metronidazol 500mg", "sintomas_secundarios": "sabor metálico, neuropatía periferica", "indicaciones": "infecciones anaerobias, giardiasis", "rango_edad": "Adultos y niños mayores de 3 años", "estado_medicamento": "disponible"},
    {"nombre": "Clindamicina 300mg", "descripcion": "Antibiótico lincosamida.", "composicion": "Clindamicina fosfato 300mg", "sintomas_secundarios": "colitis pseudomembranosa", "indicaciones": "infecciones de piel, hueso", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Enalapril 10mg", "descripcion": "IECA para hipertensión.", "composicion": "Enalapril maleato 10mg", "sintomas_secundarios": "tos seca, hipotensión", "indicaciones": "hipertensión, IC", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Losartán 50mg", "descripcion": "ARA-II para hipertensión.", "composicion": "Losartán potásico 50mg", "sintomas_secundarios": "mareo, hiperkalemia", "indicaciones": "hipertensión, nefropatía diabética", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Amlodipino 5mg", "descripcion": "Bloqueador de canales de calcio dihidropiridínico.", "composicion": "Amlodipino besilato 5mg", "sintomas_secundarios": "edema periférico, cefalea", "indicaciones": "hipertensión, angina", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Metoprolol 50mg", "descripcion": "Betabloqueador cardioselectivo.", "composicion": "Metoprolol tartrato 50mg", "sintomas_secundarios": "bradicardia, fatiga", "indicaciones": "hipertensión, angina", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Propanolol 40mg", "descripcion": "Betabloqueador no selectivo.", "composicion": "Propanolol 40mg", "sintomas_secundarios": "broncoespasmo, fatiga", "indicaciones": "hipertensión, temblor esencial", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Hidroclorotiazida 25mg", "descripcion": "Diurético tiazídico.", "composicion": "Hidroclorotiazida 25mg", "sintomas_secundarios": "hipopotasemia, hiponatremia", "indicaciones": "hipertensión", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Furosemida 40mg", "descripcion": "Diurético de asa.", "composicion": "Furosemida 40mg", "sintomas_secundarios": "deshidratación, ototoxicidad (raro)", "indicaciones": "edema, IC", "rango_edad": "Adultos y niños mayores de 18 años", "estado_medicamento": "disponible"},
    {"nombre": "Espironolactona 25mg", "descripcion": "Diurético ahorrador de potasio.", "composicion": "Espironolactona 25mg", "sintomas_secundarios": "hiperkalemia, ginecomastia", "indicaciones": "cirrosis, IC", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Warfarina 5mg", "descripcion": "Anticoagulante cumarínico.", "composicion": "Warfarina sódica 5mg", "sintomas_secundarios": "hemorragias, necrosis cutánea", "indicaciones": "trombosis, fibrilación auricular", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Heparina sódica 5000UI", "descripcion": "Anticoagulante de acción inmediata.", "composicion": "Heparina sódica 5000UI/ml", "sintomas_secundarios": "trombocitopenia, hemorragia", "indicaciones": "profilaxis trombótica", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Enoxaparina 40mg", "descripcion": "HBPM para anticoagulación subcutánea.", "composicion": "Enoxaparina sódica 40mg", "sintomas_secundarios": "trombocitopenia, hemorragia", "indicaciones": "trombosis venosa profunda", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Clopidogrel 75mg", "descripcion": "Inhibidor de P2Y12, antiplaquetario.", "composicion": "Clopidogrel 75mg", "sintomas_secundarios": "sangrado, dispepsia", "indicaciones": "síndrome coronario agudo", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Simvastatina 20mg", "descripcion": "Estatina para reducción de colesterol LDL.", "composicion": "Simvastatina 20mg", "sintomas_secundarios": "mialgias, elevación de enzimas hepáticas", "indicaciones": "dislipidemia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fenofibrato 145mg", "descripcion": "Fibrato para reducción de triglicéridos.", "composicion": "Fenofibrato 145mg", "sintomas_secundarios": "dispepsia, mialgias", "indicaciones": "hipertrigliceridemia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Pantoprazol 40mg", "descripcion": "IBP para mantenimiento de reflujo.", "composicion": "Pantoprazol sódico 40mg", "sintomas_secundarios": "cefalea, diarrea", "indicaciones": "ERGE, úlcera péptica", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Esomeprazol 40mg", "descripcion": "S-isoforma de omeprazol, IBP.", "composicion": "Esomeprazol magnesio 40mg", "sintomas_secundarios": "mareo, flatulencia", "indicaciones": "ERGE", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fexofenadina 180mg", "descripcion": "Antihistamínico H1 no sedante.", "composicion": "Fexofenadina 180mg", "sintomas_secundarios": "cefalea, náuseas", "indicaciones": "alergias estacionales", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Montelukast 10mg", "descripcion": "Antileucotrieno para asma y rinoconjuntivitis.", "composicion": "Montelukast sodio 10mg", "sintomas_secundarios": "cefalea, dolor abdominal", "indicaciones": "asma, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Budesonida 200mcg", "descripcion": "Corticosteroide inhalado.", "composicion": "Budesonida 200mcg/dosis", "sintomas_secundarios": "irritación orofaríngea", "indicaciones": "asma, EPOC", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Beclometasona 100mcg", "descripcion": "Corticosteroide nasal para alergias.", "composicion": "Beclometasona dipropionato 100mcg", "sintomas_secundarios": "irritación nasal", "indicaciones": "rinitis alérgica", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Insulina glargina 100UI/ml", "descripcion": "Insulina basal de acción prolongada.", "composicion": "Insulina glargina 100UI/ml", "sintomas_secundarios": "hipoglucemia, lipodistrofia", "indicaciones": "diabetes tipo 1 y tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Glimepirida 2mg", "descripcion": "Sulfonilurea para diabetes tipo 2.", "composicion": "Glimepirida 2mg", "sintomas_secundarios": "hipoglucemia, aumento de peso", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Gliclazida 80mg", "descripcion": "Sulfonilurea de segunda generación.", "composicion": "Gliclazida 80mg", "sintomas_secundarios": "hipoglucemia, náuseas", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Sitagliptina 100mg", "descripcion": "Inhibidor de DPP-4 para diabetes.", "composicion": "Sitagliptina fosfato sódico 100mg", "sintomas_secundarios": "cefalea, nasofaringitis", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Empagliflozina 10mg", "descripcion": "Inhibidor de SGLT2 para diabetes.", "composicion": "Empagliflozina 10mg", "sintomas_secundarios": "infecciones urinarias, poliuria", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Sertralina 50mg", "descripcion": "ISRS para depresión y ansiedad.", "composicion": "Sertralina 50mg", "sintomas_secundarios": "náuseas, insomnio", "indicaciones": "depresión, TOC", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fluoxetina 20mg", "descripcion": "ISRS de larga vida media.", "composicion": "Fluoxetina 20mg", "sintomas_secundarios": "insomnio, disfunción sexual", "indicaciones": "depresión, bulimia nerviosa", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Citalopram 20mg", "descripcion": "ISRS para trastornos depresivos.", "composicion": "Citalopram hidrobromuro 20mg", "sintomas_secundarios": "mareo, fatiga", "indicaciones": "depresión", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Alprazolam 0.5mg", "descripcion": "Benzodiacepina de acción corta.", "composicion": "Alprazolam 0.5mg", "sintomas_secundarios": "dependencia, sedación", "indicaciones": "ansiedad, pánico", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Haloperidol 5mg", "descripcion": "Antipsicótico típico de alta potencia.", "composicion": "Haloperidol 5mg", "sintomas_secundarios": "rigidez muscular, acatisia", "indicaciones": "esquizofrenia, psicosis aguda", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Quetiapina 50mg", "descripcion": "Antipsicótico atípico.", "composicion": "Quetiapina fumarato 50mg", "sintomas_secundarios": "sedación, aumento de peso", "indicaciones": "esquizofrenia, bipolaridad", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Topiramato 100mg", "descripcion": "Antiepiléptico y profilaxis de migraña.", "composicion": "Topiramato 100mg", "sintomas_secundarios": "mareo, pérdida de peso", "indicaciones": "epilepsia, migraña", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Sumatriptán 50mg", "descripcion": "Agonista 5-HT1 para migraña.", "composicion": "Sumatriptán succinato 50mg", "sintomas_secundarios": "parestesias, sensación de opresión torácica", "indicaciones": "migraña aguda", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Aciclovir 400mg", "descripcion": "Antiviral inhibidor de ADN polimerasa.", "composicion": "Aciclovir 400mg", "sintomas_secundarios": "cefalea, náuseas", "indicaciones": "herpes labial, varicela", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Valaciclovir 500mg", "descripcion": "Profármaco de aciclovir con mejor biodisponibilidad.", "composicion": "Valaciclovir 500mg", "sintomas_secundarios": "dolor de cabeza, náuseas", "indicaciones": "herpes zóster", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Oseltamivir 75mg", "descripcion": "Inhibidor de neuraminidasa para influenza.", "composicion": "Oseltamivir fosfato 75mg", "sintomas_secundarios": "náuseas, vómitos", "indicaciones": "gripe A/B", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Loperamida 2mg", "descripcion": "Antidiarreico opioide sin pasar BHE.", "composicion": "Loperamida 2mg", "sintomas_secundarios": "estreñimiento, mareo", "indicaciones": "diarrea aguda", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Lactulosa 10g/15ml", "descripcion": "Laxante osmótico.", "composicion": "Lactulosa 10g por 15ml", "sintomas_secundarios": "flatulencia, dolor abdominal", "indicaciones": "estreñimiento", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Doxiciclina 100mg", "descripcion": "Antibiótico tetraciclina de amplio espectro.", "composicion": "Doxiciclina 100mg", "sintomas_secundarios": "fotosensibilidad, dispepsia", "indicaciones": "acné, infecciones respiratorias", "rango_edad": "Adultos y niños mayores de 8 años", "estado_medicamento": "disponible"},
    {"nombre": "Eritromicina 500mg", "descripcion": "Antibiótico macrólido de primera generación.", "composicion": "Eritromicina estolato 500mg", "sintomas_secundarios": "colestasis, náuseas", "indicaciones": "infecciones respiratorias", "rango_edad": "Adultos y niños mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Claritromicina 500mg", "descripcion": "Macrólido de segunda generación.", "composicion": "Claritromicina 500mg", "sintomas_secundarios": "sabor metálico, diarrea", "indicaciones": "infecciones de piel", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Terapia esteroidal oral varia según paciente", "descripcion": "Protocolos variados según patología.", "composicion": "Dosis ajustada de corticoides", "sintomas_secundarios": "variable", "indicaciones": "condiciones inflamatorias graves", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fenacetina Pura", "descripcion": "Analgésico antiguo, retirado del mercado.", "composicion": "Fenacetina", "sintomas_secundarios": "Nefropatía, carcinogenicidad", "indicaciones": "Ya no se usa", "rango_edad": "N/A", "estado_medicamento": "discontinuado"},
]

# Lista de EPS comunes en Colombia, para la inserción inicial
lista_eps_a_insertar = [
    {"nombre": "Nueva EPS", "nit": "8301086054"},
    {"nombre": "Sura EPS", "nit": "8909031357"},
    {"nombre": "Sanitas EPS", "nit": "8605136814"},
    {"nombre": "Compensar EPS", "nit": "8600667017"},
    {"nombre": "Coosalud EPS", "nit": "8002047247"},
    {"nombre": "Salud Total EPS", "nit": "8001021464"},
    {"nombre": "Famisanar EPS", "nit": "8605330366"},
]

def inicializar_db():
    conn = None
    cur = None
    try:
        print(f"Conectando a la base de datos PostgreSQL (Host: {PG_HOST}, DB: {PG_DB})...")
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT
        )
        conn.set_client_encoding('UTF8')
        cur = conn.cursor()

        print("Ejecutando comandos SQL para crear/recrear el esquema de la base de datos...")
        cur.execute(SQL_COMMANDS)
        print("Esquema de base de datos procesado con éxito.")

        print(f"Insertando {len(lista_medicamentos)} medicamentos en la tabla 'medicamentos'...")
        for med in lista_medicamentos:
            try:
                # Limpiar espacios no separadores de los datos del diccionario antes de la inserción
                cleaned_med = {k: v.replace('\u00A0', ' ') if isinstance(v, str) else v for k, v in med.items()}
                
                cur.execute("""
                    INSERT INTO medicamentos (
                        nombre, descripcion, composicion, sintomas_secundarios,
                        indicaciones, rango_edad, estado_medicamento
                    )
                    VALUES (
                        %(nombre)s, %(descripcion)s, %(composicion)s, %(sintomas_secundarios)s,
                        %(indicaciones)s, %(rango_edad)s, %(estado_medicamento)s
                    )
                    ON CONFLICT (nombre) DO UPDATE SET
                        descripcion = EXCLUDED.descripcion,
                        composicion = EXCLUDED.composicion,
                        sintomas_secundarios = EXCLUDED.sintomas_secundarios,
                        indicaciones = EXCLUDED.indicaciones,
                        rango_edad = EXCLUDED.rango_edad,
                        estado_medicamento = EXCLUDED.estado_medicamento;
                """, cleaned_med) # Usar el diccionario limpio
            except psycopg2.Error as e:
                print(f"Error al insertar/actualizar medicamento '{med.get('nombre', 'Desconocido')}': {e}")
                conn.rollback()
        print("Medicamentos insertados/actualizados con éxito.")

        conn.commit()
        print("\n¡Base de datos inicializada y datos cargados correctamente!")
        print("Se crearon secuencias, tablas, funciones, disparadores y se insertaron datos iniciales.")
        print("Los usuarios y medicamentos de prueba insertados por el SQL también activaron sus respectivos triggers de auditoría.")

    except psycopg2.OperationalError as e:
        print(f"\nError operacional de PostgreSQL: {e}")
        print("Verifica que el servidor PostgreSQL esté corriendo y accesible,")
        print(f"y que la base de datos '{PG_DB}' exista o que el usuario '{PG_USER}' tenga permisos para crearla si es necesario.")
    except psycopg2.Error as e:
        print(f"\nOcurrió un error de PostgreSQL al inicializar la base de datos: {e}")
        if conn:
            conn.rollback() 
    except Exception as e:
        print(f"\nOcurrió un error general inesperado: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    print("Iniciando el script de inicialización de la base de datos MediAlert...")
    inicializar_db()
    print("Proceso de inicialización de la base de datos finalizado.")