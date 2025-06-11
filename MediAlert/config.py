# medialert/config.py

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de Conexión a la Base de Datos ---
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_DB = os.getenv('PG_DB', 'medialert')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASS = os.getenv('PG_PASS', '0102')
PG_PORT = os.getenv('PG_PORT', '5432')

# --- Configuración de Flask ---
SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'super_secret_key_dev_only') # Use a strong key in production

# --- Configuración para Almacenamiento de Reportes ---
# Obtener la ruta del directorio actual del archivo config.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Definir la ruta a la carpeta 'instance' que está un nivel arriba de 'medialert'
# Asumiendo que medialert/config.py es medialert/config.py
# y la carpeta 'instance' está en la raíz del proyecto
INSTANCE_FOLDER_NAME = 'instance'
REPORTS_SUBDIRECTORY = 'generated_reports'

INSTANCE_FOLDER_PATH = os.path.join(BASE_DIR, '..', INSTANCE_FOLDER_NAME)
REPORTS_STORAGE_PATH = os.path.join(INSTANCE_FOLDER_PATH, REPORTS_SUBDIRECTORY)

ALLOWED_EXTENSIONS = {'pdf'}

# Función para verificar extensiones de archivo (se usará en report_service)
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS