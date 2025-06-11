# medialert/main.py

from flask import Flask, session, render_template, send_from_directory
from flask_cors import CORS
import os
import logging

# Importar la configuración de la aplicación
import config

# Importar los blueprints de los routers
from routers.auth import auth_bp
from routers.users import users_bp
from routers.medications import medications_bp
from routers.alerts import alerts_bp
from routers.reports import reports_bp

app = Flask(__name__, static_url_path='/static', static_folder='static', template_folder='templates')

# Cargar la configuración desde el módulo config
app.config.from_object('config')

# --- Definir rutas completas para carpetas de almacenamiento ---
# Esto se hace aquí porque app.root_path solo está disponible después de crear la instancia de Flask app
app.config['INSTANCE_FOLDER_PATH'] = os.path.join(app.root_path, '..', config.INSTANCE_FOLDER_NAME)
app.config['REPORTS_STORAGE_PATH'] = os.path.join(app.config['INSTANCE_FOLDER_PATH'], config.REPORTS_SUBDIRECTORY)

# Configurar CORS
CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": "*"}})

# --- ESTO ES CRUCIAL: REGISTRAR BLUEPRINTS PRIMERO, ANTES DE CUALQUIER app.route GENÉRICO ---
app.register_blueprint(auth_bp, url_prefix='/api')
app.register_blueprint(users_bp, url_prefix='/api/admin')
app.register_blueprint(medications_bp, url_prefix='/api/admin')
app.register_blueprint(alerts_bp, url_prefix='/api') # Some alerts endpoints are client-facing
app.register_blueprint(reports_bp, url_prefix='/api/admin') # This prefix combined with /auditoria forms /api/admin/auditoria


# --- LUEGO, LAS RUTAS PARA SERVIR ARCHIVOS HTML O ESTÁTICOS ---
# Estas rutas deben ir DESPUÉS de todos los blueprint.register_blueprint()
@app.route('/')
def index():
    # Si hay sesión, redirigir a la página correspondiente, sino al login
    if 'user_id' in session:
        if session.get('rol') == 'admin':
            return render_template('admin.html')
        elif session.get('rol') == 'cliente':
            return render_template('client.html')
    return render_template('login.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/<path:filename>') # This is the catch-all for static/template files
def serve_html_or_static(filename):
    # Servir archivos HTML específicos desde la raíz de templates
    html_files = ['admin.html', 'client.html', 'login.html', 'configuracion.html']
    if filename in html_files:
        # Redirigir a login si no está autenticado y no es login.html
        if filename != 'login.html' and 'user_id' not in session:
            return render_template('login.html') 
        
        # Si ya está logueado, redirigir de login a su panel
        if filename == 'login.html' and 'user_id' in session:
            if session.get('rol') == 'admin':
                return render_template('admin.html')
            elif session.get('rol') == 'cliente':
                return render_template('client.html')
        
        try:
            return render_template(filename)
        except Exception as e: 
            app.logger.warn(f"Template HTML no encontrado: {filename}, error: {e}")
            pass 
    
    # Intentar servir como archivo estático (CSS, JS, IMG)
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e: 
        app.logger.warn(f"Archivo estático o HTML no encontrado: {filename}, error: {e}")
        return "Archivo no encontrado", 404

# Inicialización de la aplicación
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
    app.logger.info("Iniciando la aplicación MediAlert...")
    
    # Asegurarse de que el directorio 'instance' y 'generated_reports' existan
    if not os.path.exists(app.config['INSTANCE_FOLDER_PATH']):
        os.makedirs(app.config['INSTANCE_FOLDER_PATH'], exist_ok=True)
    if not os.path.exists(app.config['REPORTS_STORAGE_PATH']):
        os.makedirs(app.config['REPORTS_STORAGE_PATH'], exist_ok=True)
        
    app.run(debug=True, host='0.0.0.0', port=5000)