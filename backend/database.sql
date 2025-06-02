-- Borra las tablas y secuencias existentes para empezar de cero
DROP TABLE IF EXISTS reportes, alertas, medicamentos, usuarios, auditoria CASCADE;
DROP SEQUENCE IF EXISTS usuarios_id_seq, medicamentos_id_seq, alertas_id_seq, auditoria_id_seq;

--------------------------------------------------------------------------------
-- SECCIÓN: SECUENCIAS
-- Descripción: Secuencias para la generación de IDs autonuméricos.
--------------------------------------------------------------------------------
CREATE SEQUENCE usuarios_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE medicamentos_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE alertas_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE auditoria_id_seq START WITH 1 INCREMENT BY 1;

--------------------------------------------------------------------------------
-- SECCIÓN: TABLAS
--------------------------------------------------------------------------------

-- Tabla: usuarios
-- Descripción: Almacena la información de los usuarios del sistema.
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY DEFAULT nextval('usuarios_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'cliente')),
    estado_usuario VARCHAR(10) DEFAULT 'activo' NOT NULL CHECK (estado_usuario IN ('activo', 'inactivo'))
);
COMMENT ON TABLE usuarios IS 'Almacena la información de los usuarios del sistema, incluyendo administradores y clientes.';
COMMENT ON COLUMN usuarios.id IS 'Identificador único del usuario (autonumérico).';
COMMENT ON COLUMN usuarios.rol IS 'Define el rol del usuario dentro del sistema (admin o cliente).';
COMMENT ON COLUMN usuarios.cedula IS 'Número de cédula del usuario, debe ser único.';
COMMENT ON COLUMN usuarios.estado_usuario IS 'Estado del usuario. Para clientes, "inactivo" significa borrado lógico y cesarán sus notificaciones de alerta.';


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
    -- Considerar otros estados si es necesario, ej: 'agotado temporalmente'
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
    CONSTRAINT fk_alertas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE NO ACTION,
    CONSTRAINT fk_alertas_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE NO ACTION
);
COMMENT ON TABLE alertas IS 'Registra las alertas de medicamentos programadas para cada usuario cliente.';
COMMENT ON COLUMN alertas.id IS 'Identificador único de la alerta (autonumérico).';
COMMENT ON COLUMN alertas.usuario_id IS 'Referencia al usuario que recibe la alerta.';
COMMENT ON COLUMN alertas.medicamento_id IS 'Referencia al medicamento de la alerta.';
COMMENT ON COLUMN alertas.estado IS 'Estado actual de la alerta (activa, inactiva por usuario/medicamento, completada, fallida).';
COMMENT ON COLUMN alertas.hora_preferida IS 'Hora específica del día en que el usuario prefiere recibir la notificación para esta alerta.';
COMMENT ON COLUMN alertas.ultima_notificacion_enviada IS 'Timestamp de la última vez que se intentó enviar una notificación para esta alerta.';


-- Tabla: auditoria
-- Descripción: Registra todas las acciones y cambios importantes en el sistema.
CREATE TABLE auditoria (
    id INTEGER PRIMARY KEY DEFAULT nextval('auditoria_id_seq'),
    usuario_id_app INTEGER,
    usuario_db NAME DEFAULT current_user,
    accion VARCHAR(255) NOT NULL,
    tabla_afectada VARCHAR(63),
    registro_id_afectado TEXT,
    datos_anteriores JSONB,
    datos_nuevos JSONB,
    detalles_adicionales JSONB,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE auditoria IS 'Tabla centralizada para registrar eventos de auditoría del sistema.';

--------------------------------------------------------------------------------
-- SECCIÓN: FUNCIONES DE POSTGRESQL
--------------------------------------------------------------------------------

-- Función: sp_registrar_evento_auditoria
-- Descripción: Función genérica para insertar registros en la tabla de auditoría.
CREATE OR REPLACE FUNCTION sp_registrar_evento_auditoria(
    p_usuario_id_app INTEGER,
    p_accion VARCHAR(255),
    p_tabla_afectada VARCHAR(63) DEFAULT NULL,
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
        p_accion               := TG_OP,
        p_tabla_afectada       := TG_TABLE_NAME,
        p_registro_id_afectado := v_registro_id_afectado,
        p_datos_anteriores     := v_datos_anteriores,
        p_datos_nuevos         := v_datos_nuevos
    );

    RETURN NULL; -- El resultado es ignorado para triggers AFTER
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
            p_usuario_id_app := current_setting('medialert.app_user_id', true)::INTEGER,
            p_accion := 'INTENTO_BORRADO_FISICO_CLIENTE_PREVENIDO',
            p_tabla_afectada := TG_TABLE_NAME,
            p_registro_id_afectado := OLD.id::TEXT,
            p_datos_anteriores := to_jsonb(OLD)
        );
        RAISE NOTICE 'El borrado físico de clientes (ID: %) está prevenido. Actualice su estado a "inactivo" en su lugar.', OLD.id;
        RETURN NULL; -- Cancela la operación DELETE
    END IF;
    RETURN OLD; -- Permite el DELETE para otros roles (ej. admin si se implementara y no tuviera este trigger)
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION func_prevenir_borrado_fisico_cliente IS 'Previene el DELETE físico de usuarios con rol "cliente".';


-- Función: func_prevenir_borrado_fisico_medicamento
-- Descripción: Previene el borrado físico de medicamentos.
CREATE OR REPLACE FUNCTION func_prevenir_borrado_fisico_medicamento()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM sp_registrar_evento_auditoria(
        p_usuario_id_app := current_setting('medialert.app_user_id', true)::INTEGER,
        p_accion := 'INTENTO_BORRADO_FISICO_MEDICAMENTO_PREVENIDO',
        p_tabla_afectada := TG_TABLE_NAME,
        p_registro_id_afectado := OLD.id::TEXT,
        p_datos_anteriores := to_jsonb(OLD)
    );
    RAISE NOTICE 'El borrado físico de medicamentos (ID: %) está prevenido. Actualice su estado a "discontinuado" en su lugar.', OLD.id;
    RETURN NULL; -- Cancela la operación DELETE
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

        -- Registrar este cambio masivo en la auditoría (opcional, ya que cada UPDATE en alertas será auditado individualmente)
        PERFORM sp_registrar_evento_auditoria(
            p_usuario_id_app := current_setting('medialert.app_user_id', true)::INTEGER,
            p_accion := 'DESACTIVACION_MASIVA_ALERTAS_POR_USUARIO_INACTIVO',
            p_tabla_afectada := 'alertas', -- Tabla afectada indirectamente
            p_registro_id_afectado := NEW.id::TEXT, -- ID del usuario que causó la desactivación
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
            p_usuario_id_app := current_setting('medialert.app_user_id', true)::INTEGER,
            p_accion := 'DESACTIVACION_MASIVA_ALERTAS_POR_MEDICAMENTO_DISCONTINUADO',
            p_tabla_afectada := 'alertas',
            p_registro_id_afectado := NEW.id::TEXT, -- ID del medicamento que causó la desactivación
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

-- Disparadores de Auditoría Genéricos (para INSERT, UPDATE en tablas principales)
CREATE TRIGGER trg_usuarios_auditoria
AFTER INSERT OR UPDATE ON usuarios
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

CREATE TRIGGER trg_medicamentos_auditoria
AFTER INSERT OR UPDATE ON medicamentos
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

-- El trigger de alertas auditará todos los cambios, incluyendo los hechos por otros triggers.
CREATE TRIGGER trg_alertas_auditoria
AFTER INSERT OR UPDATE OR DELETE ON alertas -- Las alertas sí se pueden borrar físicamente (o inactivar)
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();


-- Disparadores para Prevenir Borrado Físico (Soft Delete)
CREATE TRIGGER trg_usuarios_prevenir_delete_cliente
BEFORE DELETE ON usuarios
FOR EACH ROW EXECUTE FUNCTION func_prevenir_borrado_fisico_cliente();

CREATE TRIGGER trg_medicamentos_prevenir_delete
BEFORE DELETE ON medicamentos
FOR EACH ROW EXECUTE FUNCTION func_prevenir_borrado_fisico_medicamento();

-- Disparadores para Desactivación Automática de Alertas
CREATE TRIGGER trg_desactivar_alertas_usuario_inactivo
AFTER UPDATE OF estado_usuario ON usuarios -- Solo se dispara si cambia estado_usuario
FOR EACH ROW
EXECUTE FUNCTION func_desactivar_alertas_usuario_inactivo();

CREATE TRIGGER trg_desactivar_alertas_medicamento_discontinuado
AFTER UPDATE OF estado_medicamento ON medicamentos -- Solo se dispara si cambia estado_medicamento
FOR EACH ROW
EXECUTE FUNCTION func_desactivar_alertas_medicamento_discontinuado();

--------------------------------------------------------------------------------
-- SECCIÓN: DATOS INICIALES (PARA PRUEBAS)
--------------------------------------------------------------------------------
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

-- Insertar alertas para clientes activos con medicamentos disponibles
DO $$
DECLARE
    v_usuario_activo_id INTEGER;
    v_usuario_a_inactivar_id INTEGER;
    v_medicamento_analgex_id INTEGER;
    v_medicamento_cardio_id INTEGER;
BEGIN
    SELECT id INTO v_usuario_activo_id FROM usuarios WHERE cedula = 'user001';
    SELECT id INTO v_usuario_a_inactivar_id FROM usuarios WHERE cedula = 'user002';
    SELECT id INTO v_medicamento_analgex_id FROM medicamentos WHERE nombre = 'Analgex 500mg';
    SELECT id INTO v_medicamento_cardio_id FROM medicamentos WHERE nombre = 'CardioVital 10mg';

    IF v_usuario_activo_id IS NOT NULL AND v_medicamento_analgex_id IS NOT NULL THEN
        INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, hora_preferida, estado) VALUES
        (v_usuario_activo_id, v_medicamento_analgex_id, '1 comprimido', 'Cada 8 horas', CURRENT_DATE + INTERVAL '1 day', '08:00:00', 'activa')
        ON CONFLICT DO NOTHING;
    END IF;

    IF v_usuario_a_inactivar_id IS NOT NULL AND v_medicamento_cardio_id IS NOT NULL THEN
        INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, hora_preferida, estado) VALUES
        (v_usuario_a_inactivar_id, v_medicamento_cardio_id, '1 tableta', 'Cada 12 horas', CURRENT_DATE + INTERVAL '1 day', '09:00:00', 'activa')
        ON CONFLICT DO NOTHING;
    END IF;

    IF v_usuario_a_inactivar_id IS NOT NULL AND v_medicamento_analgex_id IS NOT NULL THEN
        INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, hora_preferida, estado) VALUES
        (v_usuario_a_inactivar_id, v_medicamento_analgex_id, '2 tabletas', 'Cada 24 horas', CURRENT_DATE + INTERVAL '1 day', '21:00:00', 'activa')
        ON CONFLICT DO NOTHING;
    END IF;
END $$;

--------------------------------------------------------------------------------
-- SECCIÓN DE PRUEBA PARA LOS NUEVOS TRIGGERS (EJECUTAR MANUALMENTE DESPUÉS DE CREAR EL ESQUEMA)
--------------------------------------------------------------------------------
/*
-- 1. Verificar alertas activas para el usuario 'user002'
SELECT u.nombre as usuario, m.nombre as medicamento, a.estado as estado_alerta, a.hora_preferida
FROM alertas a
JOIN usuarios u ON a.usuario_id = u.id
JOIN medicamentos m ON a.medicamento_id = m.id
WHERE u.cedula = 'user002';
-- Debería mostrar 2 alertas activas para 'Cliente Para Inactivar'

-- 2. Inactivar al usuario 'user002' (esto disparará trg_desactivar_alertas_usuario_inactivo)
-- Simular que la app lo hace:
-- SELECT set_config('medialert.app_user_id', (SELECT id::text FROM usuarios WHERE rol='admin' LIMIT 1), true);
UPDATE usuarios SET estado_usuario = 'inactivo' WHERE cedula = 'user002';

-- 3. Verificar de nuevo las alertas para 'user002'
SELECT u.nombre as usuario, m.nombre as medicamento, a.estado as estado_alerta
FROM alertas a
JOIN usuarios u ON a.usuario_id = u.id
JOIN medicamentos m ON a.medicamento_id = m.id
WHERE u.cedula = 'user002';
-- Ahora las alertas deberían estar 'inactiva'.

-- 4. Verificar la auditoría para la tabla 'alertas' y 'usuarios'
SELECT * FROM auditoria WHERE tabla_afectada = 'usuarios' AND registro_id_afectado = (SELECT id::text FROM usuarios WHERE cedula = 'user002') ORDER BY fecha_hora DESC;
SELECT * FROM auditoria WHERE tabla_afectada = 'alertas' AND detalles_adicionales->>'usuario_inactivado_id' = (SELECT id::text FROM usuarios WHERE cedula = 'user002') ORDER BY fecha_hora DESC;
SELECT * FROM auditoria WHERE tabla_afectada = 'alertas' AND datos_nuevos->>'estado' = 'inactiva' AND datos_anteriores->>'estado' = 'activa' ORDER BY fecha_hora DESC;


-- 5. Discontinuar un medicamento que tenga alertas activas
-- SELECT set_config('medialert.app_user_id', (SELECT id::text FROM usuarios WHERE rol='admin' LIMIT 1), true);
UPDATE medicamentos SET estado_medicamento = 'discontinuado' WHERE nombre = 'Analgex 500mg';

-- 6. Verificar alertas del medicamento 'Analgex 500mg'
SELECT u.nombre as usuario, m.nombre as medicamento, a.estado as estado_alerta
FROM alertas a
JOIN usuarios u ON a.usuario_id = u.id
JOIN medicamentos m ON a.medicamento_id = m.id
WHERE m.nombre = 'Analgex 500mg';
-- Todas las alertas activas para Analgex 500mg deberían estar ahora 'inactiva'.
*/

SELECT 'Esquema MediAlert con borrado lógico, auditoría y desactivación automática de alertas listo.' AS estado;