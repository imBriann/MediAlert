from flask import Flask, request, jsonify, session, send_from_directory, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_cors import CORS
from functools import wraps
import json

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')
CORS(app, supports_credentials=True)
app.secret_key = 'M3di$al3rt_S3cr3t'

# --- Conexión a la Base de Datos ---
def get_db_connection():
    """Establece y devuelve una conexión a la base de datos PostgreSQL."""
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
    """Verifica si el usuario ha iniciado sesión antes de acceder a la ruta."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Se requiere autenticación'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Verifica si el usuario tiene rol de administrador antes de acceder a la ruta."""
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
    """Inicia sesión del usuario verificando sus credenciales."""
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
    """Cierra la sesión del usuario actual."""
    try:
        registrar_auditoria('CIERRE_SESION', detalles={'usuario': session.get('nombre')})
        session.clear()  # Limpia la sesión
        return jsonify({'message': 'Cierre de sesión exitoso'}), 200
    except Exception as e:
        return jsonify({'error': 'Error al cerrar sesión', 'details': str(e)}), 500

@app.route('/api/session_check', methods=['GET'])
@login_required
def session_check():
    """Verifica si la sesión del usuario está activa y devuelve los detalles."""
    return jsonify({
        'user_id': session.get('user_id'),
        'nombre': session.get('nombre'),
        'rol': session.get('rol')
    })

# --- API: GESTIÓN DE CLIENTES ---
@app.route('/api/admin/clientes', methods=['GET', 'POST'])
@admin_required
def manage_clientes():
    """Gestiona la lista de clientes (listar o crear nuevos clientes)."""
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
    """Gestiona un cliente específico (obtener, actualizar o eliminar)."""
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
    """Gestiona la lista de medicamentos (listar o crear nuevos medicamentos)."""
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
    """Gestiona un medicamento específico (actualizar o eliminar)."""
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
def get_alertas_admin():
    """Lista todas las alertas existentes para los administradores."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT a.id, u.nombre as cliente_nombre, m.nombre as medicamento_nombre, 
               a.dosis, a.frecuencia, a.estado, a.fecha_inicio, a.fecha_fin
        FROM alertas a
        JOIN usuarios u ON a.usuario_id = u.id
        JOIN medicamentos m ON a.medicamento_id = m.id
        ORDER BY u.nombre, m.nombre
    """)
    alertas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(alertas)

@app.route('/api/admin/alertas', methods=['POST'])
@admin_required
def create_alerta_admin():
    """Crea una nueva alerta para un cliente y un medicamento específico."""
    data = request.json
    conn = None # Asegurar que conn esté definida para el bloque finally
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        required_fields = ['usuario_id', 'medicamento_id', 'fecha_inicio']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'El campo {field} es obligatorio.'}), 400

        fecha_fin = data.get('fecha_fin') if data.get('fecha_fin') else None # Puede ser None
        dosis = data.get('dosis', '') # Default a string vacío si no se provee
        frecuencia = data.get('frecuencia', '') # Default a string vacío

        cur.execute(
            """
            INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'activa') RETURNING id
            """,
            (data['usuario_id'], data['medicamento_id'], dosis, frecuencia, data['fecha_inicio'], fecha_fin)
        )
        new_id = cur.fetchone()['id']
        
        # Para la auditoría, obtener nombres para mejor legibilidad
        cur.execute("SELECT nombre FROM usuarios WHERE id = %s", (data['usuario_id'],))
        cliente_nombre_res = cur.fetchone()
        cliente_nombre = cliente_nombre_res['nombre'] if cliente_nombre_res else 'Desconocido'

        cur.execute("SELECT nombre FROM medicamentos WHERE id = %s", (data['medicamento_id'],))
        medicamento_nombre_res = cur.fetchone()
        medicamento_nombre = medicamento_nombre_res['nombre'] if medicamento_nombre_res else 'Desconocido'
        
        conn.commit() # Commit después de todas las lecturas para la auditoría

        audit_details = {
            'alerta_id': new_id,
            'cliente': f"{cliente_nombre} (ID: {data['usuario_id']})",
            'medicamento': f"{medicamento_nombre} (ID: {data['medicamento_id']})",
            'dosis': dosis,
            'frecuencia': frecuencia,
            'fecha_inicio': data['fecha_inicio'],
            'fecha_fin': fecha_fin if fecha_fin else "N/A"
        }
        registrar_auditoria('CREAR_ALERTA', 'alertas', new_id, audit_details)
        
        return jsonify({'message': 'Alerta creada con éxito.', 'id': new_id}), 201

    except psycopg2.Error as db_err:
        if conn:
            conn.rollback()
        pgcode = getattr(db_err, 'pgcode', '')
        if pgcode == '23503': # foreign_key_violation
            if 'alertas_usuario_id_fkey' in str(db_err):
                 return jsonify({'error': 'El ID de cliente proporcionado no existe.'}), 400
            if 'alertas_medicamento_id_fkey' in str(db_err):
                 return jsonify({'error': 'El ID de medicamento proporcionado no existe.'}), 400
        print(f"Error de base de datos al crear alerta: {db_err}")
        return jsonify({'error': f'Error de base de datos al crear la alerta.'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error general al crear alerta: {e}")
        return jsonify({'error': 'Ocurrió un error inesperado al crear la alerta.'}), 500
    finally:
        if 'cur' in locals() and cur is not None: # Verificar si cur fue inicializado
            cur.close()
        if conn is not None:
            conn.close()
            
@app.route('/api/admin/alertas/<int:alerta_id>', methods=['GET'])
@admin_required
def get_single_alerta_admin(alerta_id):
    """Obtiene los detalles de una alerta específica."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, estado FROM alertas WHERE id = %s", (alerta_id,))
        alerta = cur.fetchone()
        if alerta:
            return jsonify(alerta)
        return jsonify({'error': 'Alerta no encontrada'}), 404
    except Exception as e:
        print(f"Error al obtener alerta individual: {e}")
        return jsonify({'error': 'Error interno al obtener la alerta'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/api/admin/alertas/<int:alerta_id>', methods=['PUT'])
@admin_required
def update_alerta_admin(alerta_id):
    """Actualiza los detalles de una alerta específica."""
    data = request.json
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        required_fields = ['usuario_id', 'medicamento_id', 'fecha_inicio', 'estado']
        for field in required_fields:
            if field not in data or data[field] is None: # Permite string vacío pero no None para campos que podrían ser opcionales si no fueran 'required'
                return jsonify({'error': f'El campo {field} es obligatorio.'}), 400
        
        if not data['estado'] in ['activa', 'inactiva', 'completada']:
             return jsonify({'error': 'Valor de estado no válido.'}), 400

        fecha_fin = data.get('fecha_fin') if data.get('fecha_fin') else None
        dosis = data.get('dosis', '')
        frecuencia = data.get('frecuencia', '')
        
        cur.execute(
            """
            UPDATE alertas 
            SET usuario_id = %s, medicamento_id = %s, dosis = %s, frecuencia = %s, 
                fecha_inicio = %s, fecha_fin = %s, estado = %s
            WHERE id = %s
            """,
            (data['usuario_id'], data['medicamento_id'], dosis, frecuencia, 
             data['fecha_inicio'], fecha_fin, data['estado'], alerta_id)
        )
        
        if cur.rowcount == 0:
            conn.rollback() # Si no se actualizó ninguna fila, podría no existir
            return jsonify({'error': 'Alerta no encontrada para actualizar.'}), 404

        # Para la auditoría
        cur.execute("SELECT nombre FROM usuarios WHERE id = %s", (data['usuario_id'],))
        cliente_nombre_res = cur.fetchone()
        cliente_nombre = cliente_nombre_res['nombre'] if cliente_nombre_res else 'Desconocido'

        cur.execute("SELECT nombre FROM medicamentos WHERE id = %s", (data['medicamento_id'],))
        medicamento_nombre_res = cur.fetchone()
        medicamento_nombre = medicamento_nombre_res['nombre'] if medicamento_nombre_res else 'Desconocido'
        
        conn.commit()

        audit_details = {
            'alerta_id': alerta_id,
            'modificaciones': {
                'cliente': f"{cliente_nombre} (ID: {data['usuario_id']})",
                'medicamento': f"{medicamento_nombre} (ID: {data['medicamento_id']})",
                'dosis': dosis,
                'frecuencia': frecuencia,
                'fecha_inicio': data['fecha_inicio'],
                'fecha_fin': fecha_fin if fecha_fin else "N/A",
                'estado': data['estado']
            }
        }
        registrar_auditoria('EDITAR_ALERTA', 'alertas', alerta_id, audit_details)
        
        return jsonify({'message': 'Alerta actualizada con éxito.'}), 200

    except psycopg2.Error as db_err:
        if conn: conn.rollback()
        pgcode = getattr(db_err, 'pgcode', '')
        if pgcode == '23503': # foreign_key_violation
            return jsonify({'error': 'ID de cliente o medicamento no válido al actualizar.'}), 400
        print(f"Error de BD al actualizar alerta: {db_err}")
        return jsonify({'error': 'Error de base de datos al actualizar la alerta.'}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error general al actualizar alerta: {e}")
        return jsonify({'error': 'Error inesperado al actualizar la alerta.'}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()

@app.route('/api/admin/alertas/<int:alerta_id>', methods=['DELETE'])
@admin_required
def delete_alerta_admin(alerta_id):
    """Elimina una alerta específica."""
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Opcional: Obtener detalles para auditoría antes de borrar
        cur.execute("""
            SELECT u.nombre as cliente_nombre, m.nombre as medicamento_nombre, a.dosis 
            FROM alertas a
            LEFT JOIN usuarios u ON a.usuario_id = u.id
            LEFT JOIN medicamentos m ON a.medicamento_id = m.id
            WHERE a.id = %s
        """, (alerta_id,))
        audit_data = cur.fetchone()

        cur.execute("DELETE FROM alertas WHERE id = %s", (alerta_id,))
        
        if cur.rowcount == 0:
            conn.rollback()
            return jsonify({'error': 'Alerta no encontrada para eliminar.'}), 404
        
        conn.commit()

        audit_details = {'alerta_id_eliminada': alerta_id}
        if audit_data:
            audit_details.update({
                'cliente_anterior': audit_data.get('cliente_nombre', 'N/A'),
                'medicamento_anterior': audit_data.get('medicamento_nombre', 'N/A'),
                'dosis_anterior': audit_data.get('dosis', 'N/A')
            })
        registrar_auditoria('ELIMINAR_ALERTA', 'alertas', alerta_id, audit_details)
        
        return jsonify({'message': 'Alerta eliminada con éxito.'}), 200
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error al eliminar alerta: {e}")
        return jsonify({'error': 'Error inesperado al eliminar la alerta.'}), 500
    finally:
        if cur: cur.close()
        if conn: conn.close()


# --- API: AUDITORÍA ---
@app.route('/api/admin/auditoria', methods=['GET'])
@admin_required
def get_auditoria():
    """Devuelve el registro de auditoría para los administradores."""
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
    """Sirve la página principal de inicio de sesión."""
    return render_template('login.html')

@app.route('/favicon.ico')
def favicon():
    """Responde con un estado 204 para solicitudes de favicon."""
    return '', 204  # Responde con un estado 204 (sin contenido) para evitar errores.

@app.route('/<path:path>')
def serve_static(path):
    """Sirve archivos estáticos o devuelve un error 404 si no se encuentran."""
    # Si el archivo solicitado no existe, devuelve un error 404.
    try:
        if path in ['admin.html', 'client.html'] and 'user_id' not in session:
            return render_template('login.html')
        return render_template(path)
    except Exception:
        return "Archivo no encontrado", 404


if __name__ == '__main__':
    """Inicia la aplicación Flask en modo de depuración."""
    app.run(debug=True, host='0.0.0.0', port=5000)