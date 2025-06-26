import os
import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from datetime import timedelta  # <-- Agrega este import

# Cargar variables de entorno
load_dotenv()

PG_HOST = os.getenv('PG_HOST')
PG_DB = os.getenv('PG_DB')
PG_USER = os.getenv('PG_USER')
PG_PASS = os.getenv('PG_PASS')
PG_PORT = os.getenv('PG_PORT')

# Datos EPS
eps_data = [
    ('Nueva EPS', '8301086054', '/static/img/nueva-eps.png', 'activo'),
    ('Sura EPS', '8909031357', '/static/img/sura-eps.png', 'activo'),
    ('Sanitas EPS', '8605136814', '/static/img/sanitas-eps.png', 'activo'),
    ('Compensar EPS', '8600667017', '/static/img/compensar-eps.png', 'activo'),
    ('Coosalud EPS', '8002047247', '/static/img/coosalud-eps.png', 'activo'),
    ('Salud Total EPS', '8001021464', '/static/img/salud-total-eps.png', 'activo'),
    ('Famisanar EPS', '8605330366', '/static/img/famisanar-eps.png', 'activo'),
    ('Aliansalud EPS', '8300262108', '/static/img/aliansalud-eps.png', 'activo'),
    ('EPM Salud', '8110000632', '/static/img/epm-salud.png', 'inactivo'),
    ('SaludMia EPS', '9009848521', '/static/img/saludmia-eps.png', 'activo')
]

# Datos medicamentos (solo algunos por espacio, agrega todos si lo deseas)
medicamentos_data = [
    ('Paracetamol 500mg', 'Analgésico y antipirético.', 'Paracetamol 500mg', 'Náuseas, hepatotoxicidad en sobredosis', 'Fiebre, dolor leve a moderado', 'Todas las edades', 'disponible'),
    ('Ibuprofeno 400mg', 'Antiinflamatorio no esteroideo.', 'Ibuprofeno 400mg', 'Gastritis, dolor abdominal', 'Dolor, inflamación, fiebre', 'Mayores de 6 meses', 'disponible'),
    ('Aspirina 100mg', 'Antiplaquetario y antiinflamatorio.', 'Ácido acetilsalicílico 100mg', 'Sangrado gastrointestinal', 'Prevención trombosis, dolor leve', 'Adultos', 'disponible'),
    ('Amoxicilina 500mg', 'Antibiótico β-lactámico.', 'Amoxicilina trihidrato 500mg', 'Diarrea, candidiasis', 'Infecciones respiratorias, urinarias', 'Todas las edades', 'disponible'),
    ('Azitromicina 500mg', 'Antibiótico macrólido.', 'Azitromicina dihidrato 500mg', 'Dolor abdominal, diarrea', 'Infecciones respiratorias, otitis', 'Adultos y niños >6 meses', 'disponible'),
    ('Ciprofloxacino 500mg', 'Antibiótico fluoroquinolónico.', 'Ciprofloxacino clorhidrato 500mg', 'Tendinitis, fotosensibilidad', 'ITU, gastroenteritis', 'Adultos >18 años', 'disponible'),
    ('Metformina 850mg', 'Antidiabético oral, biguanida.', 'Metformina clorhidrato 850mg', 'Diarrea, acidosis láctica (raro)', 'Diabetes tipo 2', 'Adultos', 'disponible'),
    ('Atorvastatina 20mg', 'Reductor de lípidos, estatina.', 'Atorvastatina cálcica 20mg', 'Mialgias, elevación de transaminasas', 'Hipercolesterolemia', 'Adultos', 'disponible'),
    ('Omeprazol 20mg', 'Inhibidor de bomba de protones.', 'Omeprazol 20mg', 'Dolor de cabeza, diarrea', 'Reflujo gastroesofágico, úlcera péptica', 'Adultos y niños >1 año', 'disponible'),
    ('Loratadina 10mg', 'Antihistamínico H1 de segunda generación.', 'Loratadina 10mg', 'Cefalea, somnolencia (raro)', 'Alergias, rinitis alérgica', 'Adultos y niños >2 años', 'disponible'),
    ('Salbutamol 100mcg', 'Broncodilatador β2 agonista de acción corta.', 'Salbutamol sulfato 100mcg por dosis', 'Temblor, taquicardia', 'Asma, EPOC', 'Todas las edades', 'disponible'),
    ('Enalapril 10mg', 'IECA para hipertensión.', 'Enalapril maleato 10mg', 'Tos seca, hipotensión', 'Hipertensión, IC', 'Adultos', 'disponible'),
    ('Losartán 50mg', 'ARA-II para hipertensión.', 'Losartán potásico 50mg', 'Mareo, hiperkalemia', 'Hipertensión, nefropatía diabética', 'Adultos', 'disponible'),
    ('Amlodipino 5mg', 'Bloqueador de canales de calcio.', 'Amlodipino besilato 5mg', 'Edema periférico, cefalea', 'Hipertensión, angina', 'Adultos y niños >6 años', 'disponible'),
    ('Hidroclorotiazida 25mg', 'Diurético tiazídico.', 'Hidroclorotiazida 25mg', 'Hipopotasemia, hiponatremia', 'Hipertensión', 'Adultos', 'disponible'),
    ('Warfarina 5mg', 'Anticoagulante cumarínico.', 'Warfarina sódica 5mg', 'Hemorragias, necrosis cutánea', 'Trombosis, fibrilación auricular', 'Adultos', 'disponible'),
    ('Sertralina 50mg', 'ISRS para depresión y ansiedad.', 'Sertralina 50mg', 'Náuseas, insomnio', 'Depresión, TOC', 'Adultos', 'disponible'),
    ('Fenacetina Pura', 'Analgésico antiguo, retirado.', 'Fenacetina', 'Nefropatía, carcinogenicidad', 'Ya no se usa', 'N/A', 'discontinuado'),
    ('Levotiroxina 50mcg', 'Hormona tiroidea sintética.', 'Levotiroxina sódica 50mcg', 'Palpitaciones, pérdida de peso', 'Hipotiroidismo', 'Todas las edades', 'disponible'),
    ('Pregabalina 75mg', 'Análogo del GABA.', 'Pregabalina 75mg', 'Mareo, somnolencia', 'Dolor neuropático, fibromialgia', 'Adultos', 'disponible'),
    ('Vitamina D3 1000UI', 'Suplemento de vitamina D.', 'Colecalciferol 1000 UI', 'Hipercalcemia (en sobredosis)', 'Deficiencia de vitamina D', 'Todas las edades', 'disponible'),
    ('Hierro Fumarato 200mg', 'Suplemento de hierro.', 'Fumarato ferroso 200mg', 'Estreñimiento, heces oscuras', 'Anemia ferropénica', 'Todas las edades', 'disponible'),
    ('Ranitidina 150mg', 'Antagonista H2, reduce producción de ácido.', 'Ranitidina 150mg', 'Constipación, somnolencia', 'Úlcera gástrica, reflujo', 'Adultos y niños >12 años', 'disponible'),
    ('Cetirizina 10mg', 'Antihistamínico H1 de segunda generación.', 'Cetirizina 10mg', 'Somnolencia, boca seca', 'Urticaria, rinitis alérgica', 'Adultos y niños >6 años', 'disponible'),
    ('Prednisona 5mg', 'Corticosteroide oral.', 'Prednisona 5mg', 'Aumento de peso, hipertensión', 'Inflamación, alergias severas', 'Adultos', 'disponible'),
    ('Metoclopramida 10mg', 'Procinético y antiemético.', 'Metoclopramida 10mg', 'Somnolencia, espasmos musculares', 'Náuseas, gastroparesia', 'Adultos y niños >1 año', 'disponible'),
    ('Naproxeno 500mg', 'AINE de larga acción.', 'Naproxeno 500mg', 'Ulceración GI, retención de líquidos', 'Artritis, dolor crónico', 'Adultos y niños >12 años', 'disponible'),
    ('Clonazepam 0.5mg', 'Benzodiacepina de acción prolongada.', 'Clonazepam 0.5mg', 'Somnolencia, dependencia', 'Ansiedad, epilepsia', 'Adultos >18 años', 'disponible'),
    ('Tramadol 50mg', 'Analgésico opioide.', 'Tramadol clorhidrato 50mg', 'Mareo, náuseas', 'Dolor moderado a severo', 'Adultos', 'disponible'),
    ('Metronidazol 500mg', 'Antibacteriano y antiprotozoario.', 'Metronidazol 500mg', 'Sabor metálico, neuropatía', 'Infecciones anaerobias, giardiasis', 'Adultos y niños >3 años', 'disponible'),
    ('Fluconazol 150mg', 'Antifúngico azólico.', 'Fluconazol 150mg', 'Náuseas, hepatotoxicidad', 'Candidiasis vaginal', 'Adultos y niños >2 años', 'disponible'),
    ('Metoprolol 50mg', 'Betabloqueador cardioselectivo.', 'Metoprolol tartrato 50mg', 'Bradicardia, fatiga', 'Hipertensión, angina', 'Adultos', 'disponible'),
    ('Furosemida 40mg', 'Diurético de asa.', 'Furosemida 40mg', 'Deshidratación, ototoxicidad (raro)', 'Edema, IC', 'Adultos >18 años', 'disponible'),
    ('Clopidogrel 75mg', 'Inhibidor de P2Y12, antiplaquetario.', 'Clopidogrel 75mg', 'Sangrado, dispepsia', 'Síndrome coronario agudo', 'Adultos', 'disponible'),
    ('Simvastatina 20mg', 'Estatina para reducción de colesterol.', 'Simvastatina 20mg', 'Mialgias, elevación de enzimas hepáticas', 'Dislipidemia', 'Adultos', 'disponible'),
    ('Pantoprazol 40mg', 'IBP para mantenimiento de reflujo.', 'Pantoprazol sódico 40mg', 'Cefalea, diarrea', 'ERGE, úlcera péptica', 'Adultos y niños >1 año', 'disponible'),
    ('Montelukast 10mg', 'Antileucotrieno.', 'Montelukast sodio 10mg', 'Cefalea, dolor abdominal', 'Asma, rinitis alérgica', 'Adultos y niños >2 años', 'disponible'),
    ('Budesonida 200mcg', 'Corticosteroide inhalado.', 'Budesonida 200mcg/dosis', 'Irritación orofaríngea', 'Asma, EPOC', 'Adultos y niños >6 años', 'disponible'),
    ('Insulina glargina 100UI/ml', 'Insulina basal de acción prolongada.', 'Insulina glargina 100UI/ml', 'Hipoglucemia, lipodistrofia', 'Diabetes tipo 1 y 2', 'Adultos', 'disponible'),
    ('Sertralina 100mg', 'ISRS para depresión y ansiedad.', 'Sertralina 100mg', 'Náuseas, insomnio, disfunción sexual', 'Depresión, TOC, pánico', 'Adultos', 'disponible'),
    ('Fluoxetina 20mg', 'ISRS de larga vida media.', 'Fluoxetina 20mg', 'Insomnio, ansiedad', 'Depresión, bulimia nerviosa', 'Adultos', 'disponible'),
    ('Alprazolam 0.5mg', 'Benzodiacepina de acción corta.', 'Alprazolam 0.5mg', 'Dependencia, sedación', 'Ansiedad, pánico', 'Adultos', 'disponible'),
    ('Quetiapina 50mg', 'Antipsicótico atípico.', 'Quetiapina fumarato 50mg', 'Sedación, aumento de peso', 'Esquizofrenia, bipolaridad', 'Adultos', 'disponible'),
    ('Aciclovir 400mg', 'Antiviral.', 'Aciclovir 400mg', 'Cefalea, náuseas', 'Herpes labial, varicela', 'Adultos y niños >2 años', 'disponible'),
    ('Loperamida 2mg', 'Antidiarreico.', 'Loperamida 2mg', 'Estreñimiento, mareo', 'Diarrea aguda', 'Adultos y niños >2 años', 'disponible'),
    ('Doxiciclina 100mg', 'Antibiótico tetraciclina.', 'Doxiciclina 100mg', 'Fotosensibilidad, dispepsia', 'Acné, infecciones respiratorias', 'Adultos y niños >8 años', 'disponible')
]

# Usuarios (contraseña hasheada)
usuarios = [
    {'nombre': 'Brian Acevedo', 'cedula': '1092526700', 'email': 'admin@medialert.co', 'contrasena': 'a0416g', 'rol': 'admin', 'estado_usuario': 'activo', 'fecha_nacimiento': '1990-04-16', 'telefono': '3101234567', 'ciudad': 'Cúcuta', 'eps_id': 1, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Einer Alvear', 'cedula': '1092526701', 'email': 'eineralvear77@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1992-05-21', 'telefono': '3118765432', 'ciudad': 'Bogotá D.C.', 'eps_id': 2, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Brayan Amado', 'cedula': '1092526702', 'email': 'brayanamadoitg7c@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1995-03-15', 'telefono': '3123456789', 'ciudad': 'Medellín', 'eps_id': 3, 'tipo_regimen': 'Subsidiado', 'genero': 'Masculino'},
    {'nombre': 'Juse Carrillo', 'cedula': '1092526703', 'email': 'jusecare015@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1988-11-30', 'telefono': '3145678901', 'ciudad': 'Cali', 'eps_id': 4, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Carlos Escamilla', 'cedula': '1092526704', 'email': 'carlosescamilla2023@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'inactivo', 'fecha_nacimiento': '2000-01-01', 'telefono': '3156789012', 'ciudad': 'Barranquilla', 'eps_id': 5, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Xiomara Fajardo', 'cedula': '1092526705', 'email': 'xiomystefanny27@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1999-07-07', 'telefono': '3167890123', 'ciudad': 'Cartagena', 'eps_id': 6, 'tipo_regimen': 'Especial', 'genero': 'Femenino'},
    {'nombre': 'Yarly Guerrero', 'cedula': '1092526706', 'email': 'yarlyguerrero17@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1998-02-14', 'telefono': '3178901234', 'ciudad': 'Bucaramanga', 'eps_id': 7, 'tipo_regimen': 'Contributivo', 'genero': 'Femenino'},
    {'nombre': 'Jersain Hernández', 'cedula': '1092526707', 'email': 'jersahercal1904@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1991-04-19', 'telefono': '3189012345', 'ciudad': 'Pereira', 'eps_id': 8, 'tipo_regimen': 'Subsidiado', 'genero': 'Masculino'},
    {'nombre': 'Kevin Marquez', 'cedula': '1092526708', 'email': 'marquezkevin467@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1996-10-25', 'telefono': '3190123456', 'ciudad': 'Bogotá D.C.', 'eps_id': 1, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Juan Ochoa', 'cedula': '1092526709', 'email': 'juancamiloochoajaimes1@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1993-06-12', 'telefono': '3201234567', 'ciudad': 'Medellín', 'eps_id': 2, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Julian Pulido', 'cedula': '1092526710', 'email': 'pulidojulian00@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1990-09-01', 'telefono': '3212345678', 'ciudad': 'Cali', 'eps_id': 3, 'tipo_regimen': 'Especial', 'genero': 'Masculino'},
    {'nombre': 'Daniel Rodriguez', 'cedula': '1092526711', 'email': 'dfra0512@outlook.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1987-12-05', 'telefono': '3223456789', 'ciudad': 'Barranquilla', 'eps_id': 4, 'tipo_regimen': 'Subsidiado', 'genero': 'Masculino'},
    {'nombre': 'Carlos Rojas', 'cedula': '1092526712', 'email': 'carlosrojascubides10a@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1994-07-20', 'telefono': '3234567890', 'ciudad': 'Cartagena', 'eps_id': 5, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Kevin Rojas', 'cedula': '1092526713', 'email': 'sauremk30@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1999-11-11', 'telefono': '3005678901', 'ciudad': 'Bucaramanga', 'eps_id': 6, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Jorge Rolon', 'cedula': '1092526714', 'email': 'jorgesebastianrolonmarquez@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1997-08-18', 'telefono': '3016789012', 'ciudad': 'Cúcuta', 'eps_id': 7, 'tipo_regimen': 'Especial', 'genero': 'Masculino'},
    {'nombre': 'Sofia Velandia', 'cedula': '1092526715', 'email': 'sovelandiap2005@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '2005-01-20', 'telefono': '3027890123', 'ciudad': 'Pereira', 'eps_id': 8, 'tipo_regimen': 'Subsidiado', 'genero': 'Femenino'},
    {'nombre': 'Osmar Vera', 'cedula': '1092526716', 'email': 'osmarandresvera@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'inactivo', 'fecha_nacimiento': '1985-05-25', 'telefono': '3038901234', 'ciudad': 'Bogotá D.C.', 'eps_id': 1, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Geronimo Vergara', 'cedula': '1092526717', 'email': 'geronjose20@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1992-02-28', 'telefono': '3049012345', 'ciudad': 'Medellín', 'eps_id': 2, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Daniel Villamizar', 'cedula': '1092526718', 'email': 'dani3lsu4rez@gmail.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1998-03-03', 'telefono': '3050123456', 'ciudad': 'Cali', 'eps_id': 3, 'tipo_regimen': 'Subsidiado', 'genero': 'Masculino'},
    {'nombre': 'Laura Gómez', 'cedula': '10100101', 'email': 'laura.gomez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1991-08-10', 'telefono': '3102345678', 'ciudad': 'Bogotá D.C.', 'eps_id': 1, 'tipo_regimen': 'Contributivo', 'genero': 'Femenino'},
    {'nombre': 'Carlos Rodríguez', 'cedula': '10100102', 'email': 'carlos.rodriguez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1985-04-25', 'telefono': '3113456789', 'ciudad': 'Medellín', 'eps_id': 2, 'tipo_regimen': 'Subsidiado', 'genero': 'Masculino'},
    {'nombre': 'Ana Martínez', 'cedula': '10100103', 'email': 'ana.martinez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1993-02-18', 'telefono': '3124567890', 'ciudad': 'Cali', 'eps_id': 3, 'tipo_regimen': 'Contributivo', 'genero': 'Femenino'},
    {'nombre': 'Jorge Hernández', 'cedula': '10100104', 'email': 'jorge.hernandez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1978-12-01', 'telefono': '3135678901', 'ciudad': 'Barranquilla', 'eps_id': 4, 'tipo_regimen': 'Especial', 'genero': 'Masculino'},
    {'nombre': 'Sofía Pérez', 'cedula': '10100105', 'email': 'sofia.perez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'inactivo', 'fecha_nacimiento': '2001-06-30', 'telefono': '3146789012', 'ciudad': 'Cartagena', 'eps_id': 5, 'tipo_regimen': 'Subsidiado', 'genero': 'Femenino'},
    {'nombre': 'Luis Díaz', 'cedula': '10100106', 'email': 'luis.diaz@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1998-09-14', 'telefono': '3157890123', 'ciudad': 'Bucaramanga', 'eps_id': 6, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Valentina Torres', 'cedula': '10100107', 'email': 'valentina.torres@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1990-07-22', 'telefono': '3168901234', 'ciudad': 'Cúcuta', 'eps_id': 7, 'tipo_regimen': 'Contributivo', 'genero': 'Femenino'},
    {'nombre': 'Andrés Ramírez', 'cedula': '10100108', 'email': 'andres.ramirez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1995-01-05', 'telefono': '3179012345', 'ciudad': 'Pereira', 'eps_id': 8, 'tipo_regimen': 'Subsidiado', 'genero': 'Masculino'},
    {'nombre': 'Camila Vargas', 'cedula': '10100109', 'email': 'camila.vargas@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1989-10-12', 'telefono': '3180123456', 'ciudad': 'Bogotá D.C.', 'eps_id': 1, 'tipo_regimen': 'Contributivo', 'genero': 'Femenino'},
    {'nombre': 'Diego Moreno', 'cedula': '10100110', 'email': 'diego.moreno@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1992-11-20', 'telefono': '3191234567', 'ciudad': 'Medellín', 'eps_id': 2, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'Isabella Jiménez', 'cedula': '10100111', 'email': 'isabella.jimenez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1997-03-03', 'telefono': '3202345678', 'ciudad': 'Cali', 'eps_id': 3, 'tipo_regimen': 'Especial', 'genero': 'Femenino'},
    {'nombre': 'Juan Ruiz', 'cedula': '10100112', 'email': 'juan.ruiz@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'activo', 'fecha_nacimiento': '1980-05-19', 'telefono': '3213456789', 'ciudad': 'Barranquilla', 'eps_id': 4, 'tipo_regimen': 'Contributivo', 'genero': 'Masculino'},
    {'nombre': 'María Suárez', 'cedula': '10100113', 'email': 'maria.suarez@example.com', 'contrasena': '1234', 'rol': 'cliente', 'estado_usuario': 'inactivo', 'fecha_nacimiento': '1999-08-28', 'telefono': '3224567890', 'ciudad': 'Cartagena', 'eps_id': 5, 'tipo_regimen': 'Subsidiado', 'genero': 'Femenino'}
]

# Alertas (solo algunas por espacio, agrega todas si lo deseas)
alertas_data = [
    # usuario_email, medicamento_nombre, dosis, frecuencia, fecha_inicio_offset, fecha_fin_offset, hora, estado
    ('laura.gomez@example.com', 'Paracetamol 500mg', '1 comprimido', 'Cada 8 horas', 0, 30, '08:00:00', 'activa'),
    ('laura.gomez@example.com', 'Ibuprofeno 400mg', '1 tableta', 'Cada 12 horas', -10, 5, '12:00:00', 'activa'),
    ('carlos.rodriguez@example.com', 'Losartán 50mg', '1 tableta', 'Cada 12 horas', -90, None, '09:00:00', 'activa'),
    ('carlos.rodriguez@example.com', 'Metformina 850mg', '1 tableta', 'Con cada comida', -90, None, '21:00:00', 'activa'),
    ('ana.martinez@example.com', 'Amoxicilina 500mg', '1 cápsula', 'Cada 8 horas', -7, 0, '06:00:00', 'completada'),
    ('jorge.hernandez@example.com', 'Salbutamol 100mcg', '2 inhalaciones', 'Cada 6 horas', -180, None, '07:30:00', 'activa'),
    ('luis.diaz@example.com', 'Sertralina 50mg', '1 tableta', 'Una vez al día', -60, None, '10:00:00', 'activa'),
    ('valentina.torres@example.com', 'Levotiroxina 50mcg', '1 comprimido', 'Antes de dormir', -365, None, '22:00:00', 'activa'),
    ('andres.ramirez@example.com', 'Amlodipino 5mg', '1 tableta', 'Una vez al día', -50, 100, '20:00:00', 'activa'),
    ('camila.vargas@example.com', 'Vitamina D3 1000UI', '1 cápsula', 'Cada 24 horas', -20, 20, '13:00:00', 'activa'),
    ('diego.moreno@example.com', 'Warfarina 5mg', '1/2 tableta', 'Cada día', -400, None, '19:00:00', 'activa'),
    ('isabella.jimenez@example.com', 'Atorvastatina 20mg', '1 comprimido', 'Cada noche', -150, None, '21:30:00', 'activa'),
    ('juan.ruiz@example.com', 'Hierro Fumarato 200mg', '1 cápsula', 'Con almuerzo', -10, 80, '12:30:00', 'activa'),
    ('santiago.garcia@example.com', 'Pregabalina 75mg', '1 cápsula', 'Cada 12 horas', -25, 5, '10:00:00', 'completada'),
    ('santiago.garcia@example.com', 'Pregabalina 75mg', '1 cápsula', 'Cada 12 horas', -25, 5, '22:00:00', 'completada'),
    ('daniela.ortiz@example.com', 'Enalapril 10mg', '1 tableta', 'Cada 24 horas', -200, None, '07:00:00', 'activa'),
    ('eineralvear77@gmail.com', 'Paracetamol 500mg', '2 tabletas', 'Si hay dolor', 0, 10, '10:00:00', 'activa'),
    ('eineralvear77@gmail.com', 'Loratadina 10mg', '1 tableta', 'En la mañana', -5, 25, '06:30:00', 'activa'),
    ('brayanamadoitg7c@gmail.com', 'Metformina 850mg', '1 tableta', 'Después del desayuno', -80, None, '08:30:00', 'activa')
]

def get_db_connection():
    return psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        port=PG_PORT,
        client_encoding='UTF8'
    )

def poblar_eps(connection):
    with connection.cursor() as cursor:
        for e in eps_data:
            cursor.execute("""
                INSERT INTO eps (nombre, nit, logo_url, estado)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nit) DO NOTHING;
            """, e)
    connection.commit()
    print("✔️ EPS insertadas.")

def poblar_medicamentos(connection):
    with connection.cursor() as cursor:
        for m in medicamentos_data:
            cursor.execute("""
                INSERT INTO medicamentos (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (nombre) DO NOTHING;
            """, m)
    connection.commit()
    print("✔️ Medicamentos insertados.")

def poblar_usuarios(connection):
    with connection.cursor() as cursor:
        for usuario in usuarios:
            hashed_password = generate_password_hash(usuario['contrasena'], method='pbkdf2:sha256')
            cursor.execute("""
                INSERT INTO usuarios (
                    nombre, cedula, email, contrasena, rol, estado_usuario, fecha_nacimiento,
                    telefono, ciudad, eps_id, tipo_regimen, genero
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (cedula) DO NOTHING;
            """, (
                usuario['nombre'], usuario['cedula'], usuario['email'],
                hashed_password,
                usuario['rol'], usuario['estado_usuario'], usuario['fecha_nacimiento'],
                usuario['telefono'], usuario['ciudad'], usuario['eps_id'],
                usuario['tipo_regimen'], usuario['genero']
            ))
    connection.commit()
    print("✔️ Usuarios insertados.")

def poblar_alertas(connection):
    with connection.cursor() as cursor:
        for a in alertas_data:
            usuario_email, medicamento_nombre, dosis, frecuencia, fecha_inicio_offset, fecha_fin_offset, hora, estado = a
            # Obtener usuario_id y medicamento_id
            cursor.execute("SELECT id FROM usuarios WHERE email=%s", (usuario_email,))
            usuario_row = cursor.fetchone()
            cursor.execute("SELECT id FROM medicamentos WHERE nombre=%s", (medicamento_nombre,))
            medicamento_row = cursor.fetchone()
            if not usuario_row or not medicamento_row:
                continue
            usuario_id = usuario_row[0]
            medicamento_id = medicamento_row[0]
            # Obtener admin id para asignado_por_usuario_id
            cursor.execute("SELECT id FROM usuarios WHERE rol='admin' LIMIT 1")
            admin_row = cursor.fetchone()
            asignado_por_usuario_id = admin_row[0] if admin_row else None
            # Calcular fechas usando timedelta
            cursor.execute("SELECT CURRENT_DATE")
            today = cursor.fetchone()[0]
            fecha_inicio = today + timedelta(days=fecha_inicio_offset or 0)
            fecha_fin = today + timedelta(days=fecha_fin_offset) if fecha_fin_offset is not None else None
            cursor.execute("""
                INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, asignado_por_usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, (
                usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora, estado, asignado_por_usuario_id
            ))
    connection.commit()
    print("✔️ Alertas insertadas.")

def main():
    print("--- Poblando toda la base de datos ---")
    conn = None
    try:
        conn = get_db_connection()
        poblar_eps(conn)
        poblar_medicamentos(conn)
        poblar_usuarios(conn)
        poblar_alertas(conn)
        print("🎉 ¡Base de datos poblada exitosamente!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()
            print("🔌 Conexión cerrada.")

if __name__ == '__main__':
    main()
