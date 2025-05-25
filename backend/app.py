from flask import Flask, request, jsonify, session
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = 'super-secret-key'  # Cambia esto por una clave segura

# Fuerza los valores explícitamente para evitar problemas de entorno/codificación
PG_HOST = 'localhost'
PG_DB = 'medialert'
PG_USER = 'postgres'
PG_PASS = '0102'
PG_PORT = '5432'

def get_db_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        port=PG_PORT
    )
    return conn

def registrar_reporte(accion, detalle):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO reportes (accion, detalle) VALUES (%s, %s)", (accion, detalle))
    conn.commit()
    cur.close()
    conn.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    cedula = data.get('cedula')
    contrasena = data.get('contrasena')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE cedula=%s AND contrasena=%s", (cedula, contrasena))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        session['logged_in'] = True
        registrar_reporte('login', f'Usuario {cedula} inició sesión')
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    registrar_reporte('logout', 'Usuario cerró sesión')
    session.clear()
    return jsonify({'success': True})

@app.route('/check_login', methods=['GET'])
def check_login():
    return jsonify({'logged_in': session.get('logged_in', False)})

# --- Medicamentos ---
@app.route('/medicamentos', methods=['GET'])
def get_medicamentos():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad FROM medicamentos ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    medicamentos = [{
        'id': r[0],
        'nombre': r[1],
        'descripcion': r[2],
        'composicion': r[3],
        'sintomas_secundarios': r[4],
        'indicaciones': r[5],
        'rango_edad': r[6]
    } for r in rows]
    return jsonify(medicamentos)

@app.route('/medicamentos', methods=['POST'])
def add_medicamento():
    data = request.json
    nombre = data.get('nombre')
    descripcion = data.get('descripcion')
    composicion = data.get('composicion')
    sintomas_secundarios = data.get('sintomas_secundarios')
    indicaciones = data.get('indicaciones')
    rango_edad = data.get('rango_edad')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO medicamentos (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
        (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad)
    )
    mid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    registrar_reporte('agregar_medicamento', f'Se agregó medicamento: {nombre}')
    return jsonify({
        'id': mid,
        'nombre': nombre,
        'descripcion': descripcion,
        'composicion': composicion,
        'sintomas_secundarios': sintomas_secundarios,
        'indicaciones': indicaciones,
        'rango_edad': rango_edad
    })

@app.route('/medicamentos/<int:mid>', methods=['DELETE'])
def delete_medicamento(mid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT nombre FROM medicamentos WHERE id=%s", (mid,))
    nombre = cur.fetchone()
    cur.execute("DELETE FROM medicamentos WHERE id=%s", (mid,))
    conn.commit()
    cur.close()
    conn.close()
    registrar_reporte('eliminar_medicamento', f'Se eliminó medicamento: {nombre[0] if nombre else mid}')
    return jsonify({'success': True})

# --- Usuarios ---
@app.route('/usuarios', methods=['GET'])
def get_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, cedula FROM usuarios ORDER BY id")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    usuarios = [{'id': r[0], 'cedula': r[1]} for r in rows]
    return jsonify(usuarios)

@app.route('/usuarios', methods=['POST'])
def add_usuario():
    data = request.json
    cedula = data.get('cedula')
    contrasena = data.get('contrasena')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO usuarios (cedula, contrasena) VALUES (%s, %s) RETURNING id", (cedula, contrasena))
    uid = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    registrar_reporte('agregar_usuario', f'Se agregó usuario: {cedula}')
    return jsonify({'id': uid, 'cedula': cedula})

@app.route('/usuarios/<int:uid>', methods=['DELETE'])
def delete_usuario(uid):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT cedula FROM usuarios WHERE id=%s", (uid,))
    cedula = cur.fetchone()
    cur.execute("DELETE FROM usuarios WHERE id=%s", (uid,))
    conn.commit()
    cur.close()
    conn.close()
    registrar_reporte('eliminar_usuario', f'Se eliminó usuario: {cedula[0] if cedula else uid}')
    return jsonify({'success': True})

# --- Reportes (ejemplo simple) ---
@app.route('/reportes', methods=['GET'])
def get_reportes():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, fecha, accion, detalle FROM reportes ORDER BY fecha DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    reportes = [{
        'id': r[0],
        'fecha': r[1].strftime('%Y-%m-%d %H:%M:%S'),
        'accion': r[2],
        'detalle': r[3]
    } for r in rows]
    return jsonify(reportes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
