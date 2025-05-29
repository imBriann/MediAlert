from flask import Flask, request, jsonify, session, send_from_directory, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
from functools import wraps

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
        return jsonify(user)
    
    return jsonify({'error': 'Credenciales inválidas'}), 401

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({'message': 'Cierre de sesión exitoso'})

@app.route('/api/session_check', methods=['GET'])
@login_required
def session_check():
    return jsonify({
        'user_id': session.get('user_id'),
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    })

# --- Rutas de la API para Administradores ---

@app.route('/api/admin/clientes', methods=['GET', 'POST'])
@admin_required
def manage_clientes():
    # Esta ruta ya está implementada
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
        cur.execute("INSERT INTO usuarios (nombre, cedula, email, contrasena, rol) VALUES (%s, %s, %s, %s, 'cliente') RETURNING id",
                    (data['nombre'], data['cedula'], data['email'], data['contrasena']))
        new_id = cur.fetchone()['id']
        conn.commit()
        # Aquí registrarías la auditoría
        cur.close()
        conn.close()
        return jsonify({'message': 'Cliente creado', 'id': new_id}), 201


@app.route('/api/admin/clientes/<int:uid>', methods=['PUT', 'DELETE'])
@admin_required
def manage_single_cliente(uid):
    # Esta ruta ya está implementada
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'PUT':
        data = request.json
        cur.execute("UPDATE usuarios SET nombre=%s, cedula=%s, email=%s WHERE id=%s AND rol='cliente'",
                    (data['nombre'], data['cedula'], data['email'], uid))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Cliente actualizado'})

    if request.method == 'DELETE':
        cur.execute("DELETE FROM usuarios WHERE id=%s AND rol='cliente'", (uid,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Cliente eliminado'})

# --- ¡NUEVAS RUTAS AÑADIDAS PARA EVITAR EL ERROR! ---

@app.route('/api/admin/medicamentos', methods=['GET'])
@admin_required
def get_medicamentos():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM medicamentos ORDER BY nombre")
    medicamentos = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(medicamentos)

@app.route('/api/admin/alertas', methods=['GET'])
@admin_required
def get_alertas():
    # Por ahora, devolvemos una lista vacía para que no de error
    return jsonify([])

@app.route('/api/admin/auditoria', methods=['GET'])
@admin_required
def get_auditoria():
    # Por ahora, devolvemos una lista vacía para que no de error
    return jsonify([])

# ... (todo tu código anterior de app.py va aquí) ...

# --- ¡NUEVO ENDPOINT PARA CONFIGURACIÓN! ---
@app.route('/api/admin/perfil/password', methods=['PUT'])
@admin_required
def update_admin_password():
    """Permite al admin logueado cambiar su propia contraseña."""
    data = request.json
    new_password = data.get('contrasena')

    if not new_password:
        return jsonify({'error': 'No se proporcionó una nueva contraseña'}), 400

    admin_id = session['user_id']
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE usuarios SET contrasena = %s WHERE id = %s", (new_password, admin_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

    return jsonify({'message': 'Contraseña actualizada con éxito'})

# ... (El resto de tu código de app.py va aquí) ...


# --- Rutas de la API para Clientes ---

@app.route('/api/cliente/mis_alertas', methods=['GET'])
@login_required
def get_mis_alertas():
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.id, m.nombre as medicamento, a.dosis, a.frecuencia, a.estado
        FROM alertas a
        JOIN medicamentos m ON a.medicamento_id = m.id
        WHERE a.usuario_id = %s
    """, (user_id,))
    alertas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(alertas)


# --- Rutas para servir los archivos HTML ---
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/<path:path>')
def serve_static(path):
    if path in ['admin.html', 'client.html'] and 'user_id' not in session:
        return render_template('login.html')
    return render_template(path)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)