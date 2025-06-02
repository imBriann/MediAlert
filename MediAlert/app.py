from flask import Flask, request, jsonify, session, send_from_directory, render_template
import psycopg2
from psycopg2.extras import RealDictCursor, Json # Para manejar JSONB
from flask_cors import CORS
from functools import wraps
import json
from werkzeug.security import generate_password_hash, check_password_hash # Para contraseñas
import os
import logging
from dotenv import load_dotenv
from datetime import date, time  # Importar date y time
import uuid  # Para generar nombres únicos
from werkzeug.utils import secure_filename  # Para asegurar nombres de archivo

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}}) # Ajusta origins según necesidad
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
    os.makedirs(REPORTS_STORAGE_PATH)

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
        # Intentar establecer el app_user_id para la auditoría a nivel de BD
        if 'user_id' in session:
            with conn.cursor() as cur:
                # Usar set_config con is_local = true para que dure solo la transacción/sesión actual
                cur.execute("SELECT set_config('medialert.app_user_id', %s, true);", (str(session['user_id']),))
        return conn
    except psycopg2.Error as e:
        app.logger.error(f"Error al conectar con la base de datos: {e}")
        raise # Relanzar la excepción para que sea manejada más arriba si es necesario

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
    def serialize_dates(obj):
        """Recursively convert date objects to strings in a dictionary."""
        if isinstance(obj, dict):
            return {k: serialize_dates(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [serialize_dates(i) for i in obj]
        elif isinstance(obj, (date, time)):
            return obj.isoformat()
        return obj

    app_user_id = session.get('user_id')  # Puede ser None si la acción no está ligada a una sesión de usuario

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Convertir diccionarios de Python a objetos Json para psycopg2
        # Esto asegura que se manejen correctamente como JSONB en PostgreSQL
        p_datos_anteriores = Json(serialize_dates(datos_anteriores)) if datos_anteriores is not None else None
        p_datos_nuevos = Json(serialize_dates(datos_nuevos)) if datos_nuevos is not None else None
        p_detalles_adicionales = Json(serialize_dates(detalles_adicionales)) if detalles_adicionales is not None else None

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
        # Solo seleccionar usuarios activos
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
@login_required # Asegura que solo usuarios logueados puedan hacer logout
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
    # El decorador @login_required ya maneja si no hay sesión.
    return jsonify({
        'user_id': session.get('user_id'),
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    })

# --- API: GESTIÓN DE CLIENTES (Usuarios con rol 'cliente') ---
# Snippet from MediAlert/app.py

@app.route('/api/admin/clientes', methods=['GET', 'POST']) # Path remains for client management, but GET can be more versatile
@admin_required
def manage_clientes():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            estado_filtro = request.args.get('estado', None) # Allow no default to fetch all if not specified
            rol_filtro = request.args.get('rol', None) # Allow fetching specific roles or all

            query_parts = ["SELECT id, nombre, cedula, email, rol, estado_usuario FROM usuarios"]
            conditions = []
            params = []

            if rol_filtro:
                if rol_filtro == 'cliente':
                    conditions.append("rol = 'cliente'")
                elif rol_filtro == 'admin':
                    conditions.append("rol = 'admin'")
                # Not adding rol_filtro to params as it's directly in query string for safety
            
            if estado_filtro:
                if estado_filtro != 'todos': # 'todos' means no estado filter
                    conditions.append("estado_usuario = %s")
                    params.append(estado_filtro)
            
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))
            
            query_parts.append("ORDER BY rol, nombre")
            
            final_query = " ".join(query_parts)
            cur.execute(final_query, tuple(params))
            users = cur.fetchall()
            return jsonify(users)

        if request.method == 'POST': # This part remains specific to creating 'cliente' role users
            data = request.json
            nombre = data.get('nombre')
            cedula = data.get('cedula')
            email = data.get('email')
            contrasena_plain = data.get('contrasena')
            rol_nuevo_usuario = 'cliente'  # Hardcoded for this POST through /api/admin/clientes
            estado_nuevo_usuario = 'activo'

            if not all([nombre, cedula, email, contrasena_plain]):
                return jsonify({'error': 'Nombre, cédula, email y contraseña son requeridos.'}), 400

            hashed_password = generate_password_hash(contrasena_plain)
            
            try:
                cur.execute(
                    """
                    INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario) 
                    VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (nombre, cedula, email, hashed_password, rol_nuevo_usuario, estado_nuevo_usuario)
                )
                new_id = cur.fetchone()['id']
                conn.commit()
                
                # The audit trigger in the DB handles the direct INSERT.
                # Application level audit might be more specific.
                registrar_auditoria_aplicacion( #
                    'CREACION_CLIENTE', 
                    tabla_afectada='usuarios', 
                    registro_id=str(new_id),
                    datos_nuevos={'nombre': nombre, 'cedula': cedula, 'email': email, 'rol': rol_nuevo_usuario, 'estado_usuario': estado_nuevo_usuario},
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


@app.route('/api/admin/clientes/<int:uid>', methods=['GET', 'PUT']) # DELETE se maneja con cambio de estado
@admin_required
def manage_single_cliente(uid):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        admin_id_actual = session.get('user_id')

        if request.method == 'GET':
            cur.execute("SELECT id, nombre, cedula, email, estado_usuario FROM usuarios WHERE id = %s AND rol='cliente'", (uid,))
            cliente = cur.fetchone()
            if not cliente:
                return jsonify({'error': 'Cliente no encontrado.'}), 404
            return jsonify(cliente)
            
        if request.method == 'PUT': # Para editar datos o para "eliminar" (cambiar estado)
            data = request.json
            
            # Obtener datos actuales para auditoría
            cur.execute("SELECT * FROM usuarios WHERE id = %s AND rol='cliente'", (uid,))
            old_cliente_data = cur.fetchone()
            if not old_cliente_data:
                return jsonify({'error': 'Cliente no encontrado para actualizar.'}), 404

            nombre = data.get('nombre', old_cliente_data['nombre'])
            cedula = data.get('cedula', old_cliente_data['cedula'])
            email = data.get('email', old_cliente_data['email'])
            estado_usuario = data.get('estado_usuario', old_cliente_data['estado_usuario']) # Para soft delete

            if estado_usuario not in ['activo', 'inactivo']:
                return jsonify({'error': 'Valor de estado_usuario no válido.'}), 400
            
            # Si se provee una nueva contraseña, hashearla. Si no, no se actualiza.
            new_password_plain = data.get('contrasena_nueva')
            sql_update = "UPDATE usuarios SET nombre=%s, cedula=%s, email=%s, estado_usuario=%s"
            params = [nombre, cedula, email, estado_usuario]
            
            if new_password_plain:
                hashed_new_password = generate_password_hash(new_password_plain)
                sql_update += ", contrasena=%s"
                params.append(hashed_new_password)
            
            sql_update += " WHERE id=%s AND rol='cliente'"
            params.append(uid)

            try:
                cur.execute(sql_update, tuple(params))
                conn.commit()
                
                # Auditoría de aplicación. El trigger de BD también registrará el UPDATE.
                accion_audit = 'EDICION_CLIENTE'
                if old_cliente_data['estado_usuario'] == 'activo' and estado_usuario == 'inactivo':
                    accion_audit = 'DESACTIVACION_CLIENTE'
                elif old_cliente_data['estado_usuario'] == 'inactivo' and estado_usuario == 'activo':
                     accion_audit = 'REACTIVACION_CLIENTE'

                registrar_auditoria_aplicacion(
                    accion_audit, 
                    tabla_afectada='usuarios', 
                    registro_id=str(uid),
                    datos_anteriores=dict(old_cliente_data), # Convertir RealDictRow a dict
                    datos_nuevos={'nombre': nombre, 'cedula': cedula, 'email': email, 'estado_usuario': estado_usuario},
                    detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': f'Cliente {uid} actualizado con éxito.'})
            except psycopg2.IntegrityError as e:
                conn.rollback()
                # Manejar errores de unicidad para cédula y email
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
            # Extraer todos los campos
            nombre = data.get('nombre')
            descripcion = data.get('descripcion')
            composicion = data.get('composicion')
            sintomas_secundarios = data.get('sintomas_secundarios')
            indicaciones = data.get('indicaciones')
            rango_edad = data.get('rango_edad')
            # estado_medicamento por defecto es 'disponible' en la BD

            if not nombre: # Nombre es el campo más crítico
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
                    datos_nuevos=data, # Enviar todos los datos recibidos
                    detalles_adicionales={'creado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': 'Medicamento creado con éxito.', 'id': new_id}), 201
            except psycopg2.IntegrityError as e: # Nombre duplicado
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

@app.route('/api/admin/medicamentos/<int:mid>', methods=['GET','PUT']) # DELETE se maneja con cambio de estado
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

            # Actualizar todos los campos si se proveen
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
                    datos_nuevos=data, # Enviar todos los datos recibidos para la actualización
                    detalles_adicionales={'actualizado_por_admin_id': admin_id_actual}
                )
                return jsonify({'message': f'Medicamento {mid} actualizado con éxito.'})
            except psycopg2.IntegrityError as e: # Nombre duplicado
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
            # Mostrar todas las alertas, indicando estado de usuario y medicamento
            cur.execute("""
                SELECT 
                    a.id, a.usuario_id, u.nombre as cliente_nombre, u.estado_usuario,
                    a.medicamento_id, m.nombre as medicamento_nombre, m.estado_medicamento,
                    a.dosis, a.frecuencia, a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado as estado_alerta
                FROM alertas a
                JOIN usuarios u ON a.usuario_id = u.id
                JOIN medicamentos m ON a.medicamento_id = m.id
                ORDER BY u.nombre, m.nombre, a.fecha_inicio
            """)
            alertas = cur.fetchall()

            # Convertir objetos de tipo `time` a cadenas
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

            # Verificar que el usuario sea cliente y esté activo
            cur.execute("SELECT estado_usuario FROM usuarios WHERE id = %s AND rol = 'cliente'", (usuario_id,))
            user_check = cur.fetchone()
            if not user_check or user_check['estado_usuario'] != 'activo':
                return jsonify({'error': 'El usuario seleccionado no es un cliente activo.'}), 400
            
            # Verificar que el medicamento esté disponible
            cur.execute("SELECT estado_medicamento FROM medicamentos WHERE id = %s", (medicamento_id,))
            med_check = cur.fetchone()
            if not med_check or med_check['estado_medicamento'] != 'disponible':
                return jsonify({'error': 'El medicamento seleccionado no está disponible.'}), 400

            dosis = data.get('dosis')
            frecuencia = data.get('frecuencia')
            fecha_fin = data.get('fecha_fin') if data.get('fecha_fin') else None
            hora_preferida = data.get('hora_preferida') if data.get('hora_preferida') else None
            estado_alerta = data.get('estado', 'activa') # Por defecto 'activa'

            if estado_alerta not in ['activa', 'inactiva', 'completada', 'fallida']:
                return jsonify({'error': 'Valor de estado de alerta no válido.'}), 400

            try:
                cur.execute(
                    """
                    INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """,
                    (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado_alerta)
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

            # Convertir objetos de tipo `time` a cadenas
            if isinstance(alerta.get('hora_preferida'), (time,)):
                alerta['hora_preferida'] = alerta['hora_preferida'].strftime('%H:%M:%S')

            return jsonify(alerta)

        if request.method == 'PUT':
            data = request.json
            cur.execute("SELECT * FROM alertas WHERE id = %s", (alerta_id,))
            old_alerta_data = cur.fetchone()
            if not old_alerta_data:
                return jsonify({'error': 'Alerta no encontrada para actualizar.'}), 404

            # Validar campos como en la creación
            usuario_id = data.get('usuario_id', old_alerta_data['usuario_id'])
            medicamento_id = data.get('medicamento_id', old_alerta_data['medicamento_id'])
            
            # Verificar usuario y medicamento si cambian o si se actualiza una alerta inactiva
            # (Podría ser más complejo si se permite cambiar usuario/medicamento de una alerta)
            # Por simplicidad, asumimos que usuario_id y medicamento_id no cambian frecuentemente en un PUT,
            # o que si cambian, la validación de activo/disponible es importante.

            dosis = data.get('dosis', old_alerta_data['dosis'])
            frecuencia = data.get('frecuencia', old_alerta_data['frecuencia'])
            fecha_inicio = data.get('fecha_inicio', old_alerta_data['fecha_inicio'])
            fecha_fin = data.get('fecha_fin', old_alerta_data['fecha_fin'])
            if fecha_fin == '': fecha_fin = None # Tratar string vacío como NULL
            hora_preferida = data.get('hora_preferida', old_alerta_data['hora_preferida'])
            if hora_preferida == '': hora_preferida = None
            estado = data.get('estado', old_alerta_data['estado'])

            if estado not in ['activa', 'inactiva', 'completada', 'fallida']:
                return jsonify({'error': 'Valor de estado de alerta no válido.'}), 400
            
            try:
                cur.execute(
                    """
                    UPDATE alertas SET usuario_id=%s, medicamento_id=%s, dosis=%s, frecuencia=%s, 
                    fecha_inicio=%s, fecha_fin=%s, hora_preferida=%s, estado=%s 
                    WHERE id=%s
                    """,
                    (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, alerta_id)
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

        if request.method == 'DELETE': # Borrado físico de alertas permitido
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
@login_required # Solo usuarios logueados
def get_mis_alertas_cliente():
    if session.get('rol') != 'cliente':
        return jsonify({'error': 'Acceso denegado. Esta vista es solo para clientes.'}), 403
    
    cliente_id = session['user_id']
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # Mostrar solo alertas activas para el cliente, de medicamentos disponibles
        # y donde el propio cliente esté activo (aunque el login ya lo filtraría)
        cur.execute("""
            SELECT 
                a.id, m.nombre as medicamento_nombre, a.dosis, a.frecuencia, 
                a.fecha_inicio, a.fecha_fin, a.hora_preferida, a.estado
            FROM alertas a
            JOIN medicamentos m ON a.medicamento_id = m.id
            JOIN usuarios u ON a.usuario_id = u.id
            WHERE a.usuario_id = %s 
              AND a.estado = 'activa'
              AND m.estado_medicamento = 'disponible'
              AND u.estado_usuario = 'activo'
            ORDER BY a.fecha_inicio, a.hora_preferida
        """, (cliente_id,))
        alertas = cur.fetchall()
        return jsonify(alertas)
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener mis_alertas para cliente {cliente_id}: {e}")
        return jsonify({'error': 'Error al cargar tus alertas.'}), 500
    finally:
        if conn:
            conn.close()


# --- API: AUDITORÍA (Solo Admin) ---
# You might also want a limit parameter for the auditoria endpoint for PDF generation:
@app.route('/api/admin/auditoria', methods=['GET'])
@admin_required
def get_auditoria_logs():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        tabla_filtro = request.args.get('tabla', None)
        limit = request.args.get('limit', None) # New limit parameter

        query = """
            SELECT 
                aud.id, 
                aud.fecha_hora,
                u_app.nombre as nombre_usuario_app,
                aud.usuario_db as usuario_postgres,
                aud.accion, 
                aud.tabla_afectada, 
                aud.registro_id_afectado,
                aud.datos_anteriores, 
                aud.datos_nuevos, 
                aud.detalles_adicionales
            FROM auditoria aud
            LEFT JOIN usuarios u_app ON aud.usuario_id_app = u_app.id
        """ #
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
                pass # Ignore invalid limit

        cur.execute(query, tuple(params))
        logs = cur.fetchall()
        return jsonify(logs)
    except psycopg2.Error as e:
        app.logger.error(f"Error de BD al obtener logs de auditoría: {e}")
        return jsonify({'error': 'Error al cargar los registros de auditoría.'}), 500
    finally:
        if conn:
            conn.close()
            
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
        download_name = secure_filename(f"{report_log['nombre_reporte'].replace(' ', '_')}_{pdf_filename[:8]}.pdf")

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

# --- Rutas para servir los archivos HTML ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/<path:filename>')
def serve_html_or_static(filename):
    # Servir archivos HTML específicos desde la raíz de templates
    if filename in ['admin.html', 'client.html', 'login.html', 'configuracion.html']: # Añade otros HTML raíz aquí
        # Verificar sesión para páginas protegidas
        if filename in ['admin.html', 'client.html', 'configuracion.html'] and 'user_id' not in session:
            return render_template('login.html') # Redirigir a login si no hay sesión
        try:
            return render_template(filename)
        except Exception as e: # jinja2.exceptions.TemplateNotFound
            app.logger.warn(f"Template HTML no encontrado: {filename}, error: {e}")
            # Podrías intentar servir desde static si no es un template conocido
            # o simplemente devolver 404.
            pass # Dejar que intente servir desde static
    
    # Intentar servir como archivo estático (CSS, JS, IMG)
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e: # werkzeug.exceptions.NotFound
        app.logger.warn(f"Archivo estático o HTML no encontrado: {filename}, error: {e}")
        return "Archivo no encontrado", 404


if __name__ == '__main__':
    # Configurar logging básico
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    app.logger.info("Iniciando la aplicación MediAlert...")
    if not os.path.exists(INSTANCE_FOLDER_PATH):
        os.makedirs(INSTANCE_FOLDER_PATH)
    if not os.path.exists(app.config['REPORTS_STORAGE_PATH']):
        os.makedirs(app.config['REPORTS_STORAGE_PATH'])
    app.run(debug=True, host='0.0.0.0', port=5000)

