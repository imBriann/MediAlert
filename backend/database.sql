-- Borra las tablas y secuencias existentes para empezar de cero
DROP TABLE IF EXISTS reportes, alertas, medicamentos, usuarios, auditoria CASCADE;
DROP SEQUENCE IF EXISTS usuarios_id_seq, medicamentos_id_seq, alertas_id_seq, auditoria_id_seq;

--------------------------------------------------------------------------------
-- SECCIÓN: SECUENCIAS
--------------------------------------------------------------------------------
CREATE SEQUENCE usuarios_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE medicamentos_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE alertas_id_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE auditoria_id_seq START WITH 1 INCREMENT BY 1;

--------------------------------------------------------------------------------
-- SECCIÓN: TABLAS
--------------------------------------------------------------------------------

-- Tabla: usuarios
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY DEFAULT nextval('usuarios_id_seq'),
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'cliente')),
    estado_usuario VARCHAR(10) DEFAULT 'activo' NOT NULL CHECK (estado_usuario IN ('activo', 'inactivo'))
);
COMMENT ON TABLE usuarios IS 'Almacena la información de los usuarios del sistema.';
COMMENT ON COLUMN usuarios.estado_usuario IS 'Estado del usuario. Para clientes, "inactivo" significa borrado lógico.';


-- Tabla: medicamentos
CREATE TABLE medicamentos (
    id INTEGER PRIMARY KEY DEFAULT nextval('medicamentos_id_seq'),
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    composicion TEXT,
    sintomas_secundarios TEXT,
    indicaciones TEXT,
    rango_edad VARCHAR(50),
    -- Nueva columna para el estado del medicamento (borrado lógico)
    estado_medicamento VARCHAR(15) DEFAULT 'disponible' NOT NULL CHECK (estado_medicamento IN ('disponible', 'discontinuado', 'agotado'))
);
COMMENT ON TABLE medicamentos IS 'Catálogo de medicamentos. Incluye estado para borrado lógico.';
COMMENT ON COLUMN medicamentos.estado_medicamento IS 'Estado actual del medicamento (disponible, discontinuado, agotado). "discontinuado" puede usarse para borrado lógico.';


-- Tabla: alertas
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY DEFAULT nextval('alertas_id_seq'),
    usuario_id INT NOT NULL, -- Se eliminará la FK directa a usuarios para permitir que las alertas persistan si el usuario se "inactiva"
    medicamento_id INT NOT NULL, -- Se eliminará la FK directa a medicamentos por la misma razón
    dosis VARCHAR(100),
    frecuencia VARCHAR(100),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    estado VARCHAR(20) DEFAULT 'activa' CHECK (estado IN ('activa', 'inactiva', 'completada')),
    CONSTRAINT fk_alertas_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE NO ACTION, -- Previene borrado si hay alertas activas. O se maneja en la app.
    CONSTRAINT fk_alertas_medicamento FOREIGN KEY (medicamento_id) REFERENCES medicamentos(id) ON DELETE NO ACTION
);
COMMENT ON TABLE alertas IS 'Alertas de medicamentos. Las FK ahora son NO ACTION para el borrado lógico de usuarios/medicamentos.';
COMMENT ON COLUMN alertas.usuario_id IS 'Referencia al usuario. Las alertas pueden persistir para usuarios inactivos (historial).';
COMMENT ON COLUMN alertas.medicamento_id IS 'Referencia al medicamento. Las alertas pueden persistir para medicamentos discontinuados (historial).';


-- Tabla: auditoria
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

--------------------------------------------------------------------------------
-- SECCIÓN: FUNCIONES DE POSTGRESQL
--------------------------------------------------------------------------------

-- Función: sp_registrar_evento_auditoria
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


-- Función: func_disparador_auditoria_generico
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
        -- Esta sección del trigger genérico se volverá menos relevante si prevenimos los DELETEs físicos.
        -- Sin embargo, es bueno mantenerla por si los administradores (u otros roles) sí pueden borrar físicamente.
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

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;


-- Función: func_prevenir_borrado_cliente
-- Descripción: Previene el borrado físico de usuarios con rol 'cliente'.
--              En su lugar, podría convertirlo a una actualización de estado, pero
--              es más limpio manejar la actualización de estado desde la lógica de aplicación.
--              Aquí simplemente cancelaremos el DELETE.
CREATE OR REPLACE FUNCTION func_prevenir_borrado_fisico_cliente()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.rol = 'cliente' THEN
        -- En lugar de RAISE EXCEPTION, que detendría la transacción y podría no ser deseado
        -- si la app espera un "éxito" para luego confirmar el borrado lógico,
        -- es mejor que la app NO INTENTE un DELETE para clientes.
        -- Si la app intenta un DELETE, podemos loggearlo y no hacer nada o lanzar excepción.
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
    RETURN OLD; -- Permite el DELETE para otros roles (ej. admin si se implementara)
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


--------------------------------------------------------------------------------
-- SECCIÓN: DISPARADORES (TRIGGERS)
--------------------------------------------------------------------------------

-- Disparadores de Auditoría Genéricos (para INSERT, UPDATE)
CREATE TRIGGER trg_usuarios_auditoria
AFTER INSERT OR UPDATE ON usuarios -- Excluimos DELETE aquí si vamos a prevenirlo
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

CREATE TRIGGER trg_medicamentos_auditoria
AFTER INSERT OR UPDATE ON medicamentos -- Excluimos DELETE aquí
FOR EACH ROW EXECUTE FUNCTION func_disparador_auditoria_generico();

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


-- Si aún se quiere auditar los intentos de DELETE fallidos (ya cubierto por las funciones de prevención)
-- o los DELETEs exitosos para otros roles/tablas, el trigger de auditoría genérico puede incluir DELETE:
-- Re-añadir DELETE al trigger de auditoría de usuarios si los 'admin' SÍ pueden borrarse físicamente.
-- Por ahora, la prevención lo maneja.

--------------------------------------------------------------------------------
-- SECCIÓN: DATOS INICIALES
--------------------------------------------------------------------------------
INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario) VALUES
('Administrador Principal', 'admin001', 'admin@medialert.co', 'bcrypt_hash_admin', 'admin', 'activo'),
('Cliente Activo Ejemplo', 'user001', 'cliente@example.com', 'bcrypt_hash_cliente', 'cliente', 'activo'),
('Cliente Inactivo Ejemplo', 'user002', 'cliente.inactivo@example.com', 'bcrypt_hash_cliente2', 'cliente', 'inactivo')
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO medicamentos (nombre, descripcion, estado_medicamento) VALUES
('Analgex 500mg', 'Alivio del dolor y fiebre.', 'disponible'),
('CardioVital 10mg', 'Tratamiento hipertensión.', 'disponible'),
('Antibiotix Max (Obsoleto)', 'Antibiótico de amplio espectro.', 'discontinuado')
ON CONFLICT (nombre) DO NOTHING;

-- Insertar alerta para el cliente activo con medicamento disponible
INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, estado)
SELECT u.id, m.id, '1 pastilla', 'Cada 8 horas', '2025-06-01', 'activa'
FROM usuarios u, medicamentos m
WHERE u.cedula = 'user001' AND m.nombre = 'Analgex 500mg'
ON CONFLICT DO NOTHING;


SELECT 'Esquema MediAlert con borrado lógico y auditoría listo.' AS estado;