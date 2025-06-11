# medialert/services/auth_service.py

import psycopg2
from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, session

from database import get_db_connection, registrar_auditoria_aplicacion

def verify_and_login_user(cedula, password_ingresada):
    """Verifica credenciales de usuario y establece la sesión."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, nombre, rol, contrasena as hashed_password FROM usuarios WHERE cedula = %s AND estado_usuario = 'activo'",
            (cedula,)
        )
        user = cur.fetchone()

        if user and check_password_hash(user['hashed_password'], password_ingresada):
            session['user_id'] = user['id']
            session['nombre'] = user['nombre']
            session['rol'] = user['rol']
            
            registrar_auditoria_aplicacion(
                'INICIO_SESION_EXITOSO', 
                detalles_adicionales={'usuario_cedula': cedula, 'nombre_usuario': user['nombre']}
            )
            return {'id': user['id'], 'nombre': user['nombre'], 'rol': user['rol']}
        else:
            registrar_auditoria_aplicacion(
                'INICIO_SESION_FALLIDO', 
                detalles_adicionales={'usuario_cedula': cedula, 'motivo': 'Credenciales inválidas o usuario inactivo'}
            )
            return None # Credenciales inválidas
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD durante el login: {e}")
        raise # Propagar el error para que la ruta lo maneje
    finally:
        if conn:
            conn.close()

def logout_user():
    """Cierra la sesión del usuario y registra la auditoría."""
    usuario_nombre = session.get('nombre', 'Desconocido')
    usuario_id = session.get('user_id')
    
    session.clear() 
    
    registrar_auditoria_aplicacion(
        'CIERRE_SESION', 
        detalles_adicionales={'usuario_id_cerrado': usuario_id, 'nombre_usuario_cerrado': usuario_nombre}
    )

def get_current_user_session_info():
    """Devuelve la información de sesión del usuario actual."""
    return {
        'user_id': session.get('user_id'),
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    }

def update_user_password(user_id, current_password, new_password):
    """Actualiza la contraseña de un usuario."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("SELECT contrasena as hashed_password FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user or not check_password_hash(user['hashed_password'], current_password):
            registrar_auditoria_aplicacion(
                'CAMBIO_CONTRASENA_FALLIDO',
                tabla_afectada='usuarios',
                registro_id=str(user_id),
                detalles_adicionales={'motivo': 'Contraseña actual incorrecta'}
            )
            return False, "La contraseña actual es incorrecta."
            
        new_password_hashed = generate_password_hash(new_password)
        cur.execute("UPDATE usuarios SET contrasena = %s WHERE id = %s", (new_password_hashed, user_id))
        conn.commit()
        
        registrar_auditoria_aplicacion(
            'CAMBIO_CONTRASENA_EXITOSO',
            tabla_afectada='usuarios',
            registro_id=str(user_id),
            datos_anteriores={'contrasena': '********'}, 
            datos_nuevos={'contrasena': '********'}
        )
        return True, "Contraseña actualizada con éxito."
        
    except psycopg2.Error as e:
        current_app.logger.error(f"Error de BD al cambiar contraseña para usuario {user_id}: {e}")
        if conn: conn.rollback()
        raise # Propagar el error
    finally:
        if conn:
            conn.close()