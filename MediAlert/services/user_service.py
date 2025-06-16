# medialert/services/user_service.py
import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from flask import current_app
# La importación ahora es más simple
from database import get_db_connection, registrar_auditoria_aplicacion

# (Las funciones get_users y get_user_by_id no cambian)
def get_users(estado_filtro=None, rol_filtro=None, search_query=None):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query_parts = ["SELECT u.id, u.nombre, u.cedula, u.email, u.rol, u.estado_usuario, u.fecha_nacimiento, u.telefono, u.ciudad, u.genero, u.tipo_regimen, u.fecha_registro, u.eps_id, e.nombre as eps_nombre FROM usuarios u LEFT JOIN eps e ON u.eps_id = e.id"]
        conditions, params = [], []
        if rol_filtro:
            conditions.append("u.rol = %s")
            params.append(rol_filtro)
        if estado_filtro and estado_filtro != 'todos':
            conditions.append("u.estado_usuario = %s")
            params.append(estado_filtro)
        if search_query:
            conditions.append("(u.nombre ILIKE %s OR u.cedula ILIKE %s)")
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))
        query_parts.append("ORDER BY u.rol, u.nombre")
        cur.execute(" ".join(query_parts), tuple(params))
        return cur.fetchall()
    finally:
        if conn: conn.close()

def get_user_by_id(uid):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (uid,))
        return cur.fetchone()
    finally:
        if conn: conn.close()

def create_user(user_data):
    """Crea un nuevo usuario. El ID del admin se obtiene en la función de auditoría."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # ... (código para obtener datos y hashear contraseña)
        nombre, cedula, email, contrasena_plain = user_data.get('nombre'), user_data.get('cedula'), user_data.get('email'), user_data.get('contrasena')
        if not all([nombre, cedula, email, contrasena_plain]):
            raise ValueError('Nombre, cédula, email y contraseña son requeridos.')
        hashed_password = generate_password_hash(contrasena_plain)
        
        sql = "INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario, fecha_nacimiento, telefono, ciudad, genero, tipo_regimen, fecha_registro, eps_id) VALUES (%s, %s, %s, %s, 'cliente', 'activo', %s, %s, %s, %s, %s, %s, %s) RETURNING id"
        params = (nombre, cedula, email, hashed_password, user_data.get('fecha_nacimiento') or None, user_data.get('telefono') or None, user_data.get('ciudad') or None, user_data.get('genero') or None, user_data.get('tipo_regimen') or None, datetime.now().date(), user_data.get('eps_id') or None)
        cur.execute(sql, params)
        new_id = cur.fetchone()['id']
        conn.commit()
        
        # ***** CORRECCIÓN *****
        # Ya no se pasa 'admin_id_actual'. La función de auditoría lo maneja.
        datos_nuevos_audit = {k: (v or None) for k, v in user_data.items() if k != 'contrasena'}
        registrar_auditoria_aplicacion('CREACION_CLIENTE', tabla_afectada='usuarios', registro_id=str(new_id), datos_nuevos=datos_nuevos_audit)
        
        return new_id
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "usuarios_cedula_key" in str(e): raise ValueError(f'La cédula "{cedula}" ya está registrada.')
        if "usuarios_email_key" in str(e): raise ValueError(f'El email "{email}" ya está registrado.')
        raise
    finally:
        if conn: conn.close()

def update_user(uid, user_data, old_user_data):
    """Actualiza un usuario. El ID del admin se obtiene en la función de auditoría."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # ... (código para construir la consulta de actualización)
        allowed_fields = ['nombre', 'cedula', 'email', 'estado_usuario', 'fecha_nacimiento', 'telefono', 'ciudad', 'genero', 'tipo_regimen', 'eps_id']
        sql_update_parts, params = [], []
        for field in allowed_fields:
            if field in user_data:
                sql_update_parts.append(f"{field} = %s")
                params.append(user_data[field] or None)
        if user_data.get('contrasena_nueva'):
            sql_update_parts.append("contrasena = %s")
            params.append(generate_password_hash(user_data['contrasena_nueva']))
        if not sql_update_parts: return True
        sql_update = f"UPDATE usuarios SET {', '.join(sql_update_parts)} WHERE id=%s AND rol='cliente'"
        params.append(uid)
        cur.execute(sql_update, tuple(params))
        conn.commit()
        
        # ***** CORRECCIÓN *****
        # Ya no se pasa 'admin_id_actual'.
        accion_audit = 'EDICION_CLIENTE'
        if old_user_data.get('estado_usuario') == 'activo' and user_data.get('estado_usuario') == 'inactivo':
            accion_audit = 'DESACTIVACION_CLIENTE'
        elif old_user_data.get('estado_usuario') == 'inactivo' and user_data.get('estado_usuario') == 'activo':
            accion_audit = 'REACTIVACION_CLIENTE'
        datos_nuevos_cleaned = {k: (v or None) for k, v in user_data.items() if k != 'contrasena_nueva'}
        if user_data.get('contrasena_nueva'): datos_nuevos_cleaned['contrasena'] = "********"
        
        registrar_auditoria_aplicacion(accion_audit, tabla_afectada='usuarios', registro_id=str(uid), datos_anteriores=dict(old_user_data), datos_nuevos=datos_nuevos_cleaned)
        
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise ValueError(f'Error de integridad al actualizar: {e}')
    finally:
        if conn: conn.close()

def get_eps_list():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, nombre FROM eps WHERE estado = 'activo' ORDER BY nombre")
        return cur.fetchall()
    finally:
        if conn: conn.close()
