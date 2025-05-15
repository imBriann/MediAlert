from flask import Flask, request, jsonify
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

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
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Credenciales incorrectas'}), 401

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
