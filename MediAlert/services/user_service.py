# medialert/services/user_service.py

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash
from datetime import datetime, date
from flask import current_app, session

from database import get_db_connection, registrar_auditoria_aplicacion

def get_users(estado_filtro=None, rol_filtro=None, search_query=None):
    """Obtiene una lista de usuarios basada en filtros."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query_parts = ["""
            SELECT u.id, u.nombre, u.cedula, u.email, u.rol, u.estado_usuario, 
                   u.fecha_nacimiento, u.telefono, u.ciudad, u.fecha_registro,
                   u.eps_id, e.nombre as eps_nombre
            FROM usuarios u
            LEFT JOIN eps e ON u.eps_id = e.id
        """]
        conditions = []
        params = []

        if rol_filtro:
            if rol_filtro == 'cliente':
                conditions.append("rol = 'cliente'")
            elif rol_filtro == 'admin':
                conditions.append("rol = 'admin'")

        if estado_filtro and estado_filtro != 'todos':
            conditions.append("estado_usuario = %s")
            params.append(estado_filtro)

        if search_query:
            conditions.append("(nombre ILIKE %s OR cedula ILIKE %s)")
            params.append(f"%{search_query}%")
            params.append(f"%{search_query}%")

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY rol, nombre")

        final_query = " ".join(query_parts)
        cur.execute(final_query, tuple(params))
        users = cur.fetchall()
        return users
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener usuarios: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_user_by_id(uid):
    """Obtiene un usuario por su ID."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT id, nombre, cedula, email, rol, estado_usuario, fecha_nacimiento, telefono, ciudad, fecha_registro, eps_id 
            FROM usuarios 
            WHERE id = %s
            """, (uid,))
        user = cur.fetchone()
        return user
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener usuario {uid}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def create_user(user_data, admin_id_actual):
    """Crea un nuevo usuario (cliente)."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        nombre = user_data.get('nombre')
        cedula = user_data.get('cedula')
        email = user_data.get('email')
        contrasena_plain = user_data.get('contrasena')
        fecha_nacimiento = user_data.get('fecha_nacimiento')
        telefono = user_data.get('telefono')
        ciudad = user_data.get('ciudad')
        eps_id = user_data.get('eps_id')

        rol_nuevo_usuario = 'cliente'
        estado_nuevo_usuario = 'activo'
        fecha_registro_actual = datetime.now().date()

        if not all([nombre, cedula, email, contrasena_plain]):
            raise ValueError('Nombre, cédula, email y contraseña son requeridos.')
        
        if fecha_nacimiento:
            if isinstance(fecha_nacimiento, date):
                fecha_nacimiento_str = fecha_nacimiento.isoformat()
            else:
                fecha_nacimiento_str = fecha_nacimiento
            try:
                datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Formato de fecha de nacimiento inválido. UsebeginPath-MM-DD.')

        hashed_password = generate_password_hash(contrasena_plain)
        
        cur.execute(
            """
            INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario, 
                                  fecha_nacimiento, telefono, ciudad, fecha_registro, eps_id) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (nombre, cedula, email, hashed_password, rol_nuevo_usuario, estado_nuevo_usuario,
             fecha_nacimiento, telefono, ciudad, fecha_registro_actual, eps_id)
        )
        new_id = cur.fetchone()['id']
        conn.commit()
        
        datos_nuevos_audit = {
            'nombre': nombre, 'cedula': cedula, 'email': email, 'rol': rol_nuevo_usuario, 
            'estado_usuario': estado_nuevo_usuario, 'fecha_nacimiento': fecha_nacimiento,
            'telefono': telefono, 'ciudad': ciudad, 'fecha_registro': fecha_registro_actual.isoformat(),
            'eps_id': eps_id
        }
        registrar_auditoria_aplicacion(
            'CREACION_CLIENTE', 
            tabla_afectada='usuarios', 
            registro_id=str(new_id),
            datos_nuevos=datos_nuevos_audit,
            detalles_adicionales={'creado_por_admin_id': admin_id_actual}
        )
        return new_id
    except psycopg2.IntegrityError as e: 
        conn.rollback()
        if "usuarios_cedula_key" in str(e):
            raise ValueError(f'La cédula "{cedula}" ya está registrada.')
        if "usuarios_email_key" in str(e):
            raise ValueError(f'El email "{email}" ya está registrado.')
        current_app.logger.error(f"Error de integridad al crear cliente: {e}")
        raise
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al crear cliente: {e}")
        raise
    finally:
        if conn:
            conn.close()

def update_user(uid, user_data, old_user_data, admin_id_actual):
    """Actualiza la información de un usuario existente."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        nombre = user_data.get('nombre', old_user_data['nombre'])
        cedula = user_data.get('cedula', old_user_data['cedula'])
        email = user_data.get('email', old_user_data['email'])
        estado_usuario = user_data.get('estado_usuario', old_user_data['estado_usuario'])
        fecha_nacimiento = user_data.get('fecha_nacimiento', old_user_data['fecha_nacimiento'])
        if fecha_nacimiento == '': fecha_nacimiento = None
        telefono = user_data.get('telefono', old_user_data['telefono'])
        if telefono == '': telefono = None
        ciudad = user_data.get('ciudad', old_user_data['ciudad'])
        if ciudad == '': ciudad = None
        eps_id = user_data.get('eps_id', old_user_data.get('eps_id'))
        if eps_id == '': eps_id = None

        if estado_usuario not in ['activo', 'inactivo']:
            raise ValueError('Valor de estado_usuario no válido.')
        
        if fecha_nacimiento:
            if isinstance(fecha_nacimiento, date):
                fecha_nacimiento_str = fecha_nacimiento.isoformat()
            else:
                fecha_nacimiento_str = fecha_nacimiento
            try:
                datetime.strptime(fecha_nacimiento_str, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Formato de fecha de nacimiento inválido. UsebeginPath-MM-DD.')

        new_password_plain = user_data.get('contrasena_nueva')
        sql_update_parts = ["nombre=%s", "cedula=%s", "email=%s", "estado_usuario=%s", 
                            "fecha_nacimiento=%s", "telefono=%s", "ciudad=%s", "eps_id=%s"]
        params = [nombre, cedula, email, estado_usuario, fecha_nacimiento, telefono, ciudad, eps_id]
        
        if new_password_plain:
            hashed_new_password = generate_password_hash(new_password_plain)
            sql_update_parts.append("contrasena=%s")
            params.append(hashed_new_password)
        
        sql_update = f"UPDATE usuarios SET {', '.join(sql_update_parts)} WHERE id=%s AND rol='cliente'"
        params.append(uid)

        cur.execute(sql_update, tuple(params))
        conn.commit()
        
        accion_audit = 'EDICION_CLIENTE'
        if old_user_data['estado_usuario'] == 'activo' and estado_usuario == 'inactivo':
            accion_audit = 'DESACTIVACION_CLIENTE'
        elif old_user_data['estado_usuario'] == 'inactivo' and estado_usuario == 'activo':
             accion_audit = 'REACTIVACION_CLIENTE'

        datos_nuevos_audit = {
            'nombre': nombre, 'cedula': cedula, 'email': email, 'estado_usuario': estado_usuario,
            'fecha_nacimiento': fecha_nacimiento, 'telefono': telefono, 'ciudad': ciudad,
            'eps_id': eps_id
        }
        if new_password_plain: datos_nuevos_audit['contrasena'] = "********"

        registrar_auditoria_aplicacion(
            accion_audit, 
            tabla_afectada='usuarios', 
            registro_id=str(uid),
            datos_anteriores=dict(old_user_data),
            datos_nuevos=datos_nuevos_audit,
            detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
        )
        return True
    except psycopg2.IntegrityError as e:
        conn.rollback()
        raise ValueError(f'Error de integridad al actualizar: {e}')
    except psycopg2.Error as e:
        conn.rollback()
        current_app.logger.error(f"Error de BD al actualizar cliente {uid}: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_eps_list():
    """Obtiene una lista de EPS activas."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, nombre FROM eps WHERE estado = 'activo' ORDER BY nombre")
        eps_list = cur.fetchall()
        return eps_list
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al obtener EPS: {e}")
        raise
    finally:
        if conn:
            conn.close()