from flask import Flask, request, jsonify, session, send_from_directory, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
from functools import wraps
import json

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True)
app.secret_key = 'tu-super-secreta-llave-para-sesiones' # ¡Cambia esto en producción!

# --- Conexión a la Base de Datos ---
def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="medialert",
        user="postgres",
        password="0102", # Tu contraseña
        port="5432"
    )
    return conn

# --- Decoradores de Autorización ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Se requiere autenticación'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('rol') != 'admin':
            return jsonify({'error': 'Acceso denegado. Se requiere rol de administrador'}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- Función de Auditoría ---
def registrar_auditoria(accion, tabla_afectada=None, registro_id=None, detalles=None):
    """Registra una acción en la tabla de auditoría llamando a una función de PostgreSQL."""
    admin_id = session.get('user_id')
    if not admin_id:
        # Si no hay user_id en la sesión, no se registra.
        # Podrías añadir un log aquí si quieres rastrear intentos de auditoría sin sesión.
        # print("Auditoría no registrada: user_id no encontrado en la sesión.")
        return

    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Convierte el diccionario de detalles a una cadena JSON si existe
        detalles_json = json.dumps(detalles) if detalles else None

        # Llama a la función de PostgreSQL sp_registrar_auditoria
        # psycopg2 puede llamar funciones que devuelven VOID usando SELECT
        cur.execute(
            "SELECT sp_registrar_auditoria(%s, %s, %s, %s, %s);",
            (admin_id, accion, tabla_afectada, registro_id, detalles_json)
        )
        # Alternativamente, podrías usar cur.callproc si prefieres esa sintaxis:
        # cur.callproc("sp_registrar_auditoria", (admin_id, accion, tabla_afectada, registro_id, detalles_json))
        
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error de base de datos al registrar auditoría vía SP: {e}")
        if conn:
            conn.rollback() # Importante hacer rollback en caso de error
    except Exception as e:
        print(f"Error general al registrar auditoría vía SP: {e}")
        if conn: # Asegurar rollback también para errores no específicos de psycopg2
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
    contrasena = data.get('contrasena')
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nombre, rol FROM usuarios WHERE cedula = %s AND contrasena = %s", (cedula, contrasena))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['nombre'] = user['nombre']
        session['rol'] = user['rol']
        registrar_auditoria('INICIO_SESION', detalles={'usuario': user['nombre']})
        return jsonify(user)
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    try:
        registrar_auditoria('CIERRE_SESION', detalles={'usuario': session.get('nombre')})
        session.clear()  # Limpia la sesión
        return jsonify({'message': 'Cierre de sesión exitoso'}), 200
    except Exception as e:
        return jsonify({'error': 'Error al cerrar sesión', 'details': str(e)}), 500

@app.route('/api/session_check', methods=['GET'])
@login_required
def session_check():
    return jsonify({
        'user_id': session.get('user_id'),
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    })

# --- API: GESTIÓN DE CLIENTES ---
@app.route('/api/admin/clientes', methods=['GET', 'POST'])
@admin_required
def manage_clientes():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'GET':
        cur.execute("SELECT id, nombre, cedula, email FROM usuarios WHERE rol='cliente' ORDER BY nombre")
        clientes = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(clientes)

    if request.method == 'POST':
        data = request.json
        try:
            cur.execute(
                "INSERT INTO usuarios (nombre, cedula, email, contrasena, rol) VALUES (%s, %s, %s, %s, 'cliente') RETURNING id",
                (data['nombre'], data['cedula'], data['email'], data['contrasena'])
            )
            new_id = cur.fetchone()['id']
            conn.commit()
            registrar_auditoria('CREAR_CLIENTE', 'usuarios', new_id, data)
            return jsonify({'message': 'Cliente creado', 'id': new_id}), 201
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()

@app.route('/api/admin/clientes/<int:uid>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def manage_single_cliente(uid):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if request.method == 'GET':
        cur.execute("SELECT id, nombre, cedula, email FROM usuarios WHERE id = %s AND rol='cliente'", (uid,))
        cliente = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify(cliente)
        
    if request.method == 'PUT':
        data = request.json
        try:
            cur.execute(
                "UPDATE usuarios SET nombre=%s, cedula=%s, email=%s WHERE id=%s AND rol='cliente'",
                (data['nombre'], data['cedula'], data['email'], uid)
            )
            conn.commit()
            registrar_auditoria('EDITAR_CLIENTE', 'usuarios', uid, data)
            return jsonify({'message': 'Cliente actualizado'})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()

    if request.method == 'DELETE':
        try:
            cur.execute("DELETE FROM usuarios WHERE id=%s AND rol='cliente'", (uid,))
            conn.commit()
            registrar_auditoria('ELIMINAR_CLIENTE', 'usuarios', uid)
            return jsonify({'message': 'Cliente eliminado'})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()

# --- API: GESTIÓN DE MEDICAMENTOS ---
@app.route('/api/admin/medicamentos', methods=['GET', 'POST'])
@admin_required
def manage_medicamentos():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    if request.method == 'GET':
        cur.execute("SELECT * FROM medicamentos ORDER BY nombre")
        medicamentos = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(medicamentos)
    
    if request.method == 'POST':
        data = request.json
        try:
            cur.execute(
                "INSERT INTO medicamentos (nombre, descripcion) VALUES (%s, %s) RETURNING id",
                (data['nombre'], data['descripcion'])
            )
            new_id = cur.fetchone()['id']
            conn.commit()
            registrar_auditoria('CREAR_MEDICAMENTO', 'medicamentos', new_id, data)
            return jsonify({'message': 'Medicamento creado', 'id': new_id}), 201
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()

@app.route('/api/admin/medicamentos/<int:mid>', methods=['PUT', 'DELETE'])
@admin_required
def manage_single_medicamento(mid):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        try:
            cur.execute(
                "UPDATE medicamentos SET nombre=%s, descripcion=%s WHERE id=%s",
                (data['nombre'], data['descripcion'], mid)
            )
            conn.commit()
            registrar_auditoria('EDITAR_MEDICAMENTO', 'medicamentos', mid, data)
            return jsonify({'message': 'Medicamento actualizado'})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()

    if request.method == 'DELETE':
        try:
            # Primero, elimina las alertas asociadas para evitar errores de clave foránea
            cur.execute("DELETE FROM alertas WHERE medicamento_id=%s", (mid,))
            cur.execute("DELETE FROM medicamentos WHERE id=%s", (mid,))
            conn.commit()
            registrar_auditoria('ELIMINAR_MEDICAMENTO', 'medicamentos', mid)
            return jsonify({'message': 'Medicamento y sus alertas asociadas eliminados'})
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            cur.close()
            conn.close()

# --- API: GESTIÓN DE ALERTAS ---
@app.route('/api/admin/alertas', methods=['GET'])
@admin_required
def get_alertas():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.id, u.nombre as cliente_nombre, m.nombre as medicamento_nombre, a.dosis, a.frecuencia, a.estado
        FROM alertas a
        JOIN usuarios u ON a.usuario_id = u.id
        JOIN medicamentos m ON a.medicamento_id = m.id
        ORDER BY u.nombre, m.nombre
    """)
    alertas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(alertas)
# (Las rutas POST, PUT, DELETE para alertas seguirían una lógica similar)


# --- API: AUDITORÍA ---
@app.route('/api/admin/auditoria', methods=['GET'])
@admin_required
def get_auditoria():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.id, u.nombre as admin_nombre, a.accion, a.tabla_afectada, a.registro_id, a.detalles, a.fecha_hora
        FROM auditoria a
        JOIN usuarios u ON a.usuario_id = u.id
        ORDER BY a.fecha_hora DESC
    """)
    logs = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(logs)


# --- Rutas para servir los archivos HTML ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204  # Responde con un estado 204 (sin contenido) para evitar errores.

@app.route('/<path:path>')
def serve_static(path):
    # Si el archivo solicitado no existe, devuelve un error 404.
    try:
        if path in ['admin.html', 'client.html'] and 'user_id' not in session:
            return render_template('login.html')
        return render_template(path)
    except Exception:
        return "Archivo no encontrado", 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)