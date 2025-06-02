# backend/insert_admin_user.py
import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de la Conexión a la Base de Datos (igual que en init_db.py y app.py) ---
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_DB = os.getenv('PG_DB', 'medialert')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASS = os.getenv('PG_PASS', '0102')  # ¡Usa tu contraseña real o una variable de entorno!
PG_PORT = os.getenv('PG_PORT', '5432')

# --- Detalles del Administrador a Insertar ---
ADMIN_NOMBRE = "Admin Script"
ADMIN_CEDULA = "admin999"  # Asegúrate de que esta cédula sea única
ADMIN_EMAIL = "adminscript@medialert.co"  # Asegúrate de que este email sea único
ADMIN_CONTRASENA_PLAIN = "1234"
ADMIN_ROL = "admin"
ADMIN_ESTADO = "activo"

def insertar_admin():
    conn = None
    cur = None
    try:
        print(f"Conectando a la base de datos PostgreSQL (Host: {PG_HOST}, DB: {PG_DB})...")
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT
        )
        conn.set_client_encoding('UTF8')
        cur = conn.cursor()

        # Hashear la contraseña
        hashed_password = generate_password_hash(ADMIN_CONTRASENA_PLAIN, method='pbkdf2:sha256')

        print(f"Intentando insertar al administrador: {ADMIN_NOMBRE} (Cédula: {ADMIN_CEDULA})")

        # Verificar si el usuario ya existe por cédula o email para evitar conflicto y dar un mensaje más claro
        cur.execute("SELECT id FROM usuarios WHERE cedula = %s OR email = %s", (ADMIN_CEDULA, ADMIN_EMAIL))
        existing_user = cur.fetchone()

        if existing_user:
            print(f"Error: Ya existe un usuario con la cédula '{ADMIN_CEDULA}' o el email '{ADMIN_EMAIL}'. No se insertó el nuevo administrador.")
            return

        # Insertar el nuevo administrador
        cur.execute(
            """
            INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (ADMIN_NOMBRE, ADMIN_CEDULA, ADMIN_EMAIL, hashed_password, ADMIN_ROL, ADMIN_ESTADO)
        )
        new_admin_id = cur.fetchone()[0]
        conn.commit()
        print(f"Administrador '{ADMIN_NOMBRE}' insertado con éxito. ID: {new_admin_id}")

    except psycopg2.OperationalError as e:
        print(f"\nError operacional de PostgreSQL: {e}")
        print("Verifica que el servidor PostgreSQL esté corriendo y accesible,")
        print(f"y que la base de datos '{PG_DB}' exista.")
    except psycopg2.Error as e:
        print(f"\nOcurrió un error de PostgreSQL al insertar el administrador: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"\nOcurrió un error general inesperado: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    print("Iniciando el script para insertar administrador...")
    # Es recomendable tener un archivo .env en el mismo directorio que este script
    # o en el directorio raíz del proyecto con las variables PG_HOST, PG_DB, etc.
    # Ejemplo de .env:
    # PG_HOST=localhost
    # PG_DB=medialert
    # PG_USER=postgres
    # PG_PASS=tu_password_de_db
    # PG_PORT=5432

    if not all([PG_HOST, PG_DB, PG_USER, PG_PASS]):
        print("Error: Faltan variables de entorno para la conexión a la base de datos (PG_HOST, PG_DB, PG_USER, PG_PASS).")
        print("Asegúrate de tener un archivo .env configurado o las variables exportadas.")
    else:
        insertar_admin()
    print("Proceso de inserción de administrador finalizado.")