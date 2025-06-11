import psycopg2
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
import random
from datetime import datetime, timedelta, date
import re # Importar el módulo re

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# --- Configuración de la Conexión a la Base de Datos ---
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_DB = os.getenv('PG_DB', 'medialert')
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASS = os.getenv('PG_PASS', '0102')
PG_PORT = os.getenv('PG_PORT', '5432')

# --- Datos para Generación ---
# Listas mejoradas con nombres y apellidos colombianos comunes
first_names_male = [
    'Juan', 'Carlos', 'Andrés', 'Jorge', 'Luis', 'Diego', 'Fernando', 'Alejandro', 
    'Miguel', 'José', 'David', 'Santiago', 'Sebastián', 'Daniel', 'Mateo',
    'Camilo', 'Felipe', 'Ricardo', 'Esteban', 'Manuel'
]
first_names_female = [
    'María', 'Ana', 'Sofía', 'Camila', 'Valentina', 'Isabella', 'Laura', 'Paula', 
    'Daniela', 'Carolina', 'Luisa', 'Juliana', 'Gabriela', 'Manuela', 'Adriana',
    'Marcela', 'Patricia', 'Sandra', 'Mónica', 'Catalina'
]
all_first_names = first_names_male + first_names_female

last_names = [
    'Gómez', 'Rodríguez', 'González', 'López', 'Martínez', 'Hernández', 'Pérez', 
    'Díaz', 'Torres', 'Ramírez', 'Vargas', 'Moreno', 'Jiménez', 'Ruiz', 'Suárez',
    'García', 'Ortiz', 'Silva', 'Rojas', 'Mendoza', 'Castro', 'Álvarez', 'Fernández',
    'Sanchez', 'Romero', 'Soto', 'Herrera', 'Mejía', 'Osorio', 'Valencia'
]

# Ciudades colombianas con sus códigos de área para teléfonos fijos (indicativos)
# y algunos prefijos comunes para celulares
ciudades_colombia = {
    'Bogotá D.C.': {'indicativo_fijo': '601', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Medellín': {'indicativo_fijo': '604', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Cali': {'indicativo_fijo': '602', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Barranquilla': {'indicativo_fijo': '605', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Cartagena': {'indicativo_fijo': '605', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Bucaramanga': {'indicativo_fijo': '607', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Cúcuta': {'indicativo_fijo': '607', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
    'Pereira': {'indicativo_fijo': '606', 'prefijos_celular': ['300', '301', '302', '304', '305', '310', '311', '312', '313', '314', '320', '321', '322', '323', '350']},
}

# Dominios de email comunes
dominios_email = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 
                  'aol.com', 'icloud.com', 'protonmail.com', 'live.com']


common_pass = "password123"
hashed_common_pass = generate_password_hash(common_pass, method='pbkdf2:sha256')

# Lista de medicamentos (similar a la de init_db.py)
lista_medicamentos_a_insertar = [
    {"nombre": "Paracetamol 500mg", "descripcion": "Analgésico y antipirético.", "composicion": "Paracetamol 500mg", "sintomas_secundarios": "náuseas, hepatotoxicidad en sobredosis", "indicaciones": "fiebre, dolor leve a moderado", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Ibuprofeno 400mg", "descripcion": "Antiinflamatorio no esteroideo.", "composicion": "Ibuprofeno 400mg", "sintomas_secundarios": "gastritis, dolor abdominal", "indicaciones": "dolor, inflamación, fiebre", "rango_edad": "Mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Aspirina 100mg", "descripcion": "Antiplaquetario y antiinflamatorio.", "composicion": "Ácido acetilsalicílico 100mg", "sintomas_secundarios": "sangrado gastrointestinal", "indicaciones": "prevención trombosis, dolor leve", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Amoxicilina 500mg", "descripcion": "Antibiótico β-lactámico.", "composicion": "Amoxicilina trihidrato 500mg", "sintomas_secundarios": "diarrea, candidiasis", "indicaciones": "infecciones respiratorias, urinarias", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Azitromicina 500mg", "descripcion": "Antibiótico macrólido.", "composicion": "Azitromicina dihidrato 500mg", "sintomas_secundarios": "dolor abdominal, diarrea", "indicaciones": "infecciones respiratorias, otitis", "rango_edad": "Adultos y niños mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Ciprofloxacino 500mg", "descripcion": "Antibiótico fluoroquinolónico.", "composicion": "Ciprofloxacino clorhidrato 500mg", "sintomas_secundarios": "tendinitis, fotosensibilidad", "indicaciones": "ITU, gastroenteritis", "rango_edad": "Adultos y niños mayores de 18 años", "estado_medicamento": "disponible"},
    {"nombre": "Metformina 850mg", "descripcion": "Antidiabético oral, biguanida.", "composicion": "Metformina clorhidrato 850mg", "sintomas_secundarios": "diarrea, acidosis láctica (raro)", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Atorvastatina 20mg", "descripcion": "Reductor de lípidos, estatina.", "composicion": "Atorvastatina cálcica 20mg", "sintomas_secundarios": "mialgias, elevación de transaminasas", "indicaciones": "hipercolesterolemia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Omeprazol 20mg", "descripcion": "Inhibidor de bomba de protones.", "composicion": "Omeprazol 20mg", "sintomas_secundarios": "dolor de cabeza, diarrea", "indicaciones": "reflujo gastroesofágico, úlcera péptica", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Ranitidina 150mg", "descripcion": "Antagonista H2, reduce producción de ácido.", "composicion": "Ranitidina 150mg", "sintomas_secundarios": "constipación, somnolencia", "indicaciones": "úlcera gástrica, reflujo", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Loratadina 10mg", "descripcion": "Antihistamínico H1 de segunda generación.", "composicion": "Loratadina 10mg", "sintomas_secundarios": "cefalea, somnolencia (raro)", "indicaciones": "alergias, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Cetirizina 10mg", "descripcion": "Antihistamínico H1 de segunda generación.", "composicion": "Cetirizina 10mg", "sintomas_secundarios": "somnolencia, boca seca", "indicaciones": "urticaria, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Salbutamol 100mcg", "descripcion": "Broncodilatador β2 agonista de acción corta.", "composicion": "Salbutamol sulfato 100mcg por dosis", "sintomas_secundarios": "temblor, taquicardia", "indicaciones": "asma, EPOC", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Prednisona 5mg", "descripcion": "Corticosteroide oral de acción intermedia.", "composicion": "Prednisona 5mg", "sintomas_secundarios": "aumento de peso, hipertensión", "indicaciones": "inflamación, alergias severas", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Metoclopramida 10mg", "descripcion": "Procinético y antiemético.", "composicion": "Metoclopramida 10mg", "sintomas_secundarios": "somnolencia, espasmos musculares", "indicaciones": "náuseas, gastroparesia", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Omeprazol 40mg", "descripcion": "IBP para tratamiento de úlceras más severas.", "composicion": "Omeprazol 40mg", "sintomas_secundarios": "insomnio, mareo", "indicaciones": "síndrome de Zollinger-Ellison", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Naproxeno 500mg", "descripcion": "AINE de larga acción.", "composicion": "Naproxeno 500mg", "sintomas_secundarios": "ulceración GI, retención de líquidos", "indicaciones": "artritis, dolor crónico", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Clonazepam 0.5mg", "descripcion": "Benzodiacepina de acción prolongada.", "composicion": "Clonazepam 0.5mg", "sintomas_secundarios": "somnolencia, dependencia", "indicaciones": "ansiedad, epilepsia", "rango_edad": "Adultos y niños mayores de 18 años", "estado_medicamento": "disponible"},
    {"nombre": "Diazepam 10mg", "descripcion": "Benzodiacepina de acción larga.", "composicion": "Diazepam 10mg", "sintomas_secundarios": "sedación, ataxia", "indicaciones": "ansiedad, espasmos musculares", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Tramadol 50mg", "descripcion": "Analgesico opioide de moderada potencia.", "composicion": "Tramadol clorhidrato 50mg", "sintomas_secundarios": "mareo, náuseas", "indicaciones": "dolor moderado a severo", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Codeína 30mg", "descripcion": "Opioide leve, antitúsivo ocasional.", "composicion": "Codeína fosfato 30mg", "sintomas_secundarios": "estreñimiento, somnolencia", "indicaciones": "dolor leve, tos seca", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Metamizol 575mg", "descripcion": "Analgésico y antipirético no opioide.", "composicion": "Metamizol sódico 575mg", "sintomas_secundarios": "agranulocitosis (raro), hipotensión", "indicaciones": "dolor agudo, fiebre alta", "rango_edad": "Adultos y niños mayores de 3 meses", "estado_medicamento": "disponible"},
    {"nombre": "Ondansetrón 4mg", "descripcion": "Antiemético 5-HT3 receptor antagonista.", "composicion": "Ondansetrón 4mg", "sintomas_secundarios": "estreñimiento, cefalea", "indicaciones": "náuseas por quimioterapia", "rango_edad": "Adultos y niños mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Fluconazol 150mg", "descripcion": "Antifúngico azólico de amplio espectro.", "composicion": "Fluconazol 150mg", "sintomas_secundarios": "náuseas, hepatotoxicidad", "indicaciones": "candidiasis vaginal", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Ketoconazol 200mg", "descripcion": "Antifúngico azólico sistémico.", "composicion": "Ketoconazol 200mg", "sintomas_secundarios": "alteraciones hepáticas", "indicaciones": "dermatofitosis, candidiasis", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Metronidazol 500mg", "descripcion": "Antibacteriano y antiprotozoario nitroimidazol.", "composicion": "Metronidazol 500mg", "sintomas_secundarios": "sabor metálico, neuropatía periferica", "indicaciones": "infecciones anaerobias, giardiasis", "rango_edad": "Adultos y niños mayores de 3 años", "estado_medicamento": "disponible"},
    {"nombre": "Clindamicina 300mg", "descripcion": "Antibiótico lincosamida.", "composicion": "Clindamicina fosfato 300mg", "sintomas_secundarios": "colitis pseudomembranosa", "indicaciones": "infecciones de piel, hueso", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Enalapril 10mg", "descripcion": "IECA para hipertensión.", "composicion": "Enalapril maleato 10mg", "sintomas_secundarios": "tos seca, hipotensión", "indicaciones": "hipertensión, IC", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Losartán 50mg", "descripcion": "ARA-II para hipertensión.", "composicion": "Losartán potásico 50mg", "sintomas_secundarios": "mareo, hiperkalemia", "indicaciones": "hipertensión, nefropatía diabética", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Amlodipino 5mg", "descripcion": "Bloqueador de canales de calcio dihidropiridínico.", "composicion": "Amlodipino besilato 5mg", "sintomas_secundarios": "edema periférico, cefalea", "indicaciones": "hipertensión, angina", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Metoprolol 50mg", "descripcion": "Betabloqueador cardioselectivo.", "composicion": "Metoprolol tartrato 50mg", "sintomas_secundarios": "bradicardia, fatiga", "indicaciones": "hipertensión, angina", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Propanolol 40mg", "descripcion": "Betabloqueador no selectivo.", "composicion": "Propanolol 40mg", "sintomas_secundarios": "broncoespasmo, fatiga", "indicaciones": "hipertensión, temblor esencial", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Hidroclorotiazida 25mg", "descripcion": "Diurético tiazídico.", "composicion": "Hidroclorotiazida 25mg", "sintomas_secundarios": "hipopotasemia, hiponatremia", "indicaciones": "hipertensión", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Furosemida 40mg", "descripcion": "Diurético de asa.", "composicion": "Furosemida 40mg", "sintomas_secundarios": "deshidratación, ototoxicidad (raro)", "indicaciones": "edema, IC", "rango_edad": "Adultos y niños mayores de 18 años", "estado_medicamento": "disponible"},
    {"nombre": "Espironolactona 25mg", "descripcion": "Diurético ahorrador de potasio.", "composicion": "Espironolactona 25mg", "sintomas_secundarios": "hiperkalemia, ginecomastia", "indicaciones": "cirrosis, IC", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Warfarina 5mg", "descripcion": "Anticoagulante cumarínico.", "composicion": "Warfarina sódica 5mg", "sintomas_secundarios": "hemorragias, necrosis cutánea", "indicaciones": "trombosis, fibrilación auricular", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Heparina sódica 5000UI", "descripcion": "Anticoagulante de acción inmediata.", "composicion": "Heparina sódica 5000UI/ml", "sintomas_secundarios": "trombocitopenia, hemorragia", "indicaciones": "profilaxis trombótica", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Enoxaparina 40mg", "descripcion": "HBPM para anticoagulación subcutánea.", "composicion": "Enoxaparina sódica 40mg", "sintomas_secundarios": "trombocitopenia, hemorragia", "indicaciones": "trombosis venosa profunda", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Clopidogrel 75mg", "descripcion": "Inhibidor de P2Y12, antiplaquetario.", "composicion": "Clopidogrel 75mg", "sintomas_secundarios": "sangrado, dispepsia", "indicaciones": "síndrome coronario agudo", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Simvastatina 20mg", "descripcion": "Estatina para reducción de colesterol LDL.", "composicion": "Simvastatina 20mg", "sintomas_secundarios": "mialgias, elevación de enzimas hepáticas", "indicaciones": "dislipidemia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fenofibrato 145mg", "descripcion": "Fibrato para reducción de triglicéridos.", "composicion": "Fenofibrato 145mg", "sintomas_secundarios": "dispepsia, mialgias", "indicaciones": "hipertrigliceridemia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Pantoprazol 40mg", "descripcion": "IBP para mantenimiento de reflujo.", "composicion": "Pantoprazol sódico 40mg", "sintomas_secundarios": "cefalea, diarrea", "indicaciones": "ERGE, úlcera péptica", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Esomeprazol 40mg", "descripcion": "S-isoforma de omeprazol, IBP.", "composicion": "Esomeprazol magnesio 40mg", "sintomas_secundarios": "mareo, flatulencia", "indicaciones": "ERGE", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fexofenadina 180mg", "descripcion": "Antihistamínico H1 no sedante.", "composicion": "Fexofenadina 180mg", "sintomas_secundarios": "cefalea, náuseas", "indicaciones": "alergias estacionales", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Montelukast 10mg", "descripcion": "Antileucotrieno para asma y rinoconjuntivitis.", "composicion": "Montelukast sodio 10mg", "sintomas_secundarios": "cefalea, dolor abdominal", "indicaciones": "asma, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Budesonida 200mcg", "descripcion": "Corticosteroide inhalado.", "composicion": "Budesonida 200mcg/dosis", "sintomas_secundarios": "irritación orofaríngea", "indicaciones": "asma, EPOC", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Beclometasona 100mcg", "descripcion": "Corticosteroide nasal para alergias.", "composicion": "Beclometasona dipropionato 100mcg", "sintomas_secundarios": "irritación nasal", "indicaciones": "rinitis alérgica", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Insulina glargina 100UI/ml", "descripcion": "Insulina basal de acción prolongada.", "composicion": "Insulina glargina 100UI/ml", "sintomas_secundarios": "hipoglucemia, lipodistrofia", "indicaciones": "diabetes tipo 1 y tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Glimepirida 2mg", "descripcion": "Sulfonilurea para diabetes tipo 2.", "composicion": "Glimepirida 2mg", "sintomas_secundarios": "hipoglucemia, aumento de peso", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Gliclazida 80mg", "descripcion": "Sulfonilurea de segunda generación.", "composicion": "Gliclazida 80mg", "sintomas_secundarios": "hipoglucemia, náuseas", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Sitagliptina 100mg", "descripcion": "Inhibidor de DPP-4 para diabetes.", "composicion": "Sitagliptina fosfato sódico 100mg", "sintomas_secundarios": "cefalea, nasofaringitis", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Empagliflozina 10mg", "descripcion": "Inhibidor de SGLT2 para diabetes.", "composicion": "Empagliflozina 10mg", "sintomas_secundarios": "infecciones urinarias, poliuria", "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Sertralina 50mg", "descripcion": "ISRS para depresión y ansiedad.", "composicion": "Sertralina 50mg", "sintomas_secundarios": "náuseas, insomnio", "indicaciones": "depresión, TOC", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fluoxetina 20mg", "descripcion": "ISRS de larga vida media.", "composicion": "Fluoxetina 20mg", "sintomas_secundarios": "insomnio, disfunción sexual", "indicaciones": "depresión, bulimia nerviosa", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Citalopram 20mg", "descripcion": "ISRS para trastornos depresivos.", "composicion": "Citalopram hidrobromuro 20mg", "sintomas_secundarios": "mareo, fatiga", "indicaciones": "depresión", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Alprazolam 0.5mg", "descripcion": "Benzodiacepina de acción corta.", "composicion": "Alprazolam 0.5mg", "sintomas_secundarios": "dependencia, sedación", "indicaciones": "ansiedad, pánico", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Haloperidol 5mg", "descripcion": "Antipsicótico típico de alta potencia.", "composicion": "Haloperidol 5mg", "sintomas_secundarios": "rigidez muscular, acatisia", "indicaciones": "esquizofrenia, psicosis aguda", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Quetiapina 50mg", "descripcion": "Antipsicótico atípico.", "composicion": "Quetiapina fumarato 50mg", "sintomas_secundarios": "sedación, aumento de peso", "indicaciones": "esquizofrenia, bipolaridad", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Topiramato 100mg", "descripcion": "Antiepiléptico y profilaxis de migraña.", "composicion": "Topiramato 100mg", "sintomas_secundarios": "mareo, pérdida de peso", "indicaciones": "epilepsia, migraña", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Sumatriptán 50mg", "descripcion": "Agonista 5-HT1 para migraña.", "composicion": "Sumatriptán succinato 50mg", "sintomas_secundarios": "parestesias, sensación de opresión torácica", "indicaciones": "migraña aguda", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Aciclovir 400mg", "descripcion": "Antiviral inhibidor de ADN polimerasa.", "composicion": "Aciclovir 400mg", "sintomas_secundarios": "cefalea, náuseas", "indicaciones": "herpes labial, varicela", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Valaciclovir 500mg", "descripcion": "Profármaco de aciclovir con mejor biodisponibilidad.", "composicion": "Valaciclovir 500mg", "sintomas_secundarios": "dolor de cabeza, náuseas", "indicaciones": "herpes zóster", "rango_edad": "Adultos y niños mayores de 12 años", "estado_medicamento": "disponible"},
    {"nombre": "Oseltamivir 75mg", "descripcion": "Inhibidor de neuraminidasa para influenza.", "composicion": "Oseltamivir fosfato 75mg", "sintomas_secundarios": "náuseas, vómitos", "indicaciones": "gripe A/B", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Loperamida 2mg", "descripcion": "Antidiarreico opioide sin pasar BHE.", "composicion": "Loperamida 2mg", "sintomas_secundarios": "estreñimiento, mareo", "indicaciones": "diarrea aguda", "rango_edad": "Adultos y niños mayores de 2 años", "estado_medicamento": "disponible"},
    {"nombre": "Lactulosa 10g/15ml", "descripcion": "Laxante osmótico.", "composicion": "Lactulosa 10g por 15ml", "sintomas_secundarios": "flatulencia, dolor abdominal", "indicaciones": "estreñimiento", "rango_edad": "Adultos y niños mayores de 1 año", "estado_medicamento": "disponible"},
    {"nombre": "Doxiciclina 100mg", "descripcion": "Antibiótico tetraciclina de amplio espectro.", "composicion": "Doxiciclina 100mg", "sintomas_secundarios": "fotosensibilidad, dispepsia", "indicaciones": "acné, infecciones respiratorias", "rango_edad": "Adultos y niños mayores de 8 años", "estado_medicamento": "disponible"},
    {"nombre": "Eritromicina 500mg", "descripcion": "Antibiótico macrólido de primera generación.", "composicion": "Eritromicina estolato 500mg", "sintomas_secundarios": "colestasis, náuseas", "indicaciones": "infecciones respiratorias", "rango_edad": "Adultos y niños mayores de 6 meses", "estado_medicamento": "disponible"},
    {"nombre": "Claritromicina 500mg", "descripcion": "Macrólido de segunda generación.", "composicion": "Claritromicina 500mg", "sintomas_secundarios": "sabor metálico, diarrea", "indicaciones": "infecciones de piel", "rango_edad": "Adultos y niños mayores de 6 años", "estado_medicamento": "disponible"},
    {"nombre": "Terapia esteroidal oral varia según paciente", "descripcion": "Protocolos variados según patología.", "composicion": "Dosis ajustada de corticoides", "sintomas_secundarios": "variable", "indicaciones": "condiciones inflamatorias graves", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Fenacetina Pura", "descripcion": "Analgésico antiguo, retirado del mercado.", "composicion": "Fenacetina", "sintomas_secundarios": "Nefropatía, carcinogenicidad", "indicaciones": "Ya no se usa", "rango_edad": "N/A", "estado_medicamento": "discontinuado"},
    {"nombre": "Levotiroxina 50mcg", "descripcion": "Hormona tiroidea sintética.", "composicion": "Levotiroxina sódica 50mcg", "sintomas_secundarios": "palpitaciones, pérdida de peso", "indicaciones": "Hipotiroidismo", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Pregabalina 75mg", "descripcion": "Análogo del GABA.", "composicion": "Pregabalina 75mg", "sintomas_secundarios": "mareo, somnolencia", "indicaciones": "Dolor neuropático, fibromialgia, epilepsia", "rango_edad": "Adultos", "estado_medicamento": "disponible"},
    {"nombre": "Vitamina D3 1000UI", "descripcion": "Suplemento de vitamina D.", "composicion": "Colecalciferol 1000 UI", "sintomas_secundarios": "Hipercalcemia (en sobredosis)", "indicaciones": "Deficiencia de vitamina D", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"},
    {"nombre": "Hierro Fumarato 200mg", "descripcion": "Suplemento de hierro.", "composicion": "Fumarato ferroso 200mg", "sintomas_secundarios": "Estreñimiento, heces oscuras", "indicaciones": "Anemia ferropénica", "rango_edad": "Todas las edades", "estado_medicamento": "disponible"}
]

# Lista de usuarios de Oracle proporcionados
oracle_users_data = [
    {"username": "ACEVEDO", "email": "acevedobrian499@gmail.com"},
    {"username": "ALVEAR", "email": "eineralvear77@gmail.com"},
    {"username": "AMADO", "email": "brayanamadoitg7c@gmail.com"},
    {"username": "CARRILLO", "email": "jusecare015@gmail.com"},
    {"username": "ESCAMILLA", "email": "carlosescamilla2023@gmail.com"},
    {"username": "FAJARDO", "email": "xiomystefanny27@gmail.com"},
    {"username": "GUERRERO", "email": "yarlyguerrero17@gmail.com"},
    {"username": "HERNÁNDEZ", "email": "jersahercal1904@gmail.com"},
    {"username": "MARQUEZ", "email": "marquezkevin467@gmail.com"},
    {"username": "OCHOA", "email": "juancamiloochoajaimes1@gmail.com"},
    {"username": "PULIDO", "email": "pulidojulian00@gmail.com"},
    {"username": "RODRIGUEZ", "email": "dfra0512@outlook.com"},
    {"username": "ROJASC", "email": "carlosrojascubides10a@gmail.com"},
    {"username": "ROJASK", "email": "sauremk30@gmail.com"},
    {"username": "ROLON", "email": "jorgesebastianrolonmarquez@gmail.com"},
    {"username": "VELANDIA", "email": "sovelandiap2005@gmail.com"},
    {"username": "VERA", "email": "osmarandresvera@gmail.com"},
    {"username": "VERGARA", "email": "geronjose20@gmail.com"},
    {"username": "VILLAMIZAR", "email": "dani3lsu4rez@gmail.com"},
]

dosis_ejemplos = ["1 comprimido", "2 tabletas", "10 mg", "5 ml", "1 cápsula", "1 aplicación"]
frecuencia_ejemplos = ["Cada 8 horas", "Una vez al día", "Cada 12 horas", "Antes de dormir", "Con cada comida", "Cada 6 horas", "Dos veces al día"]
alert_states = ["activa", "inactiva", "completada"]


def get_db_connection():
    conn = psycopg2.connect(
        host=PG_HOST,
        database=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        port=PG_PORT
    )
    conn.set_client_encoding('UTF8')
    return conn

def limpiar_tablas(conn):
    cur = conn.cursor()
    print("Limpiando datos existentes de las tablas...")
    try:
        # El orden es importante para respetar las restricciones de clave externa (FK)
        # Suponiendo que alertas depende de usuarios y medicamentos
        # Y que auditoria puede depender de usuarios (aunque no haya FK estricta en el DDL proporcionado)
        
        cur.execute("DELETE FROM alertas;")
        print("  - Datos de 'alertas' eliminados.")
        
        cur.execute("DELETE FROM auditoria;")
        print("  - Datos de 'auditoria' eliminados.")

        cur.execute("DELETE FROM reportes_log;")
        print("  - Datos de 'reportes_log' eliminados.")
        
        cur.execute("DELETE FROM medicamentos;")
        print("  - Datos de 'medicamentos' eliminados.")

        # Antes de eliminar usuarios, se debe asegurar que no haya referencias.
        # Si 'eps_id' en 'usuarios' tiene ON DELETE SET NULL, no hay problema para eliminar usuarios antes de EPS.
        cur.execute("DELETE FROM usuarios;")
        print("  - Datos de 'usuarios' eliminados.")
        
        cur.execute("DELETE FROM eps;") # NUEVO: Limpiar EPS
        print("  - Datos de 'eps' eliminados.")
        
        conn.commit()
        print("Limpieza de tablas completada.")
    except psycopg2.Error as e:
        print(f"Error durante la limpieza de tablas: {e}")
        conn.rollback()
        raise # Relanzar para detener la ejecución si la limpieza falla críticamente
    finally:
        cur.close()

def insertar_eps_lote(conn, eps_a_insertar):
    cur = conn.cursor()
    print(f"Insertando {len(eps_a_insertar)} EPS...")
    sql_insert_eps = """
        INSERT INTO eps (nombre, nit)
        VALUES (%s, %s)
        ON CONFLICT (nombre) DO NOTHING;
    """
    for eps in eps_a_insertar:
        try:
            cur.execute(sql_insert_eps, (eps['nombre'], eps['nit']))
        except psycopg2.Error as e:
            print(f"Error al insertar EPS {eps['nombre']}: {e}")
            conn.rollback()
    conn.commit()
    print("Inserción de EPS completada.")
    cur.close()

# Modificación: Ahora acepta 'eps_id_to_assign'
def insertar_usuarios_lote(conn, usuarios_a_insertar):
    cur = conn.cursor()
    print(f"Intentando insertar {len(usuarios_a_insertar)} usuarios...")
    # Ajusta la sentencia SQL para incluir los nuevos campos, incluyendo eps_id
    sql_insert_usuario = """
        INSERT INTO usuarios (
            nombre, cedula, email, contrasena, rol, estado_usuario,
            fecha_nacimiento, telefono, ciudad, fecha_registro, eps_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (cedula) DO NOTHING; 
    """
    for usuario in usuarios_a_insertar:
        try:
            cur.execute(
                sql_insert_usuario,
                (
                    usuario['nombre'], usuario['cedula'], usuario['email'], 
                    usuario['contrasena'], usuario['rol'], usuario['estado_usuario'],
                    usuario.get('fecha_nacimiento'), 
                    usuario.get('telefono'),
                    usuario.get('ciudad'),
                    usuario.get('fecha_registro'),
                    usuario.get('eps_id') # NUEVO: Campo eps_id
                )
            )
        except psycopg2.Error as e:
            print(f"Error al insertar usuario {usuario.get('cedula', 'Desconocido')}: {e}")
            conn.rollback() 
    conn.commit()
    print(f"Inserción de lote de usuarios completada.")
    cur.close()

def insertar_medicamentos_lote(conn, medicamentos_a_insertar):
    cur = conn.cursor()
    print(f"Intentando insertar/actualizar {len(medicamentos_a_insertar)} medicamentos...")
    for med in medicamentos_a_insertar:
        try:
            cleaned_med = {k: v.replace('\u00A0', ' ') if isinstance(v, str) else v for k, v in med.items()}
            cur.execute("""
                INSERT INTO medicamentos (
                    nombre, descripcion, composicion, sintomas_secundarios,
                    indicaciones, rango_edad, estado_medicamento
                )
                VALUES (
                    %(nombre)s, %(descripcion)s, %(composicion)s, %(sintomas_secundarios)s,
                    %(indicaciones)s, %(rango_edad)s, %(estado_medicamento)s
                )
                ON CONFLICT (nombre) DO NOTHING;
            """, cleaned_med)
        except psycopg2.Error as e:
            print(f"Error al insertar medicamento {med['nombre']}: {e}")
            conn.rollback()
    conn.commit()
    print("Inserción de lote de medicamentos completada.")
    cur.close()

def insertar_alertas_lote(conn, num_alertas):
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM usuarios WHERE rol = 'cliente' AND estado_usuario = 'activo'")
    cliente_ids = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT id FROM medicamentos WHERE estado_medicamento = 'disponible'")
    medicamento_ids = [row[0] for row in cur.fetchall()]

    cur.execute("SELECT id FROM usuarios WHERE rol = 'admin' LIMIT 1") # Obtener ID del admin para asignado_por
    admin_row = cur.fetchone()
    admin_id = admin_row[0] if admin_row else None # Acceder por índice ya que no es RealDictCursor

    if not cliente_ids or not medicamento_ids or admin_id is None:
        print("No hay suficientes clientes activos, medicamentos disponibles o administradores para crear alertas.")
        cur.close()
        return

    print(f"Intentando insertar {num_alertas} alertas...")
    alertas_insertadas = 0
    for i in range(num_alertas):
        try:
            usuario_id = random.choice(cliente_ids)
            medicamento_id = random.choice(medicamento_ids)
            dosis = random.choice(dosis_ejemplos)
            frecuencia = random.choice(frecuencia_ejemplos)
            
            start_date_obj = datetime.now() + timedelta(days=random.randint(-10, 10))
            fecha_inicio = start_date_obj.strftime('%Y-%m-%d')
            
            fecha_fin_val = None
            if random.choice([True, False]): 
                fecha_fin_obj = start_date_obj + timedelta(days=random.randint(7, 90))
                fecha_fin_val = fecha_fin_obj.strftime('%Y-%m-%d')
            
            hora_preferida_val = None
            if random.choice([True, False]): 
                hora_preferida_val = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:00"
            
            estado = random.choice(alert_states)
            if estado == "completada":
                 # Adjust dates for 'completada' state to ensure fecha_fin is in the past and after fecha_inicio
                 if start_date_obj.date() >= date.today(): # If start is today or future, make it past
                     start_date_obj = datetime.now() - timedelta(days=random.randint(10,20))
                     fecha_inicio = start_date_obj.strftime('%Y-%m-%d')
                 
                 # Ensure end_date is after start_date but in the past
                 fecha_fin_obj = start_date_obj + timedelta(days=random.randint(1,5))
                 if fecha_fin_obj.date() >= date.today():
                     fecha_fin_obj = datetime.now() - timedelta(days=1)
                     # Final check to ensure fecha_fin is not before fecha_inicio
                     if fecha_fin_obj.date() < start_date_obj.date():
                         fecha_fin_obj = start_date_obj + timedelta(days=1)
                 fecha_fin_val = fecha_fin_obj.strftime('%Y-%m-%d')


            cur.execute(
                """
                INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, asignado_por_usuario_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin_val, hora_preferida_val, estado, admin_id)
            )
            alertas_insertadas +=1
        except psycopg2.Error as e:
            print(f"Error al insertar alerta: {e}")
            conn.rollback() 
    
    conn.commit()
    print(f"{alertas_insertadas} alertas insertadas.")
    cur.close()

def generar_fecha_nacimiento_realista(edad_min=18, edad_max=80):
    """Genera una fecha de nacimiento aleatoria para alguien entre edad_min y edad_max años."""
    hoy = date.today()
    año_nacimiento = hoy.year - random.randint(edad_min, edad_max)
    mes_nacimiento = random.randint(1, 12)
    dia_nacimiento = random.randint(1, 28 if mes_nacimiento == 2 else 30 if mes_nacimiento in [4, 6, 9, 11] else 31)
    return date(año_nacimiento, mes_nacimiento, dia_nacimiento)

def generar_numero_telefono_colombiano(ciudad_info):
    """Genera un número de teléfono colombiano (celular o fijo basado en ciudad)."""
    if random.choice([True, False, True]):  # Mayor probabilidad para celular
        prefijo = random.choice(ciudad_info['prefijos_celular'])
        numero = prefijo + str(random.randint(1000000, 9999999))
    else:  # Fijo
        numero = ciudad_info['indicativo_fijo'] + str(random.randint(1000000, 9999999))
    return numero

def main():
    conn = None
    try:
        conn = get_db_connection()
        print("Conexión a la base de datos establecida.")
        limpiar_tablas(conn)

        # --- Insertar EPS ---
        lista_eps_colombia = [
            {"nombre": "Nueva EPS", "nit": "8301086054"},
            {"nombre": "Sura EPS", "nit": "8909031357"},
            {"nombre": "Sanitas EPS", "nit": "8605136814"},
            {"nombre": "Compensar EPS", "nit": "8600667017"},
            {"nombre": "Coosalud EPS", "nit": "8002047247"},
            {"nombre": "Salud Total EPS", "nit": "8001021464"},
            {"nombre": "Famisanar EPS", "nit": "8605330366"},
            {"nombre": "Aliansalud EPS", "nit": "8300262108"},
            {"nombre": "EPM Salud", "nit": "8110000632"},
            {"nombre": "SaludMia EPS", "nit": "9009848521"}
        ]
        insertar_eps_lote(conn, lista_eps_colombia)

        # Obtener IDs de EPS para asignarlos a los usuarios
        cur = conn.cursor()
        cur.execute("SELECT id FROM eps WHERE estado = 'activo'")
        eps_ids = [row[0] for row in cur.fetchall()]
        cur.close()

        if not eps_ids:
            print("Advertencia: No hay EPS disponibles para asignar a los clientes. Asegúrate de que las EPS se inserten primero.")
            # Si no hay EPS, los clientes se insertarán con eps_id = NULL

        # --- Generar e Insertar Administradores ---
        admins_a_insertar = []
        admins_a_insertar.append({
            'nombre': "Brian Acevedo",
            'cedula': "1092526700",
            'email': "admin@medialert.co",
            'contrasena': generate_password_hash("a0416g", method='pbkdf2:sha256'),
            'rol': 'admin',
            'estado_usuario': 'activo',
            'fecha_nacimiento': generar_fecha_nacimiento_realista(25, 40), # Admin típico en este rango de edad
            'telefono': generar_numero_telefono_colombiano(random.choice(list(ciudades_colombia.values()))), # Random city for admin
            'ciudad': random.choice(list(ciudades_colombia.keys())),
            'fecha_registro': datetime.now().strftime('%Y-%m-%d'),
            'eps_id': random.choice(eps_ids) if eps_ids else None # Asignar EPS al admin también
        })
        # Más admins aleatorios
        for i in range(5):
            nombre_admin = random.choice(first_names_male + first_names_female)
            apellido_admin = random.choice(last_names)
            cedula_admin = f"ADM{random.randint(10000, 99999)}" # Cédulas para admins pueden ser diferentes
            email_admin = f"admin{nombre_admin.lower().replace(' ', '')}{apellido_admin.lower().replace(' ', '')}{random.randint(1,99)}@{random.choice(dominios_email)}"
            ciudad_admin_nombre, ciudad_data_admin = random.choice(list(ciudades_colombia.items()))
            admins_a_insertar.append({
                'nombre': f"{nombre_admin} {apellido_admin}",
                'cedula': cedula_admin,
                'email': email_admin,
                'contrasena': hashed_common_pass,
                'rol': 'admin',
                'estado_usuario': 'activo',
                'fecha_nacimiento': generar_fecha_nacimiento_realista(30, 60),
                'telefono': generar_numero_telefono_colombiano(ciudad_data_admin),
                'ciudad': ciudad_admin_nombre,
                'fecha_registro': (datetime.now() - timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
                'eps_id': random.choice(eps_ids) if eps_ids else None
            })
        insertar_usuarios_lote(conn, admins_a_insertar)

        # --- Generar e Insertar Clientes (adicionales a los de Oracle) ---
        clientes_a_insertar = []
        for i in range(1, 151): # Generar 150 clientes aleatorios
            nombre_base = random.choice(all_first_names)
            apellido1 = random.choice(last_names)
            apellido2 = random.choice(last_names)
            nombre_cliente = f"{nombre_base} {apellido1}"
            if random.choice([True, False]): # 50% de probabilidad de tener segundo apellido
                nombre_cliente += f" {apellido2}"
            
            cedula_cliente = str(random.randint(100000000, 1999999999)) # Generar número de 9 o 10 dígitos

            # Asegurar email único y válido
            email_base = nombre_base.lower().replace(' ', '')
            email_apellido = apellido1.lower().replace(' ', '')
            email_cliente = f"{email_base}{email_apellido}{random.randint(1,999)}@{random.choice(dominios_email)}"

            fecha_registro_dt = datetime.now() - timedelta(days=random.randint(0, 3*365))
            estado_cliente = random.choices(['activo', 'inactivo'], weights=[0.9, 0.1], k=1)[0]
            fecha_nacimiento_cliente = generar_fecha_nacimiento_realista()
            ciudad_nombre, ciudad_data = random.choice(list(ciudades_colombia.items()))
            telefono_cliente = generar_numero_telefono_colombiano(ciudad_data)
            eps_id_cliente = random.choice(eps_ids) if eps_ids else None

            clientes_a_insertar.append({
                'nombre': nombre_cliente,
                'cedula': cedula_cliente,
                'email': email_cliente,
                'contrasena': hashed_common_pass,
                'rol': 'cliente',
                'estado_usuario': estado_cliente,
                'fecha_nacimiento': fecha_nacimiento_cliente.strftime('%Y-%m-%d'),
                'telefono': telefono_cliente,
                'ciudad': ciudad_nombre,
                'fecha_registro': fecha_registro_dt.strftime('%Y-%m-%d'),
                'eps_id': eps_id_cliente
            })
        insertar_usuarios_lote(conn, clientes_a_insertar)

        # --- Insertar Usuarios de Oracle ---
        print(f"Insertando {len(oracle_users_data)} usuarios del archivo Oracle...")
        oracle_clients_to_insert = []
        for user_data in oracle_users_data:
            username = user_data['username'].strip().title() # Apellido con primera letra mayúscula
            email = user_data['email'].strip()
            
            # Intenta extraer el nombre del correo de forma más robusta
            local_part = email.split('@')[0]
            # Eliminar caracteres no alfabéticos y números del inicio/fin para aislar nombres/apellidos
            clean_local_part = ''.join(filter(str.isalpha, local_part)).lower()
            
            first_name_inferred = ""
            # Buscar nombres comunes en el email (heurístico)
            for fname in all_first_names:
                if fname.lower() in clean_local_part:
                    # Si encontramos un nombre, lo tomamos como el primer nombre
                    first_name_inferred = fname
                    break
            
            if not first_name_inferred: # Fallback si no se pudo inferir un nombre común
                # Intentar tomar la primera parte alfabética del email que no sea el username
                parts = re.findall(r'[a-zA-Z]+', local_part)
                if parts:
                    for part in parts:
                        if part.lower() not in username.lower(): # Si no es el username (apellido)
                            first_name_inferred = part.title()
                            break
                if not first_name_inferred: # Último recurso: usar un nombre aleatorio
                    first_name_inferred = random.choice(all_first_names)
            
            full_name = f"{first_name_inferred} {username}" # Nombre y luego el apellido
            
            # Generar cédula aleatoria para estos usuarios
            cedula_oracle = str(random.randint(100000000, 1999999999))

            fecha_registro_dt = datetime.now() - timedelta(days=random.randint(0, 3*365))
            estado_cliente = random.choices(['activo', 'inactivo'], weights=[0.95, 0.05], k=1)[0] # Más probabilidad de activo
            fecha_nacimiento_cliente = generar_fecha_nacimiento_realista()
            ciudad_nombre, ciudad_data = random.choice(list(ciudades_colombia.items()))
            telefono_cliente = generar_numero_telefono_colombiano(ciudad_data)
            eps_id_cliente = random.choice(eps_ids) if eps_ids else None

            oracle_clients_to_insert.append({
                'nombre': full_name,
                'cedula': cedula_oracle,
                'email': email,
                'contrasena': hashed_common_pass, # Usar contraseña genérica
                'rol': 'cliente',
                'estado_usuario': estado_cliente,
                'fecha_nacimiento': fecha_nacimiento_cliente.strftime('%Y-%m-%d'),
                'telefono': telefono_cliente,
                'ciudad': ciudad_nombre,
                'fecha_registro': fecha_registro_dt.strftime('%Y-%m-%d'),
                'eps_id': eps_id_cliente
            })
        insertar_usuarios_lote(conn, oracle_clients_to_insert)

        # --- Insertar Medicamentos ---
        insertar_medicamentos_lote(conn, lista_medicamentos_a_insertar)
        
        # --- Insertar Alertas ---
        insertar_alertas_lote(conn, 300) 

        print("\nProceso de población de base de datos finalizado con éxito.")

    except psycopg2.OperationalError as e:
        print(f"\nError operacional de PostgreSQL: {e}")
    except psycopg2.Error as e:
        print(f"\nOcurrió un error de PostgreSQL durante la población: {e}")
        if conn: conn.rollback()
    except Exception as e:
        print(f"\nOcurrió un error general inesperado: {e}")
        # Asegúrate de imprimir el error completo para depuración
        import traceback
        traceback.print_exc() # Esto imprimirá el stack trace completo
        if conn: conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    print("Iniciando el script para poblar la base de datos MediAlert...")
    if not all([PG_HOST, PG_DB, PG_USER, PG_PASS]):
        print("Error: Faltan variables de entorno para la conexión a la base de datos (PG_HOST, PG_DB, PG_USER, PG_PASS).")
        print("Asegúrate de tener un archivo .env configurado o las variables exportadas.")
    else:
        main()
    print("Script de población finalizado.")