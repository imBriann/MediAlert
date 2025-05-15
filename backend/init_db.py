import psycopg2
import os

# Fuerza los valores explícitamente para descartar problemas de entorno
PG_HOST = 'localhost'
PG_DB = 'medialert'
PG_USER = 'postgres'
PG_PASS = '0102'
PG_PORT = '5432'

def print_bytes(label, value):
    print(f"{label}: {value} -> {list(value.encode('utf-8', errors='replace'))}")

print("Conectando a PostgreSQL con:")
print_bytes("  HOST", PG_HOST)
print_bytes("  DB", PG_DB)
print_bytes("  USER", PG_USER)
print_bytes("  PASS", PG_PASS)
print_bytes("  PORT", PG_PORT)

try:
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        port=PG_PORT
    )
    # Test: muestra el encoding real de la conexión y la base de datos
    cur = conn.cursor()
    cur.execute("SHOW server_encoding;")
    print("server_encoding:", cur.fetchone())
    cur.execute("SHOW client_encoding;")
    print("client_encoding:", cur.fetchone())
    cur.close()
except Exception as e:
    print("Error al conectar a PostgreSQL:")
    print(e)
    os._exit(1)

conn.set_client_encoding('UTF8')
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    cedula VARCHAR(50) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL
)
''')
# Usuario de prueba: cedula=123456, contrasena=admin
cur.execute("INSERT INTO usuarios (cedula, contrasena) VALUES (%s, %s) ON CONFLICT (cedula) DO NOTHING", ('123456', 'admin'))
conn.commit()
cur.close()
conn.close()
print(f"Base de datos PostgreSQL inicializada con usuario de prueba.")
