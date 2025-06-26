import os
import psycopg2
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de la Conexión a la Base de Datos ---
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_DB = os.getenv('PG_DB', 'MediAlert')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASS = os.getenv('PG_PASS', '0102')
PG_PORT = os.getenv('PG_PORT', '5432')

# --- Rutas a los archivos SQL ---
SCHEMA_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), 'script_MediAlert.sql')


def get_db_connection():
    """
    Establece y retorna una conexión a la base de datos PostgreSQL, asegurando la codificación UTF-8.
    """
    try:
        # CORRECCIÓN FINAL: Se añade el parámetro 'client_encoding' aquí también.
        # Esto asegura que este script (que ESCRIBE los datos) use la misma codificación
        # que la aplicación principal (que LEE los datos), solucionando el conflicto.
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT,
            client_encoding='UTF8'
        )
        print("✅ Conexión (init_db) a la base de datos establecida con éxito en UTF-8.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"❌ Error al conectar con la base de datos desde init_db.py: {e}")
        raise


def execute_sql_from_file(connection, filepath):
    """
    Ejecuta un script SQL desde un archivo, estandarizándolo a UTF-8 si es necesario.
    """
    print(f"▶️ Procesando script: {os.path.basename(filepath)}...")
    encodings_to_try = ['utf-8', 'utf-8-sig', 'cp1252', 'latin-1']
    sql_script = None
    successful_encoding = None

    for encoding in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                sql_script = f.read()
            successful_encoding = encoding
            break
        except (UnicodeDecodeError, FileNotFoundError):
            continue

    if successful_encoding and successful_encoding != 'utf-8':
        print(f"   ... Archivo leído con '{successful_encoding}'. Estandarizando a UTF-8...")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(sql_script)
        print(f"   ✔️ Archivo '{os.path.basename(filepath)}' ha sido guardado como UTF-8.")
    else:
        print(f"   ... Archivo ya está en formato UTF-8 estándar.")

    if sql_script is None:
        raise UnicodeError(f"No se pudo decodificar el archivo {filepath} con ninguna codificación probada.")

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_script)
        connection.commit()
        print(f"✔️ Script SQL ejecutado con éxito.")
    except (psycopg2.Error) as e:
        print(f"❌ Error al ejecutar el script SQL '{filepath}': {e}")
        connection.rollback()
        raise


def main():
    """
    Función principal que orquesta la creación y población de la base de datos.
    """
    print("--- Iniciando Proceso de Inicialización de la Base de Datos ---")
    conn = None
    try:
        conn = get_db_connection()
        execute_sql_from_file(conn, SCHEMA_SCRIPT_PATH)
        print("\n🎉 ¡Proceso de inicialización de la base de datos completado exitosamente!")
    except Exception as e:
        print(f"\n🔥 El proceso de inicialización falló. Error: {e!r}")
    finally:
        if conn:
            conn.close()
            print("\n🔌 Conexión a la base de datos cerrada.")
        print("--- Proceso de Inicialización de la Base de Datos Finalizado ---")


if __name__ == '__main__':
    main()

