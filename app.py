import psycopg2
from psycopg2.extras import RealDictCursor, Json
from flask import Flask, request, jsonify, session, send_from_directory, render_template
from flask_cors import CORS
from functools import wraps
import json
from werkzeug.security import generate_password_hash, check_password_hash
import os
import logging
from dotenv import load_dotenv
from datetime import date, time, datetime
import uuid
from werkzeug.utils import secure_filename

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# --- Configuración de Conexión a la Base de Datos ---
PG_HOST = os.getenv('PG_HOST')
PG_DB = os.getenv('PG_DB')
PG_USER = os.getenv('PG_USER')
PG_PASS = os.getenv('PG_PASS')
PG_PORT = os.getenv('PG_PORT', '5432')

# --- Configuración para Almacenamiento de Reportes ---
INSTANCE_FOLDER_PATH = os.path.join(app.root_path, '..', 'instance')
REPORTS_STORAGE_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'generated_reports')
if not os.path.exists(REPORTS_STORAGE_PATH):
    os.makedirs(REPORTS_STORAGE_PATH, exist_ok=True)

app.config['REPORTS_STORAGE_PATH'] = REPORTS_STORAGE_PATH
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_db_connection():
    """Establece y devuelve una conexión a la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT
        )
        if 'user_id' in session:
            with conn.cursor() as cur:
                cur.execute("SELECT set_config('medialert.app_user_id', %s, true);", (str(session['user_id']),))
        return conn
    except psycopg2.Error as e:
        app.logger.error(f"Error al conectar con la base de datos: {e}")
        raise

# --- Decoradores de Autorización ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Autenticación requerida. Por favor, inicie sesión.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'admin':
            return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador.'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Función de Auditoría de Aplicación ---
def registrar_auditoria_aplicacion(accion, tabla_afectada=None, registro_id=None,
                                   datos_anteriores=None, datos_nuevos=None, detalles_adicionales=None):
    """
    Registra una acción en la tabla de auditoría llamando a la función de PostgreSQL
    sp_registrar_evento_auditoria.
    Los datos (anteriores, nuevos, adicionales) deben ser diccionarios de Python.
    """
    def serialize_data(obj):
        """Convierte recursivamente objetos date, time, y datetime a strings ISO en un diccionario o lista."""
        if isinstance(obj, dict):
            return {k: serialize_data(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize_data(i) for i in obj]
        elif isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return obj

    app_user_id = session.get('user_id')

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        p_datos_anteriores = Json(serialize_data(datos_anteriores)) if datos_anteriores is not None else None
        p_datos_nuevos = Json(serialize_data(datos_nuevos)) if datos_nuevos is not None else None
        p_detalles_adicionales = Json(serialize_data(detalles_adicionales)) if detalles_adicionales is not None else None

        cur.execute(
            "SELECT sp_registrar_evento_auditoria(%s, %s, %s, %s, %s, %s, %s);",
            (app_user_id, accion, tabla_afectada, registro_id,
             p_datos_anteriores, p_datos_nuevos, p_detalles_adicionales)
        )
        conn.commit()
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al registrar auditoría de aplicación ({accion}): {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        app.logger.error(f"Error general al registrar auditoría de aplicación ({accion}): {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

# --- Rutas de Autenticación y Sesión ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    cedula = data.get('cedula')
    password_ingresada = data.get('contrasena')

    if not cedula or not password_ingresada:
        return jsonify({'error': 'Cédula y contraseña son requeridas.'}), 400

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
            return jsonify({'id': user['id'], 'nombre': user['nombre'], 'rol': user['rol']})
        else:
            registrar_auditoria_aplicacion(
                'INICIO_SESION_FALLIDO',
                detalles_adicionales={'usuario_cedula': cedula, 'motivo': 'Credenciales inválidas o usuario inactivo'}
            )
            return jsonify({'error': 'Credenciales inválidas o usuario inactivo.'}), 401
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD durante el login: {e}")
        return jsonify({'error': 'Error interno del servidor al intentar iniciar sesión.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    try:
        usuario_nombre = session.get('nombre', 'Desconocido')
        usuario_id = session.get('user_id')

        session.clear()

        registrar_auditoria_aplicacion(
            'CIERRE_SESION',
            detalles_adicionales={'usuario_id_cerrado': usuario_id, 'nombre_usuario_cerrado': usuario_nombre}
        )
        return jsonify({'message': 'Cierre de sesión exitoso.'}), 200
    except Exception as e:
        app.logger.error(f"Error durante el logout: {e}")
        return jsonify({'error': 'Error interno al cerrar sesión.', 'details': str(e)}), 500

@app.route('/api/session_check', methods=['GET'])
@login_required
def session_check():
    return jsonify({
        'user_id': session.get('user_id'),
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    })

# --- API: GESTIÓN DE CLIENTES (Usuarios con rol 'cliente') ---
@app.route('/api/admin/clientes', methods=['GET', 'POST'])
@admin_required
def manage_clientes():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            estado_filtro = request.args.get('estado', None)
            rol_filtro = request.args.get('rol', None)
            search_query = request.args.get('query', None)

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
            return jsonify(users)

        if request.method == 'POST':
            data = request.json
            nombre = data.get('nombre')
            cedula = data.get('cedula')
            email = data.get('email')
            contrasena_plain = data.get('contrasena')
            fecha_nacimiento = data.get('fecha_nacimiento')
            telefono = data.get('telefono')
            ciudad = data.get('ciudad')
            eps_id = data.get('eps_id')

            rol_nuevo_usuario = 'cliente'
            estado_nuevo_usuario = 'activo'
            fecha_registro_actual = datetime.now().date()

            if not all([nombre, cedula, email, contrasena_plain]):
                return jsonify({'error': 'Nombre, cédula, email y contraseña son requeridos.'}), 400

            if fecha_nacimiento:
                try:
                    if isinstance(fecha_nacimiento, date):
                        fecha_nacimiento = fecha_nacimiento.isoformat()
                    datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
                except ValueError:
                    return jsonify({'error': 'Formato de fecha de nacimiento inválido. UsebeginPath-MM-DD.'}), 400

            hashed_password = generate_password_hash(contrasena_plain)

            try:
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
                return jsonify({'message': 'Cliente creado con éxito.', 'id': new_id}), 201
            except psycopg2.IntegrityError as e:
                conn.rollback()
                if "usuarios_cedula_key" in str(e):
                    return jsonify({'error': f'La cédula "{cedula}" ya está registrada.'}), 409
                if "usuarios_email_key" in str(e):
                    return jsonify({'error': f'El email "{email}" ya está registrado.'}), 409
                app.logger.error(f"Error de integridad al crear cliente: {e}")
                return jsonify({'error': 'Error de integridad de datos al crear cliente.'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al crear cliente: {e}")
                return jsonify({'error': 'Error de base de datos al crear cliente.'}), 500
    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_clientes: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/admin/clientes/<int:uid>', methods=['GET', 'PUT'])
@admin_required
def manage_single_cliente(uid):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        cur.execute("""
            SELECT id, nombre, cedula, email, rol, estado_usuario, fecha_nacimiento, telefono, ciudad, fecha_registro, eps_id
            FROM usuarios
            WHERE id = %s
            """, (uid,))
        current_user_data = cur.fetchone()

        if not current_user_data:
            return jsonify({'error': 'Usuario no encontrado.'}), 404

        if current_user_data['rol'] != 'cliente':
             return jsonify({'error': 'Esta ruta es solo para gestionar clientes.'}), 403


        if request.method == 'GET':
            return jsonify(current_user_data)

        if request.method == 'PUT':
            data = request.json

            nombre = data.get('nombre', current_user_data['nombre'])
            cedula = data.get('cedula', current_user_data['cedula'])
            email = data.get('email', current_user_data['email'])
            estado_usuario = data.get('estado_usuario', current_user_data['estado_usuario'])

            fecha_nacimiento = data.get('fecha_nacimiento', current_user_data['fecha_nacimiento'])
            if fecha_nacimiento == '': fecha_nacimiento = None
            telefono = data.get('telefono', current_user_data['telefono'])
            if telefono == '': telefono = None
            ciudad = data.get('ciudad', current_user_data['ciudad'])
            if ciudad == '': ciudad = None
            eps_id = data.get('eps_id', current_user_data.get('eps_id'))
            if eps_id == '': eps_id = None

            if estado_usuario not in ['activo', 'inactivo']:
                return jsonify({'error': 'Valor de estado_usuario no válido.'}), 400

            if fecha_nacimiento:
                try:
                    if isinstance(fecha_nacimiento, date):
                        fecha_nacimiento = fecha_nacimiento.isoformat()
                    datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
                except ValueError:
                    return jsonify({'error': 'Formato de fecha de nacimiento inválido. UsebeginPath-MM-DD.'}), 400

            new_password_plain = data.get('contrasena_nueva')
            sql_update_parts = ["nombre=%s", "cedula=%s", "email=%s", "estado_usuario=%s",
                                "fecha_nacimiento=%s", "telefono=%s", "ciudad=%s", "eps_id=%s"]
            params = [nombre, cedula, email, estado_usuario, fecha_nacimiento, telefono, ciudad, eps_id]

            if new_password_plain:
                hashed_new_password = generate_password_hash(new_password_plain)
                sql_update_parts.append("contrasena=%s")
                params.append(hashed_new_password)

            sql_update = f"UPDATE usuarios SET {', '.join(sql_update_parts)} WHERE id=%s AND rol='cliente'"
            params.append(uid)

            try:
                cur.execute(sql_update, tuple(params))
                conn.commit()

                accion_audit = 'EDICION_CLIENTE'
                if current_user_data['estado_usuario'] == 'activo' and estado_usuario == 'inactivo':
                    accion_audit = 'DESACTIVACION_CLIENTE'
                elif current_user_data['estado_usuario'] == 'inactivo' and estado_usuario == 'activo':
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
                    datos_anteriores=dict(current_user_data),
                    datos_nuevos=datos_nuevos_audit,
                    detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': f'Cliente {uid} actualizado con éxito.'})
            except psycopg2.IntegrityError as e:
                conn.rollback()
                return jsonify({'error': f'Error de integridad al actualizar: {e}'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al actualizar cliente {uid}: {e}")
                return jsonify({'error': f'Error de base de datos al actualizar cliente {uid}.'}), 500
    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_single_cliente {uid}: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

# --- API: CONFIGURACIÓN DE USUARIO ---
@app.route('/api/configuracion/usuario', methods=['GET'])
@login_required
def get_configuracion_usuario():
    user_id = session.get('user_id')
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT u.id, u.nombre, u.cedula, u.email, u.rol, u.estado_usuario,
                   u.fecha_nacimiento, u.telefono, u.ciudad, u.fecha_registro,
                   u.eps_id, e.nombre as eps_nombre
            FROM usuarios u
            LEFT JOIN eps e ON u.eps_id = e.id
            WHERE u.id = %s
        """, (user_id,))
        user_data = cur.fetchone()
        if not user_data:
            return jsonify({'error': 'Usuario no encontrado.'}), 404
        return jsonify(user_data)
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener datos de configuración del usuario {user_id}: {e}")
        return jsonify({'error': 'Error al cargar datos de configuración.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/configuracion/cambiar_contrasena', methods=['POST'])
@login_required
def cambiar_contrasena_usuario():
    user_id = session.get('user_id')
    data = request.json
    contrasena_actual = data.get('contrasena_actual')
    contrasena_nueva = data.get('contrasena_nueva')
    contrasena_nueva_confirmacion = data.get('contrasena_nueva_confirmacion')

    if not all([contrasena_actual, contrasena_nueva, contrasena_nueva_confirmacion]):
        return jsonify({'error': 'Todos los campos de contraseña son requeridos.'}), 400

    if contrasena_nueva != contrasena_nueva_confirmacion:
        return jsonify({'error': 'La nueva contraseña y su confirmación no coinciden.'}), 400

    if len(contrasena_nueva) < 6:
        return jsonify({'error': 'La nueva contraseña debe tener al menos 6 caracteres.'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT contrasena as hashed_password FROM usuarios WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user or not check_password_hash(user['hashed_password'], contrasena_actual):
            registrar_auditoria_aplicacion(
                'CAMBIO_CONTRASENA_FALLIDO',
                tabla_afectada='usuarios',
                registro_id=str(user_id),
                detalles_adicionales={'motivo': 'Contraseña actual incorrecta'}
            )
            return jsonify({'error': 'La contraseña actual es incorrecta.'}), 401

        nueva_contrasena_hashed = generate_password_hash(contrasena_nueva)
        cur.execute("UPDATE usuarios SET contrasena = %s WHERE id = %s", (nueva_contrasena_hashed, user_id))
        conn.commit()

        registrar_auditoria_aplicacion(
            'CAMBIO_CONTRASENA_EXITOSO',
            tabla_afectada='usuarios',
            registro_id=str(user_id),
            datos_anteriores={'contrasena': '********'},
            datos_nuevos={'contrasena': '********'}
        )
        return jsonify({'message': 'Contraseña actualizada con éxito.'})

    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al cambiar contraseña para usuario {user_id}: {e}")
        if conn: conn.rollback()
        return jsonify({'error': 'Error de base de datos al cambiar la contraseña.'}), 500
    except Exception as e:
        app.logger.error(f"Error general al cambiar contraseña para usuario {user_id}: {e}")
        if conn: conn.rollback()
        return jsonify({'error': 'Error interno del servidor al cambiar la contraseña.'}), 500
    finally:
        if conn:
            conn.close()

# --- API: GESTIÓN DE MEDICAMENTOS ---
@app.route('/api/admin/medicamentos', methods=['GET', 'POST'])
@admin_required
def manage_medicamentos():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            estado_filtro = request.args.get('estado', 'disponible')
            if estado_filtro not in ['disponible', 'discontinuado', 'todos']:
                estado_filtro = 'disponible'

            query = "SELECT id, nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento FROM medicamentos"
            params = []
            if estado_filtro != 'todos':
                query += " WHERE estado_medicamento = %s"
                params.append(estado_filtro)
            query += " ORDER BY nombre"

            cur.execute(query, tuple(params))
            medicamentos = cur.fetchall()
            return jsonify(medicamentos)

        if request.method == 'POST':
            data = request.json
            nombre = data.get('nombre')
            descripcion = data.get('descripcion')
            composicion = data.get('composicion')
            sintomas_secundarios = data.get('sintomas_secundarios')
            indicaciones = data.get('indicaciones')
            rango_edad = data.get('rango_edad')

            if not nombre:
                return jsonify({'error': 'El nombre del medicamento es requerido.'}), 400

            try:
                cur.execute(
                    """
                    INSERT INTO medicamentos (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento)
                    VALUES (%s, %s, %s, %s, %s, %s, 'disponible') RETURNING id
                    """,
                    (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad)
                )
                new_id = cur.fetchone()['id']
                conn.commit()
                registrar_auditoria_aplicacion(
                    'CREACION_MEDICAMENTO',
                    tabla_afectada='medicamentos',
                    registro_id=str(new_id),
                    datos_nuevos=data,
                    detalles_adicionales={'creado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': 'Medicamento creado con éxito.', 'id': new_id}), 201
            except psycopg2.IntegrityError as e:
                conn.rollback()
                return jsonify({'error': f'El medicamento "{nombre}" ya existe.'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al crear medicamento: {e}")
                return jsonify({'error': 'Error de base de datos al crear medicamento.'}), 500
    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_medicamentos: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/admin/medicamentos/<int:mid>', methods=['GET','PUT'])
@admin_required
def manage_single_medicamento(mid):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            cur.execute("SELECT * FROM medicamentos WHERE id = %s", (mid,))
            medicamento = cur.fetchone()
            if not medicamento:
                return jsonify({'error': 'Medicamento no encontrado.'}), 404
            return jsonify(medicamento)

        if request.method == 'PUT':
            data = request.json

            cur.execute("SELECT * FROM medicamentos WHERE id = %s", (mid,))
            old_med_data = cur.fetchone()
            if not old_med_data:
                return jsonify({'error': 'Medicamento no encontrado para actualizar.'}), 404

            nombre = data.get('nombre', old_med_data['nombre'])
            descripcion = data.get('descripcion', old_med_data['descripcion'])
            composicion = data.get('composicion', old_med_data['composicion'])
            sintomas_secundarios = data.get('sintomas_secundarios', old_med_data['sintomas_secundarios'])
            indicaciones = data.get('indicaciones', old_med_data['indicaciones'])
            rango_edad = data.get('rango_edad', old_med_data['rango_edad'])
            estado_medicamento = data.get('estado_medicamento', old_med_data['estado_medicamento'])

            if estado_medicamento not in ['disponible', 'discontinuado']:
                 return jsonify({'error': 'Valor de estado_medicamento no válido.'}), 400

            try:
                cur.execute(
                    """
                    UPDATE medicamentos SET nombre=%s, descripcion=%s, composicion=%s,
                    sintomas_secundarios=%s, indicaciones=%s, rango_edad=%s, estado_medicamento=%s
                    WHERE id=%s
                    """,
                    (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento, mid)
                )
                conn.commit()

                accion_audit = 'EDICION_MEDICAMENTO'
                if old_med_data['estado_medicamento'] == 'disponible' and estado_medicamento == 'discontinuado':
                    accion_audit = 'DISCONTINUACION_MEDICAMENTO'
                elif old_med_data['estado_medicamento'] == 'discontinuado' and estado_medicamento == 'disponible':
                    accion_audit = 'REACTIVACION_MEDICAMENTO'

                registrar_auditoria_aplicacion(
                    accion_audit,
                    tabla_afectada='medicamentos',
                    registro_id=str(mid),
                    datos_anteriores=dict(old_med_data),
                    datos_nuevos=data,
                    detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': f'Medicamento {mid} actualizado con éxito.'})
            except psycopg2.IntegrityError as e:
                conn.rollback()
                return jsonify({'error': f'El nombre de medicamento "{nombre}" ya existe para otro ID.'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al actualizar medicamento {mid}: {e}")
                return jsonify({'error': f'Error de base de datos al actualizar medicamento {mid}.'}), 500
    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_single_medicamento {mid}: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

# --- API: GESTIÓN DE ALERTAS ---
@app.route('/api/admin/alertas', methods=['GET', 'POST'])
@admin_required
def manage_alertas_admin():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            usuario_id_filtro = request.args.get('usuario_id', type=int)
            group_by_client = request.args.get('group_by_client', 'false').lower() == 'true'
            search_query = request.args.get('query', None)

            if group_by_client:
                query = """
                    SELECT
                        u.id as usuario_id,
                        u.nombre as cliente_nombre,
                        u.cedula,
                        u.estado_usuario,
                        COUNT(CASE WHEN a.estado = 'activa' THEN 1 ELSE NULL END) as alertas_activas_count,
                        COUNT(a.id) as total_alertas_count
                    FROM usuarios u
                    LEFT JOIN alertas a ON u.id = a.usuario_id
                    WHERE u.rol = 'cliente'
                    GROUP BY u.id, u.nombre, u.cedula, u.estado_usuario
                    ORDER BY u.nombre;
                """
                cur.execute(query)
                clientes_con_alertas = cur.fetchall()
                return jsonify(clientes_con_alertas)

            else:
                query_parts = ["""
                    SELECT
                        a.id, a.usuario_id, u.nombre as cliente_nombre, u.estado_usuario,
                        a.medicamento_id, m.nombre as medicamento_nombre, m.estado_medicamento,
                        a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida,
                        a.estado as estado_alerta, a.asignado_por_usuario_id, ap.nombre as asignador_nombre
                    FROM alertas a
                    JOIN usuarios u ON a.usuario_id = u.id
                    JOIN medicamentos m ON a.medicamento_id = m.id
                    LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
                """]
                conditions = []
                params = []

                if usuario_id_filtro:
                    conditions.append("a.usuario_id = %s")
                    params.append(usuario_id_filtro)

                if conditions:
                    query_parts.append("WHERE " + " AND ".join(conditions))

                query_parts.append("ORDER BY u.nombre, m.nombre, a.fecha_inicio")

                final_query = " ".join(query_parts)
                cur.execute(final_query, tuple(params))
                alertas = cur.fetchall()

                for alerta in alertas:
                    if isinstance(alerta.get('hora_preferida'), (time,)):
                        alerta['hora_preferida'] = alerta['hora_preferida'].strftime('%H:%M:%S')
                return jsonify(alertas)

        if request.method == 'POST':
            data = request.json
            usuario_id = data.get('usuario_id')
            medicamento_id = data.get('medicamento_id')
            fecha_inicio = data.get('fecha_inicio')

            if not all([usuario_id, medicamento_id, fecha_inicio]):
                return jsonify({'error': 'ID de usuario, ID de medicamento y fecha de inicio son requeridos.'}), 400

            cur.execute("SELECT estado_usuario FROM usuarios WHERE id = %s AND rol = 'cliente'", (usuario_id,))
            user_check = cur.fetchone()
            if not user_check or user_check['estado_usuario'] != 'activo':
                return jsonify({'error': 'El usuario seleccionado no es un cliente activo.'}), 400

            cur.execute("SELECT estado_medicamento FROM medicamentos WHERE id = %s", (medicamento_id,))
            med_check = cur.fetchone()
            if not med_check or med_check['estado_medicamento'] != 'disponible':
                return jsonify({'error': 'El medicamento seleccionado no está disponible.'}), 400

            dosis = data.get('dosis')
            frecuencia = data.get('frecuencia')
            fecha_fin = data.get('fecha_fin') if data.get('fecha_fin') else None
            hora_preferida = data.get('hora_preferida') if data.get('hora_preferida') else None
            estado_alerta = data.get('estado', 'activa')

            if estado_alerta not in ['activa', 'inactiva', 'completada', 'fallida']:
                return jsonify({'error': 'Valor de estado de alerta no válido.'}), 400

            try:
                cur.execute(
                    """
                    INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, asignado_por_usuario_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado_alerta, admin_id_actual)
                )
                new_id = cur.fetchone()['id']
                conn.commit()
                registrar_auditoria_aplicacion(
                    'CREACION_ALERTA',
                    tabla_afectada='alertas',
                    registro_id=str(new_id),
                    datos_nuevos=data,
                    detalles_adicionales={'creado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': 'Alerta creada con éxito.', 'id': new_id}), 201
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al crear alerta: {e}")
                return jsonify({'error': 'Error de base de datos al crear alerta.'}), 500
    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_alertas_admin: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/admin/alertas/<int:alerta_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def manage_single_alerta_admin(alerta_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            cur.execute("SELECT * FROM alertas WHERE id = %s", (alerta_id,))
            alerta = cur.fetchone()
            if not alerta:
                return jsonify({'error': 'Alerta no encontrada.'}), 404
            if isinstance(alerta.get('hora_preferida'), (time,)):
                alerta['hora_preferida'] = alerta['hora_preferida'].strftime('%H:%M:%S')
            return jsonify(alerta)

        if request.method == 'PUT':
            data = request.json
            cur.execute("SELECT * FROM alertas WHERE id = %s", (alerta_id,))
            old_alerta_data = cur.fetchone()
            if not old_alerta_data:
                return jsonify({'error': 'Alerta no encontrada para actualizar.'}), 404

            usuario_id = data.get('usuario_id', old_alerta_data['usuario_id'])
            medicamento_id = data.get('medicamento_id', old_alerta_data['medicamento_id'])
            dosis = data.get('dosis', old_alerta_data['dosis'])
            frecuencia = data.get('frecuencia', old_alerta_data['frecuencia'])
            fecha_inicio = data.get('fecha_inicio', old_alerta_data['fecha_inicio'])
            fecha_fin = data.get('fecha_fin', old_alerta_data['fecha_fin'])
            if fecha_fin == '': fecha_fin = None
            hora_preferida = data.get('hora_preferida', old_alerta_data['hora_preferida'])
            if hora_preferida == '': hora_preferida = None
            estado = data.get('estado', old_alerta_data['estado'])

            if estado not in ['activa', 'inactiva', 'completada', 'fallida']:
                return jsonify({'error': 'Valor de estado de alerta no válido.'}), 400

            try:
                cur.execute(
                    """
                    UPDATE alertas SET usuario_id=%s, medicamento_id=%s, dosis=%s, frecuencia=%s,
                    fecha_inicio=%s, fecha_fin=%s, hora_preferida=%s, estado=%s, asignado_por_usuario_id=%s
                    WHERE id=%s
                    """,
                    (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, admin_id_actual, alerta_id)
                )
                conn.commit()
                registrar_auditoria_aplicacion(
                    'EDICION_ALERTA',
                    tabla_afectada='alertas',
                    registro_id=str(alerta_id),
                    datos_anteriores=dict(old_alerta_data),
                    datos_nuevos=data,
                    detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': f'Alerta {alerta_id} actualizada con éxito.'})
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al actualizar alerta {alerta_id}: {e}")
                return jsonify({'error': f'Error de base de datos al actualizar alerta {alerta_id}.'}), 500

        if request.method == 'DELETE':
            cur.execute("SELECT * FROM alertas WHERE id = %s", (alerta_id,))
            old_alerta_data = cur.fetchone()
            if not old_alerta_data:
                return jsonify({'error': 'Alerta no encontrada para eliminar.'}), 404
            try:
                cur.execute("DELETE FROM alertas WHERE id = %s", (alerta_id,))
                conn.commit()
                registrar_auditoria_aplicacion(
                    'ELIMINACION_ALERTA',
                    tabla_afectada='alertas',
                    registro_id=str(alerta_id),
                    datos_anteriores=dict(old_alerta_data),
                    detalles_adicionales={'eliminado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': f'Alerta {alerta_id} eliminada con éxito.'})
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al eliminar alerta {alerta_id}: {e}")
                return jsonify({'error': f'Error de base de datos al eliminar alerta {alerta_id}.'}), 500
    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_single_alerta_admin {alerta_id}: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

# --- API: VISTA DEL CLIENTE ---
@app.route('/api/cliente/mis_alertas', methods=['GET'])
@login_required
def get_mis_alertas_cliente():
    if session.get('rol') != 'cliente':
        return jsonify({'error': 'Acceso denegado. Esta vista es solo para clientes.'}), 403

    cliente_id = session['user_id']
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT
                a.id, m.nombre as medicamento_nombre, a.dosis, a.frecuencia,
                a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.usuario_id = %s
            ORDER BY a.fecha_inicio DESC, a.hora_preferida DESC
        """, (cliente_id,))
        alertas = cur.fetchall()

        for alerta in alertas:
            if isinstance(alerta.get('hora_preferida'), time):
                alerta['hora_preferida'] = alerta['hora_preferida'].strftime('%H:%M:%S')

        return jsonify(alertas)
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener mis_alertas para cliente {cliente_id}: {e}")
        return jsonify({'error': 'Error al cargar tus alertas.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/cliente/recetas_consolidadas', methods=['GET'])
@login_required
def get_consolidated_recetas_cliente():
    """
    Endpoint para que un cliente obtenga una lista consolidada de sus alertas activas
    para generar una receta médica.
    """
    # Check if a specific user_id is provided (admin scenario)
    user_id_param = request.args.get('user_id', type=int)

    if session.get('rol') == 'cliente' and user_id_param and user_id_param != session.get('user_id'):
        return jsonify({'error': 'Acceso denegado. Un cliente solo puede ver sus propias recetas consolidadas.'}), 403
    elif session.get('rol') == 'cliente' and not user_id_param:
        # If client is requesting their own data without user_id param
        cliente_id = session.get('user_id')
    elif session.get('rol') == 'admin' and user_id_param:
        # If admin is requesting a specific client's data
        cliente_id = user_id_param
    else:
        return jsonify({'error': 'Acceso denegado. Esta vista es solo para clientes o administradores solicitando data específica.'}), 403


    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                a.id as alerta_id, a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado as estado_alerta,
                m.nombre as medicamento_nombre, m.descripcion as medicamento_descripcion, m.composicion as medicamento_composicion,
                m.indicaciones as medicamento_indicaciones, m.sintomas_secundarios as medicamento_sintomas_secundarios,
                m.rango_edad as medicamento_rango_edad,
                u.nombre as cliente_nombre, u.cedula as cliente_cedula, u.fecha_nacimiento as cliente_fecha_nacimiento,
                u.telefono as cliente_telefono, u.ciudad as cliente_ciudad,
                e.nombre as eps_nombre, e.nit as eps_nit,
                ap.nombre as asignador_nombre, ap.cedula as asignador_cedula, ap.rol as asignador_rol
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN eps e ON u.eps_id = e.id
            LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            WHERE a.usuario_id = %s AND a.estado = 'activa' AND m.estado_medicamento = 'disponible'
            ORDER BY m.nombre;
        """, (cliente_id,))
        recetas_data = cur.fetchall()

        if not recetas_data:
            return jsonify({'message': 'No hay alertas activas para generar una receta consolidada.'}), 200

        for receta in recetas_data:
            if receta.get('fecha_inicio'):
                receta['fecha_inicio'] = receta['fecha_inicio'].isoformat()
            if receta.get('fecha_fin'):
                receta['fecha_fin'] = receta['fecha_fin'].isoformat()
            if receta.get('hora_preferida'):
                receta['hora_preferida'] = str(receta['hora_preferida'])
            if receta.get('cliente_fecha_nacimiento'):
                receta['cliente_fecha_nacimiento'] = receta['cliente_fecha_nacimiento'].isoformat()

        return jsonify(recetas_data)

    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener recetas consolidadas para cliente {cliente_id}: {e}")
        return jsonify({'error': 'Error al cargar las recetas consolidadas.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/admin/recetas_consolidadas', methods=['GET'])
@admin_required
def get_consolidated_recetas_admin():
    """
    Endpoint para que un administrador obtenga una lista consolidada de TODAS las alertas activas
    de todos los clientes, para generar una receta médica.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("""
            SELECT
                a.id as alerta_id, a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado as estado_alerta,
                u.nombre as cliente_nombre, u.cedula as cliente_cedula, u.fecha_nacimiento as cliente_fecha_nacimiento,
                u.telefono as cliente_telefono, u.ciudad as cliente_ciudad,
                m.nombre as medicamento_nombre, m.descripcion as medicamento_descripcion, m.composicion as medicamento_composicion,
                m.indicaciones as medicamento_indicaciones, m.sintomas_secundarios as medicamento_sintomas_secundarios,
                m.rango_edad as medicamento_rango_edad,
                e.nombre as eps_nombre, e.nit as eps_nit,
                ap.nombre as asignador_nombre, ap.cedula as asignador_cedula, ap.rol as asignador_rol
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN eps e ON u.eps_id = e.id
            LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            WHERE a.estado = 'activa' AND m.estado_medicamento = 'disponible' AND u.rol = 'cliente'
            ORDER BY u.nombre, m.nombre;
        """)
        recetas_data = cur.fetchall()

        if not recetas_data:
            return jsonify({'message': 'No hay alertas activas de clientes para generar una receta consolidada.'}), 200

        for receta in recetas_data:
            if receta.get('fecha_inicio'):
                receta['fecha_inicio'] = receta['fecha_inicio'].isoformat()
            if receta.get('fecha_fin'):
                receta['fecha_fin'] = receta['fecha_fin'].isoformat()
            if receta.get('hora_preferida'):
                receta['hora_preferida'] = str(receta['hora_preferida'])
            if receta.get('cliente_fecha_nacimiento'):
                receta['cliente_fecha_nacimiento'] = receta['cliente_fecha_nacimiento'].isoformat()

        return jsonify(recetas_data)

    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener recetas consolidadas para admin: {e}")
        return jsonify({'error': 'Error al cargar las recetas consolidadas para el administrador.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/receta_medica/<int:alerta_id>', methods=['GET'])
@login_required
def get_receta_data(alerta_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if session.get('rol') == 'cliente':
            cur.execute("SELECT usuario_id FROM alertas WHERE id = %s", (alerta_id,))
            alerta_owner = cur.fetchone()
            if not alerta_owner or alerta_owner['usuario_id'] != session.get('user_id'):
                return jsonify({'error': 'No autorizado para ver esta receta.'}), 403

        cur.execute("""
            SELECT
                a.id as alerta_id, a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado as estado_alerta,
                u.nombre as cliente_nombre, u.cedula as cliente_cedula, u.fecha_nacimiento as cliente_fecha_nacimiento,
                u.telefono as cliente_telefono, u.ciudad as cliente_ciudad,
                m.nombre as medicamento_nombre, m.descripcion as medicamento_descripcion, m.composicion as medicamento_composicion,
                m.indicaciones as medicamento_indicaciones, m.sintomas_secundarios as medicamento_sintomas_secundarios,
                m.rango_edad as medicamento_rango_edad,
                e.nombre as eps_nombre, e.nit as eps_nit,
                ap.nombre as asignador_nombre, ap.cedula as asignador_cedula, ap.rol as asignador_rol
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN eps e ON u.eps_id = e.id
            LEFT JOIN usuarios ap ON a.asignado_por_usuario_id = ap.id
            WHERE a.id = %s
        """, (alerta_id,))

        receta_data = cur.fetchone()

        if not receta_data:
            return jsonify({'error': 'Alerta o receta no encontrada.'}), 404

        if receta_data.get('fecha_inicio'):
            receta_data['fecha_inicio'] = receta_data['fecha_inicio'].isoformat()
        if receta_data.get('fecha_fin'):
            receta_data['fecha_fin'] = receta_data['fecha_fin'].isoformat()
        if receta_data.get('hora_preferida'):
            receta_data['hora_preferida'] = str(receta_data['hora_preferida'])
        if receta_data.get('cliente_fecha_nacimiento'):
            receta_data['cliente_fecha_nacimiento'] = receta_data['cliente_fecha_nacimiento'].isoformat()

        return jsonify(receta_data)

    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener datos de receta {alerta_id}: {e}")
        return jsonify({'error': 'Error al cargar los datos de la receta.'}), 500
    finally:
        if conn:
            conn.close()


# --- API: AUDITORÍA (Solo Admin) ---
@app.route('/api/admin/auditoria', methods=['GET'])
@admin_required
def get_auditoria_logs():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        tabla_filtro = request.args.get('tabla', None)
        limit = request.args.get('limit', None)

        query = """
            SELECT
                aud.id, aud.fecha_hora, u_app.nombre as nombre_usuario_app,
                u_app.cedula as cedula_usuario_app,
                aud.usuario_db as usuario_postgres, aud.accion, aud.tabla_afectada,
                aud.registro_id_afectado, aud.datos_anteriores, aud.datos_nuevos,
                aud.detalles_adicionales
            FROM auditoria aud
            LEFT JOIN usuarios u_app ON aud.usuario_id_app = u_app.id
        """
        params = []

        if tabla_filtro:
            query += " WHERE aud.tabla_afectada = %s"
            params.append(tabla_filtro)

        query += " ORDER BY aud.fecha_hora DESC"

        if limit:
            try:
                query += " LIMIT %s"
                params.append(int(limit))
            except ValueError:
                app.logger.warn("Invalid limit parameter for auditoria endpoint.")
                pass

        cur.execute(query, tuple(params))
        logs = cur.fetchall()
        return jsonify(logs)
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener logs de auditoría: {e}")
        return jsonify({'error': 'Error al cargar los registros de auditoría.'}), 500
    finally:
        if conn:
            conn.close()

# --- API: REPORTES LOG Y UPLOAD/DOWNLOAD ---
@app.route('/api/admin/reportes_log', methods=['GET', 'POST'])
@admin_required
def manage_reportes_log():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'POST':
            data = request.json
            tipo_reporte = data.get('tipo_reporte')
            nombre_reporte = data.get('nombre_reporte')
            pdf_filename = data.get('pdf_filename')

            if not all([tipo_reporte, nombre_reporte, pdf_filename]):
                return jsonify({'error': 'Tipo, nombre del reporte y nombre del archivo PDF son requeridos.'}), 400

            try:
                cur.execute(
                    """
                    INSERT INTO reportes_log (tipo_reporte, nombre_reporte, pdf_filename, generado_por_usuario_id)
                    VALUES (%s, %s, %s, %s) RETURNING id
                    """,
                    (tipo_reporte, nombre_reporte, pdf_filename, admin_id_actual)
                )
                log_id = cur.fetchone()['id']
                conn.commit()
                return jsonify({'message': 'Generación de reporte registrada con éxito.', 'log_id': log_id}), 201
            except psycopg2.IntegrityError as e:
                conn.rollback()
                app.logger.error(f"Error de integridad al registrar log de reporte: {e}")
                return jsonify({'error': 'Error de integridad al guardar el log del reporte.'}), 409
            except psycopg2.Error as e:
                conn.rollback()
                app.logger.error(f"Error de BD al registrar generación de reporte: {e}")
                return jsonify({'error': 'Error de base de datos al registrar la generación del reporte.'}), 500

        if request.method == 'GET':
            cur.execute("""
                SELECT rl.id, rl.tipo_reporte, rl.nombre_reporte, rl.pdf_filename,
                       rl.fecha_generacion, u.nombre as generado_por_nombre
                FROM reportes_log rl
                LEFT JOIN usuarios u ON rl.generado_por_usuario_id = u.id
                ORDER BY rl.fecha_generacion DESC
                LIMIT 50
            """)
            logs = cur.fetchall()
            return jsonify(logs)

    except psycopg2.Error as e:
        app.logger.error(f"Error de conexión/BD en manage_reportes_log: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/admin/reportes/upload_pdf', methods=['POST'])
@admin_required
def upload_report_pdf():
    if 'report_pdf' not in request.files:
        return jsonify({'error': 'No se encontró el archivo PDF en la solicitud.'}), 400

    file = request.files['report_pdf']

    if file.filename == '':
        return jsonify({'error': 'No se seleccionó ningún archivo.'}), 400

    if file and allowed_file(file.filename):
        unique_id = uuid.uuid4()
        extension = secure_filename(file.filename.rsplit('.', 1)[1].lower())
        storage_filename = f"{unique_id}.{extension}"

        try:
            file.save(os.path.join(app.config['REPORTS_STORAGE_PATH'], storage_filename))
            return jsonify({'message': 'Archivo PDF subido con éxito.', 'filename': storage_filename}), 201
        except Exception as e:
            app.logger.error(f"Error al guardar el archivo PDF subido: {e}")
            return jsonify({'error': 'Error interno al guardar el archivo PDF.'}), 500
    else:
        return jsonify({'error': 'Tipo de archivo no permitido. Solo se aceptan PDFs.'}), 400

@app.route('/api/admin/reportes/download/<int:log_id>', methods=['GET'])
@admin_required
def download_report_pdf(log_id):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT pdf_filename, nombre_reporte FROM reportes_log WHERE id = %s", (log_id,))
        report_log = cur.fetchone()

        if not report_log:
            return jsonify({'error': 'Registro de reporte no encontrado.'}), 404

        pdf_filename = report_log['pdf_filename']
        base_name = report_log['nombre_reporte'].replace(' ', '_').replace('/', '-')
        timestamp_part = pdf_filename.split('.')[0][:8]
        download_name = secure_filename(f"{base_name}_{timestamp_part}.pdf")


        reports_dir = app.config['REPORTS_STORAGE_PATH']

        if not os.path.exists(os.path.join(reports_dir, pdf_filename)):
            app.logger.error(f"Archivo PDF no encontrado en el servidor: {os.path.join(reports_dir, pdf_filename)}")
            return jsonify({'error': 'Archivo PDF no encontrado en el servidor.'}), 404

        return send_from_directory(directory=reports_dir,
                                   path=pdf_filename,
                                   as_attachment=True,
                                   download_name=download_name)

    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al intentar descargar reporte {log_id}: {e}")
        return jsonify({'error': 'Error de base de datos al obtener información del reporte.'}), 500
    except Exception as e:
        app.logger.error(f"Error general al intentar descargar reporte {log_id}: {e}")
        return jsonify({'error': f'Error al procesar la descarga del reporte: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# --- NUEVOS ENDPOINTS ---

@app.route('/api/eps', methods=['GET'])
@login_required
def get_eps():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, nombre FROM eps WHERE estado = 'activo' ORDER BY nombre")
        eps_list = cur.fetchall()
        return jsonify(eps_list)
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener EPS: {e}")
        return jsonify({'error': 'Error al cargar las EPS.'}), 500
    finally:
        if conn:
            conn.close()


# --- Rutas para servir los archivos HTML ---
@app.route('/')
def index():
    if 'user_id' in session:
        if session.get('rol') == 'admin':
            return render_template('admin.html')
        elif session.get('rol') == 'cliente':
            return render_template('client.html')
    return render_template('login.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/<path:filename>')
def serve_html_or_static(filename):
    html_files = ['admin.html', 'client.html', 'login.html', 'configuracion.html']
    if filename in html_files:
        if filename != 'login.html' and 'user_id' not in session:
            return render_template('login.html')

        if filename == 'login.html' and 'user_id' in session:
            if session.get('rol') == 'admin':
                return render_template('admin.html')
            elif session.get('rol') == 'cliente':
                return render_template('client.html')

        try:
            return render_template(filename)
        except Exception as e:
            app.logger.warn(f"Template HTML no encontrado: {filename}, error: {e}")
            pass

    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        app.logger.warn(f"Archivo estático o HTML no encontrado: {filename}, error: {e}")
        return "Archivo no encontrado", 404


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    app.logger.info("Iniciando la aplicación MediAlert...")
    if not os.path.exists(INSTANCE_FOLDER_PATH):
        os.makedirs(INSTANCE_FOLDER_PATH, exist_ok=True)
    if not os.path.exists(app.config['REPORTS_STORAGE_PATH']):
        os.makedirs(app.config['REPORTS_STORAGE_PATH'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)