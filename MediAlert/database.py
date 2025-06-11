# medialert/database.py

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from flask import current_app, session
from datetime import date, time, datetime # Importar datetime para fecha_registro

# Helper para serializar tipos de datos Python para JSONB
def _serialize_data_for_jsonb(obj):
    """
    Convierte recursivamente objetos date, time, y datetime a strings ISO en un diccionario o lista
    para ser usados con JSONB en PostgreSQL.
    """
    if isinstance(obj, dict):
        return {k: _serialize_data_for_jsonb(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_data_for_jsonb(i) for i in obj]
    elif isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    return obj

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=current_app.config['PG_HOST'],
            database=current_app.config['PG_DB'],
            user=current_app.config['PG_USER'],
            password=current_app.config['PG_PASS'],
            port=current_app.config['PG_PORT']
        )
        # Intentar establecer el app_user_id para la auditoría a nivel de BD
        # Solo si la sesión ya existe para evitar errores en llamadas sin sesión
        if 'user_id' in session:
            with conn.cursor() as cur:
                # Usar set_config con is_local = true para que dure solo la transacción/sesión actual
                cur.execute("SELECT set_config('medialert.app_user_id', %s, true);", (str(session['user_id']),))
        return conn
    except psycopg2.Error as e:
        current_app.logger.error(f"Error al conectar con la base de datos: {e}")
        raise # Relanzar la excepción para que sea manejada más arriba si es necesario

def registrar_auditoria_aplicacion(accion, tabla_afectada=None, registro_id=None,
                                   datos_anteriores=None, datos_nuevos=None, detalles_adicionales=None):
    """
    Registra una acción en la tabla de auditoría llamando a la función de PostgreSQL
    sp_registrar_evento_auditoria.
    Los datos (anteriores, nuevos, adicionales) deben ser diccionarios de Python.
    """
    app_user_id = session.get('user_id')

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        p_datos_anteriores = Json(_serialize_data_for_jsonb(datos_anteriores)) if datos_anteriores is not None else None
        p_datos_nuevos = Json(_serialize_data_for_jsonb(datos_nuevos)) if datos_nuevos is not None else None
        p_detalles_adicionales = Json(_serialize_data_for_jsonb(detalles_adicionales)) if detalles_adicionales is not None else None

        cur.execute(
            "SELECT sp_registrar_evento_auditoria(%s, %s, %s, %s, %s, %s, %s);",
            (app_user_id, accion, tabla_afectada, registro_id,
             p_datos_anteriores, p_datos_nuevos, p_detalles_adicionales)
        )
        conn.commit()
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al registrar auditoría de aplicación ({accion}): {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        current_app.logger.error(f"Error general al registrar auditoría de aplicación ({accion}): {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()