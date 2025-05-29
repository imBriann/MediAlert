import psycopg2
import os

# --- Configuración de la Conexión a la Base de Datos ---
PG_HOST = 'localhost'
PG_DB = 'medialert'
PG_USER = 'postgres'
PG_PASS = '0102'  # ¡Usa tu contraseña real aquí!
PG_PORT = '5432'

# --- Comandos SQL para crear la estructura de la base de datos ---
SQL_COMMANDS = """
-- Borra las tablas existentes para empezar de cero
DROP TABLE IF EXISTS reportes, alertas, medicamentos, usuarios CASCADE;

-- Tabla de Usuarios con roles, nombre y email
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(10) NOT NULL CHECK (rol IN ('admin', 'cliente'))
);

-- Tabla de Medicamentos con la restricción UNIQUE en el nombre
CREATE TABLE medicamentos (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) UNIQUE NOT NULL, -- <-- ¡AQUÍ ESTÁ LA CORRECCIÓN! AÑADIMOS UNIQUE.
    descripcion TEXT,
    composicion TEXT,
    sintomas_secundarios TEXT,
    indicaciones TEXT,
    rango_edad VARCHAR(50)
);

-- Tabla de Alertas: Conecta un usuario con un medicamento
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    medicamento_id INT NOT NULL REFERENCES medicamentos(id) ON DELETE CASCADE,
    dosis VARCHAR(100),
    frecuencia VARCHAR(100),
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    estado VARCHAR(20) DEFAULT 'activa'
);

-- Tabla de Reportes/Auditoría con referencia al usuario que realizó la acción
CREATE TABLE reportes (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMPTZ DEFAULT NOW(),
    accion VARCHAR(255),
    detalle TEXT,
    realizado_por INT REFERENCES usuarios(id)
);

-- Insertar un usuario administrador y un cliente de prueba para poder hacer login
INSERT INTO usuarios (nombre, cedula, email, contrasena, rol) VALUES
('Admin General', 'admin', 'admin@medialert.com', 'admin123', 'admin'),
('Juan Perez', '12345', 'juan.perez@email.com', 'cliente123', 'cliente');
"""

# --- Tu lista completa de 100 medicamentos ---
medicamentos = [
    {"nombre": "Paracetamol 500 mg",    "descripcion": "Analgésico y antipirético.",                      "composicion": "Paracetamol 500 mg",                        "sintomas_secundarios": "náuseas, hepatotoxicidad en sobredosis", "indicaciones": "fiebre, dolor leve a moderado", "rango_edad": "Todas las edades"},
    {"nombre": "Ibuprofeno 400 mg",     "descripcion": "Antiinflamatorio no esteroideo.",                  "composicion": "Ibuprofeno 400 mg",                         "sintomas_secundarios": "gastritis, dolor abdominal",                  "indicaciones": "dolor, inflamación, fiebre", "rango_edad": "Mayores de 6 meses"},
    {"nombre": "Aspirina 100 mg",       "descripcion": "Antiplaquetario y antiinflamatorio.",               "composicion": "Ácido acetilsalicílico 100 mg",             "sintomas_secundarios": "sangrado gastrointestinal",                  "indicaciones": "prevención trombosis, dolor leve", "rango_edad": "Adultos"},
    {"nombre": "Amoxicilina 500 mg",    "descripcion": "Antibiótico β-lactámico.",                           "composicion": "Amoxicilina trihidrato 500 mg",             "sintomas_secundarios": "diarrea, candidiasis",                       "indicaciones": "infecciones respiratorias, urinarias", "rango_edad": "Todas las edades"},
    {"nombre": "Azitromicina 500 mg",   "descripcion": "Antibiótico macrólido.",                              "composicion": "Azitromicina dihidrato 500 mg",             "sintomas_secundarios": "dolor abdominal, diarrea",                    "indicaciones": "infecciones respiratorias, otitis", "rango_edad": "Adultos y niños mayores de 6 meses"},
    {"nombre": "Ciprofloxacino 500 mg", "descripcion": "Antibiótico fluoroquinolónico.",                      "composicion": "Ciprofloxacino clorhidrato 500 mg",         "sintomas_secundarios": "tendinitis, fotosensibilidad",               "indicaciones": "ITU, gastroenteritis", "rango_edad": "Adultos y niños mayores de 18 años"},
    {"nombre": "Metformina 850 mg",     "descripcion": "Antidiabético oral, biguanida.",                      "composicion": "Metformina clorhidrato 850 mg",             "sintomas_secundarios": "diarrea, acidosis láctica (raro)",           "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos"},
    {"nombre": "Atorvastatina 20 mg",   "descripcion": "Reductor de lípidos, estatina.",                      "composicion": "Atorvastatina cálcica 20 mg",               "sintomas_secundarios": "mialgias, elevación de transaminasas",       "indicaciones": "hipercolesterolemia", "rango_edad": "Adultos"},
    {"nombre": "Omeprazol 20 mg",       "descripcion": "Inhibidor de bomba de protones.",                     "composicion": "Omeprazol 20 mg",                           "sintomas_secundarios": "dolor de cabeza, diarrea",                   "indicaciones": "reflujo gastroesofágico, úlcera péptica", "rango_edad": "Adultos y niños mayores de 1 año"},
    {"nombre": "Ranitidina 150 mg",     "descripcion": "Antagonista H₂, reduce producción de ácido.",          "composicion": "Ranitidina 150 mg",                         "sintomas_secundarios": "constipación, somnolencia",                  "indicaciones": "úlcera gástrica, reflujo", "rango_edad": "Adultos y niños mayores de 12 años"},
    {"nombre": "Loratadina 10 mg",      "descripcion": "Antihistamínico H₁ de segunda generación.",            "composicion": "Loratadina 10 mg",                          "sintomas_secundarios": "cefalea, somnolencia (raro)",                "indicaciones": "alergias, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Cetirizina 10 mg",      "descripcion": "Antihistamínico H₁ de segunda generación.",            "composicion": "Cetirizina 10 mg",                          "sintomas_secundarios": "somnolencia, boca seca",                      "indicaciones": "urticaria, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 6 años"},
    {"nombre": "Salbutamol 100 mcg",     "descripcion": "Broncodilatador β₂ agonista de acción corta.",         "composicion": "Salbutamol sulfato 100 mcg por dosis",       "sintomas_secundarios": "temblor, taquicardia",                        "indicaciones": "asma, EPOC", "rango_edad": "Todas las edades"},
    {"nombre": "Prednisona 5 mg",       "descripcion": "Corticosteroide oral de acción intermedia.",           "composicion": "Prednisona 5 mg",                          "sintomas_secundarios": "aumento de peso, hipertensión",              "indicaciones": "inflamación, alergias severas", "rango_edad": "Adultos"},
    {"nombre": "Metoclopramida 10 mg",  "descripcion": "Procinético y antiemético.",                           "composicion": "Metoclopramida 10 mg",                     "sintomas_secundarios": "somnolencia, espasmos musculares",           "indicaciones": "náuseas, gastroparesia", "rango_edad": "Adultos y niños mayores de 1 año"},
    {"nombre": "Omeprazol 40 mg",       "descripcion": "IBP para tratamiento de úlceras más severas.",          "composicion": "Omeprazol 40 mg",                           "sintomas_secundarios": "insomnio, mareo",                            "indicaciones": "síndrome de Zollinger-Ellison", "rango_edad": "Adultos"},
    {"nombre": "Naproxeno 500 mg",      "descripcion": "AINE de larga acción.",                                "composicion": "Naproxeno 500 mg",                         "sintomas_secundarios": "ulceración GI, retención de líquidos",        "indicaciones": "artritis, dolor crónico", "rango_edad": "Adultos y niños mayores de 12 años"},
    {"nombre": "Clonazepam 0.5 mg",     "descripcion": "Benzodiacepina de acción prolongada.",                  "composicion": "Clonazepam 0.5 mg",                       "sintomas_secundarios": "somnolencia, dependencia",                   "indicaciones": "ansiedad, epilepsia", "rango_edad": "Adultos y niños mayores de 18 años"},
    {"nombre": "Diazepam 10 mg",        "descripcion": "Benzodiacepina de acción larga.",                      "composicion": "Diazepam 10 mg",                          "sintomas_secundarios": "sedación, ataxia",                           "indicaciones": "ansiedad, espasmos musculares", "rango_edad": "Adultos y niños mayores de 12 años"},
    {"nombre": "Tramadol 50 mg",        "descripcion": "Analgesico opioide de moderada potencia.",              "composicion": "Tramadol clorhidrato 50 mg",               "sintomas_secundarios": "mareo, náuseas",                             "indicaciones": "dolor moderado a severo", "rango_edad": "Adultos"},
    {"nombre": "Codeína 30 mg",         "descripcion": "Opioide leve, antitúsivo ocasional.",                   "composicion": "Codeína fosfato 30 mg",                    "sintomas_secundarios": "estreñimiento, somnolencia",                "indicaciones": "dolor leve, tos seca", "rango_edad": "Adultos y niños mayores de 12 años"},
    {"nombre": "Metamizol 575 mg",      "descripcion": "Analgésico y antipirético no opioide.",                 "composicion": "Metamizol sódico 575 mg",                  "sintomas_secundarios": "agranulocitosis (raro), hipotensión",        "indicaciones": "dolor agudo, fiebre alta", "rango_edad": "Adultos y niños mayores de 3 meses"},
    {"nombre": "Ondansetrón 4 mg",      "descripcion": "Antiemético 5-HT₃ receptor antagonista.",               "composicion": "Ondansetrón 4 mg",                        "sintomas_secundarios": "estreñimiento, cefalea",                    "indicaciones": "náuseas por quimioterapia", "rango_edad": "Adultos y niños mayores de 6 meses"},
    {"nombre": "Fluconazol 150 mg",     "descripcion": "Antifúngico azólico de amplio espectro.",              "composicion": "Fluconazol 150 mg",                       "sintomas_secundarios": "náuseas, hepatotoxicidad",                   "indicaciones": "candidiasis vaginal", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Ketoconazol 200 mg",    "descripcion": "Antifúngico azólico sistémico.",                       "composicion": "Ketoconazol 200 mg",                      "sintomas_secundarios": "alteraciones hepáticas",                    "indicaciones": "dermatofitosis, candidiasis", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Metronidazol 500 mg",   "descripcion": "Antibacteriano y antiprotozoario nitroimidazol.",       "composicion": "Metronidazol 500 mg",                     "sintomas_secundarios": "sabor metálico, neuropatía periferica",      "indicaciones": "infecciones anaerobias, giardiasis", "rango_edad": "Adultos y niños mayores de 3 años"},
    {"nombre": "Clindamicina 300 mg",   "descripcion": "Antibiótico lincosamida.",                              "composicion": "Clindamicina fosfato 300 mg",              "sintomas_secundarios": "colitis pseudomembranosa",                  "indicaciones": "infecciones de piel, hueso", "rango_edad": "Adultos y niños mayores de 1 año"},
    {"nombre": "Enalapril 10 mg",       "descripcion": "IECA para hipertensión.",                              "composicion": "Enalapril maleato 10 mg",                  "sintomas_secundarios": "tos seca, hipotensión",                      "indicaciones": "hipertensión, IC", "rango_edad": "Adultos"},
    {"nombre": "Losartán 50 mg",        "descripcion": "ARA‑II para hipertensión.",                             "composicion": "Losartán potásico 50 mg",                 "sintomas_secundarios": "mareo, hiperkalemia",                        "indicaciones": "hipertensión, nefropatía diabética", "rango_edad": "Adultos"},
    {"nombre": "Amlodipino 5 mg",       "descripcion": "Bloqueador de canales de calcio dihidropiridínico.",    "composicion": "Amlodipino besilato 5 mg",                "sintomas_secundarios": "edema periférico, cefalea",                "indicaciones": "hipertensión, angina", "rango_edad": "Adultos y niños mayores de 6 años"},
    {"nombre": "Metoprolol 50 mg",      "descripcion": "Betabloqueador cardioselectivo.",                       "composicion": "Metoprolol tartrato 50 mg",               "sintomas_secundarios": "bradicardia, fatiga",                       "indicaciones": "hipertensión, angina", "rango_edad": "Adultos"},
    {"nombre": "Propanolol 40 mg",      "descripcion": "Betabloqueador no selectivo.",                          "composicion": "Propanolol 40 mg",                         "sintomas_secundarios": "broncoespasmo, fatiga",                     "indicaciones": "hipertensión, temblor esencial", "rango_edad": "Adultos"},
    {"nombre": "Hidroclorotiazida 25 mg","descripcion": "Diurético tiazídico.",                                 "composicion": "Hidroclorotiazida 25 mg",                 "sintomas_secundarios": "hipopotasemia, hiponatremia",              "indicaciones": "hipertensión", "rango_edad": "Adultos"},
    {"nombre": "Furosemida 40 mg",      "descripcion": "Diurético de asa.",                                     "composicion": "Furosemida 40 mg",                         "sintomas_secundarios": "deshidratación, ototoxicidad (raro)",       "indicaciones": "edema, IC", "rango_edad": "Adultos y niños mayores de 18 años"},
    {"nombre": "Espironolactona 25 mg", "descripcion": "Diurético ahorrador de potasio.",                       "composicion": "Espironolactona 25 mg",                   "sintomas_secundarios": "hiperkalemia, ginecomastia",               "indicaciones": "cirrosis, IC", "rango_edad": "Adultos"},
    {"nombre": "Warfarina 5 mg",        "descripcion": "Anticoagulante cumarínico.",                           "composicion": "Warfarina sódica 5 mg",                   "sintomas_secundarios": "hemorragias, necrosis cutánea",            "indicaciones": "trombosis, fibrilación auricular", "rango_edad": "Adultos"},
    {"nombre": "Heparina sódica 5 000 UI","descripcion": "Anticoagulante de acción inmediata.",                 "composicion": "Heparina sódica 5 000 UI/ml",             "sintomas_secundarios": "trombocitopenia, hemorragia",               "indicaciones": "profilaxis trombótica", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Enoxaparina 40 mg",     "descripcion": "HBPM para anticoagulación subcutánea.",                 "composicion": "Enoxaparina sódica 40 mg",                "sintomas_secundarios": "trombocitopenia, hemorragia",               "indicaciones": "trombosis venosa profunda", "rango_edad": "Adultos"},
    {"nombre": "Clopidogrel 75 mg",     "descripcion": "Inhibidor de P2Y₁₂, antiplaquetario.",                  "composicion": "Clopidogrel 75 mg",                       "sintomas_secundarios": "sangrado, dispepsia",                        "indicaciones": "síndrome coronario agudo", "rango_edad": "Adultos"},
    {"nombre": "Simvastatina 20 mg",    "descripcion": "Estatina para reducción de colesterol LDL.",            "composicion": "Simvastatina 20 mg",                      "sintomas_secundarios": "mialgias, elevación de enzimas hepáticas",  "indicaciones": "dislipidemia", "rango_edad": "Adultos"},
    {"nombre": "Fenofibrato 145 mg",    "descripcion": "Fibrato para reducción de triglicéridos.",              "composicion": "Fenofibrato 145 mg",                      "sintomas_secundarios": "dispepsia, mialgias",                        "indicaciones": "hipertrigliceridemia", "rango_edad": "Adultos"},
    {"nombre": "Pantoprazol 40 mg",     "descripcion": "IBP para mantenimiento de reflujo.",                    "composicion": "Pantoprazol sódico 40 mg",                "sintomas_secundarios": "cefalea, diarrea",                          "indicaciones": "ERGE, úlcera péptica", "rango_edad": "Adultos y niños mayores de 1 año"},
    {"nombre": "Esomeprazol 40 mg",     "descripcion": "S‐isoforma de omeprazol, IBP.",                         "composicion": "Esomeprazol magnesio 40 mg",               "sintomas_secundarios": "mareo, flatulencia",                        "indicaciones": "ERGE", "rango_edad": "Adultos"},
    {"nombre": "Fexofenadina 180 mg",   "descripcion": "Antihistamínico H₁ no sedante.",                        "composicion": "Fexofenadina 180 mg",                     "sintomas_secundarios": "cefalea, náuseas",                          "indicaciones": "alergias estacionales", "rango_edad": "Adultos y niños mayores de 6 años"},
    {"nombre": "Montelukast 10 mg",     "descripcion": "Antileucotrieno para asma y rinoconjuntivitis.",        "composicion": "Montelukast sodio 10 mg",                 "sintomas_secundarios": "cefalea, dolor abdominal",                  "indicaciones": "asma, rinitis alérgica", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Budesonida 200 mcg",    "descripcion": "Corticosteroide inhalado.",                             "composicion": "Budesonida 200 mcg/dosis",                "sintomas_secundarios": "irritación orofaríngea",                    "indicaciones": "asma, EPOC", "rango_edad": "Adultos y niños mayores de 6 años"},
    {"nombre": "Beclometasona 100 mcg", "descripcion": "Corticosteroide nasal para alergias.",                  "composicion": "Beclometasona dipropionato 100 mcg",       "sintomas_secundarios": "irritación nasal",                           "indicaciones": "rinitis alérgica", "rango_edad": "Adultos y niños mayores de 6 años"},
    {"nombre": "Insulina glargina 100 UI/ml","descripcion": "Insulina basal de acción prolongada.",            "composicion": "Insulina glargina 100 UI/ml",             "sintomas_secundarios": "hipoglucemia, lipodistrofia",               "indicaciones": "diabetes tipo 1 y tipo 2", "rango_edad": "Adultos"},
    {"nombre": "Glimepirida 2 mg",      "descripcion": "Sulfonilurea para diabetes tipo 2.",                    "composicion": "Glimepirida 2 mg",                        "sintomas_secundarios": "hipoglucemia, aumento de peso",              "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos"},
    {"nombre": "Gliclazida 80 mg",      "descripcion": "Sulfonilurea de segunda generación.",                   "composicion": "Gliclazida 80 mg",                        "sintomas_secundarios": "hipoglucemia, náuseas",                      "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos"},
    {"nombre": "Sitagliptina 100 mg",   "descripcion": "Inhibidor de DPP‑4 para diabetes.",                     "composicion": "Sitagliptina fosfato sódico 100 mg",       "sintomas_secundarios": "cefalea, nasofaringitis",                    "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos"},
    {"nombre": "Empagliflozina 10 mg",  "descripcion": "Inhibidor de SGLT2 para diabetes.",                     "composicion": "Empagliflozina 10 mg",                    "sintomas_secundarios": "infecciones urinarias, poliuria",           "indicaciones": "diabetes tipo 2", "rango_edad": "Adultos"},
    {"nombre": "Sertralina 50 mg",      "descripcion": "ISRS para depresión y ansiedad.",                       "composicion": "Sertralina 50 mg",                        "sintomas_secundarios": "náuseas, insomnio",                          "indicaciones": "depresión, TOC", "rango_edad": "Adultos"},
    {"nombre": "Fluoxetina 20 mg",      "descripcion": "ISRS de larga vida media.",                             "composicion": "Fluoxetina 20 mg",                        "sintomas_secundarios": "insomnio, disfunción sexual",                "indicaciones": "depresión, bulimia nerviosa", "rango_edad": "Adultos"},
    {"nombre": "Citalopram 20 mg",      "descripcion": "ISRS para trastornos depresivos.",                      "composicion": "Citalopram hidrobromuro 20 mg",            "sintomas_secundarios": "mareo, fatiga",                            "indicaciones": "depresión", "rango_edad": "Adultos"},
    {"nombre": "Alprazolam 0.5 mg",     "descripcion": "Benzodiacepina de acción corta.",                       "composicion": "Alprazolam 0.5 mg",                       "sintomas_secundarios": "dependencia, sedación",                     "indicaciones": "ansiedad, pánico", "rango_edad": "Adultos"},
    {"nombre": "Haloperidol 5 mg",      "descripcion": "Antipsicótico típico de alta potencia.",                "composicion": "Haloperidol 5 mg",                        "sintomas_secundarios": "rigidez muscular, acatisia",               "indicaciones": "esquizofrenia, psicosis aguda", "rango_edad": "Adultos"},
    {"nombre": "Quetiapina 50 mg",      "descripcion": "Antipsicótico atípico.",                                "composicion": "Quetiapina fumarato 50 mg",               "sintomas_secundarios": "sedación, aumento de peso",                "indicaciones": "esquizofrenia, bipolaridad", "rango_edad": "Adultos"},
    {"nombre": "Topiramato 100 mg",     "descripcion": "Antiepiléptico y profilaxis de migraña.",               "composicion": "Topiramato 100 mg",                       "sintomas_secundarios": "mareo, pérdida de peso",                   "indicaciones": "epilepsia, migraña", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Sumatriptán 50 mg",     "descripcion": "Agonista 5-HT₁ para migraña.",                          "composicion": "Sumatriptán succinato 50 mg",             "sintomas_secundarios": "parestesias, sensación de opresión torácica","indicaciones": "migraña aguda", "rango_edad": "Adultos y niños mayores de 12 años"},
    {"nombre": "Aciclovir 400 mg",      "descripcion": "Antiviral inhibidor de ADN polimerasa.",                "composicion": "Aciclovir 400 mg",                        "sintomas_secundarios": "cefalea, náuseas",                          "indicaciones": "herpes labial, varicela", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Valaciclovir 500 mg",    "descripcion": "Profármaco de aciclovir con mejor biodisponibilidad.",    "composicion": "Valaciclovir 500 mg",                    "sintomas_secundarios": "dolor de cabeza, náuseas",                  "indicaciones": "herpes zóster", "rango_edad": "Adultos y niños mayores de 12 años"},
    {"nombre": "Oseltamivir 75 mg",     "descripcion": "Inhibidor de neuraminidasa para influenza.",             "composicion": "Oseltamivir fosfato 75 mg",               "sintomas_secundarios": "náuseas, vómitos",                           "indicaciones": "gripe A/B", "rango_edad": "Adultos y niños mayores de 1 año"},
    {"nombre": "Loperamida 2 mg",       "descripcion": "Antidiarreico opioide sin pasar BHE.",                  "composicion": "Loperamida 2 mg",                        "sintomas_secundarios": "estreñimiento, mareo",                      "indicaciones": "diarrea aguda", "rango_edad": "Adultos y niños mayores de 2 años"},
    {"nombre": "Lactulosa 10 g/15 ml",  "descripcion": "Laxante osmótico.",                                      "composicion": "Lactulosa 10 g por 15 ml",               "sintomas_secundarios": "flatulencia, dolor abdominal",             "indicaciones": "estreñimiento", "rango_edad": "Adultos y niños mayores de 1 año"},
    {"nombre": "Doxiciclina 100 mg",    "descripcion": "Antibiótico tetraciclina de amplio espectro.",           "composicion": "Doxiciclina 100 mg",                     "sintomas_secundarios": "fotosensibilidad, dispepsia",              "indicaciones": "acné, infecciones respiratorias", "rango_edad": "Adultos y niños mayores de 8 años"},
    {"nombre": "Eritromicina 500 mg",   "descripcion": "Antibiótico macrólido de primera generación.",            "composicion": "Eritromicina estolato 500 mg",            "sintomas_secundarios": "colestasis, náuseas",                        "indicaciones": "infecciones respiratorias", "rango_edad": "Adultos y niños mayores de 6 meses"},
    {"nombre": "Claritromicina 500 mg", "descripcion": "Macrólido de segunda generación.",                       "composicion": "Claritromicina 500 mg",                   "sintomas_secundarios": "sabor metálico, diarrea",                   "indicaciones": "infecciones de piel", "rango_edad": "Adultos y niños mayores de 6 años"},
    {"nombre": "Terapia esteroidal oral varia según paciente", "descripcion": "Protocolos variados según patología.", "composicion": "Dosis ajustada de corticoides",         "sintomas_secundarios": "variable",                                 "indicaciones": "condiciones inflamatorias graves", "rango_edad": "Adultos"},
    # … sigue completando hasta 100…
]


def inicializar_db():
    """Conecta a la base de datos, borra las tablas viejas, crea las nuevas e inserta los datos iniciales."""
    conn = None
    try:
        print("Conectando a la base de datos PostgreSQL...")
        conn = psycopg2.connect(
            host=PG_HOST,
            database=PG_DB,
            user=PG_USER,
            password=PG_PASS,
            port=PG_PORT
        )
        conn.set_client_encoding('UTF8')
        cur = conn.cursor()

        print("Creando la estructura de tablas...")
        cur.execute(SQL_COMMANDS)
        print("Estructura de tablas creada con éxito.")

        print(f"Insertando {len(medicamentos)} medicamentos en la base de datos...")
        for med in medicamentos:
            cur.execute("""
                INSERT INTO medicamentos (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad)
                VALUES (%(nombre)s, %(descripcion)s, %(composicion)s, %(sintomas_secundarios)s, %(indicaciones)s, %(rango_edad)s)
                ON CONFLICT (nombre) DO NOTHING;
            """, med)
        print("Medicamentos insertados con éxito.")

        conn.commit()
        
        print("\n¡Base de datos inicializada correctamente!")
        print("Se crearon un usuario 'admin' y un usuario 'cliente' de prueba.")

    except psycopg2.Error as e:
        print("\nOcurrió un error al inicializar la base de datos:")
        print(e)
    finally:
        if conn is not None:
            conn.close()
            print("Conexión a la base de datos cerrada.")

if __name__ == '__main__':
    inicializar_db()