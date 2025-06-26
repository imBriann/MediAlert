-- =====================================================================
-- Script para el Poblado Masivo y Completo de la Base de Datos MediAlert
-- Versión 3.0 - Contiene un conjunto de datos extenso y realista.
-- =====================================================================
-- Este script inserta datos iniciales y de prueba para todas las tablas.
-- Debe ejecutarse DESPUÉS de 'script_MediAlert.sql'.
-- =====================================================================

-- ** SECCIÓN 1: INSERCIÓN DE DATOS BASE (EPS Y MEDICAMENTOS) **

INSERT INTO eps (nombre, nit, logo_url, estado) VALUES
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
ON CONFLICT (nit) DO NOTHING;

INSERT INTO medicamentos (nombre, descripcion, composicion, sintomas_secundarios, indicaciones, rango_edad, estado_medicamento) VALUES
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
ON CONFLICT (nombre) DO NOTHING;


-- ** SECCIÓN 2: INSERCIÓN DE USUARIOS **
-- Contraseñas:
-- 'a0416g' para el admin 
-- 'password123' para todos los demás 

-- Usuario Administrador
INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario, fecha_nacimiento, telefono, ciudad, eps_id, tipo_regimen, genero) VALUES
('Brian Acevedo', '1092526700', 'admin@medialert.co', 'a0416g', 'admin', 'activo', '1990-04-16', '3101234567', 'Cúcuta', 1, 'Contributivo', 'Masculino')
ON CONFLICT (cedula) DO NOTHING;

-- Usuarios de la lista "Oracle"
INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario, fecha_nacimiento, telefono, ciudad, eps_id, tipo_regimen, genero) VALUES
('Einer Alvear', '1092526701', 'eineralvear77@gmail.com', '1234', 'cliente', 'activo', '1992-05-21', '3118765432', 'Bogotá D.C.', 2, 'Contributivo', 'Masculino'),
('Brayan Amado', '1092526702', 'brayanamadoitg7c@gmail.com', '1234', 'cliente', 'activo', '1995-03-15', '3123456789', 'Medellín', 3, 'Subsidiado', 'Masculino'),
('Juse Carrillo', '1092526703', 'jusecare015@gmail.com', '1234', 'cliente', 'activo', '1988-11-30', '3145678901', 'Cali', 4, 'Contributivo', 'Masculino'),
('Carlos Escamilla', '1092526704', 'carlosescamilla2023@gmail.com', '1234', 'cliente', 'inactivo', '2000-01-01', '3156789012', 'Barranquilla', 5, 'Contributivo', 'Masculino'),
('Xiomara Fajardo', '1092526705', 'xiomystefanny27@gmail.com', '1234', 'cliente', 'activo', '1999-07-07', '3167890123', 'Cartagena', 6, 'Especial', 'Femenino'),
('Yarly Guerrero', '1092526706', 'yarlyguerrero17@gmail.com', '1234', 'cliente', 'activo', '1998-02-14', '3178901234', 'Bucaramanga', 7, 'Contributivo', 'Femenino'),
('Jersain Hernández', '1092526707', 'jersahercal1904@gmail.com', '1234', 'cliente', 'activo', '1991-04-19', '3189012345', 'Pereira', 8, 'Subsidiado', 'Masculino'),
('Kevin Marquez', '1092526708', 'marquezkevin467@gmail.com', '1234', 'cliente', 'activo', '1996-10-25', '3190123456', 'Bogotá D.C.', 1, 'Contributivo', 'Masculino'),
('Juan Ochoa', '1092526709', 'juancamiloochoajaimes1@gmail.com', '1234', 'cliente', 'activo', '1993-06-12', '3201234567', 'Medellín', 2, 'Contributivo', 'Masculino'),
('Julian Pulido', '1092526710', 'pulidojulian00@gmail.com', '1234', 'cliente', 'activo', '1990-09-01', '3212345678', 'Cali', 3, 'Especial', 'Masculino'),
('Daniel Rodriguez', '1092526711', 'dfra0512@outlook.com', '1234', 'cliente', 'activo', '1987-12-05', '3223456789', 'Barranquilla', 4, 'Subsidiado', 'Masculino'),
('Carlos Rojas', '1092526712', 'carlosrojascubides10a@gmail.com', '1234', 'cliente', 'activo', '1994-07-20', '3234567890', 'Cartagena', 5, 'Contributivo', 'Masculino'),
('Kevin Rojas', '1092526713', 'sauremk30@gmail.com', '1234', 'cliente', 'activo', '1999-11-11', '3005678901', 'Bucaramanga', 6, 'Contributivo', 'Masculino'),
('Jorge Rolon', '1092526714', 'jorgesebastianrolonmarquez@gmail.com', '1234', 'cliente', 'activo', '1997-08-18', '3016789012', 'Cúcuta', 7, 'Especial', 'Masculino'),
('Sofia Velandia', '1092526715', 'sovelandiap2005@gmail.com', '1234', 'cliente', 'activo', '2005-01-20', '3027890123', 'Pereira', 8, 'Subsidiado', 'Femenino'),
('Osmar Vera', '1092526716', 'osmarandresvera@gmail.com', '1234', 'cliente', 'inactivo', '1985-05-25', '3038901234', 'Bogotá D.C.', 1, 'Contributivo', 'Masculino'),
('Geronimo Vergara', '1092526717', 'geronjose20@gmail.com', '1234', 'cliente', 'activo', '1992-02-28', '3049012345', 'Medellín', 2, 'Contributivo', 'Masculino'),
('Daniel Villamizar', '1092526718', 'dani3lsu4rez@gmail.com', '1234', 'cliente', 'activo', '1998-03-03', '3050123456', 'Cali', 3, 'Subsidiado', 'Masculino')
ON CONFLICT (cedula) DO NOTHING;

-- 100+ Usuarios Aleatorios Adicionales
INSERT INTO usuarios (nombre, cedula, email, contrasena, rol, estado_usuario, fecha_nacimiento, telefono, ciudad, eps_id, tipo_regimen, genero) VALUES
('Laura Gómez', '10100101', 'laura.gomez@example.com', '1234', 'cliente', 'activo', '1991-08-10', '3102345678', 'Bogotá D.C.', 1, 'Contributivo', 'Femenino'),
('Carlos Rodríguez', '10100102', 'carlos.rodriguez@example.com', '1234', 'cliente', 'activo', '1985-04-25', '3113456789', 'Medellín', 2, 'Subsidiado', 'Masculino'),
('Ana Martínez', '10100103', 'ana.martinez@example.com', '1234', 'cliente', 'activo', '1993-02-18', '3124567890', 'Cali', 3, 'Contributivo', 'Femenino'),
('Jorge Hernández', '10100104', 'jorge.hernandez@example.com', '1234', 'cliente', 'activo', '1978-12-01', '3135678901', 'Barranquilla', 4, 'Especial', 'Masculino'),
('Sofía Pérez', '10100105', 'sofia.perez@example.com', '1234', 'cliente', 'inactivo', '2001-06-30', '3146789012', 'Cartagena', 5, 'Subsidiado', 'Femenino'),
('Luis Díaz', '10100106', 'luis.diaz@example.com', '1234', 'cliente', 'activo', '1998-09-14', '3157890123', 'Bucaramanga', 6, 'Contributivo', 'Masculino'),
('Valentina Torres', '10100107', 'valentina.torres@example.com', '1234', 'cliente', 'activo', '1990-07-22', '3168901234', 'Cúcuta', 7, 'Contributivo', 'Femenino'),
('Andrés Ramírez', '10100108', 'andres.ramirez@example.com', '1234', 'cliente', 'activo', '1995-01-05', '3179012345', 'Pereira', 8, 'Subsidiado', 'Masculino'),
('Camila Vargas', '10100109', 'camila.vargas@example.com', '1234', 'cliente', 'activo', '1989-10-12', '3180123456', 'Bogotá D.C.', 1, 'Contributivo', 'Femenino'),
('Diego Moreno', '10100110', 'diego.moreno@example.com', '1234', 'cliente', 'activo', '1992-11-20', '3191234567', 'Medellín', 2, 'Contributivo', 'Masculino'),
('Isabella Jiménez', '10100111', 'isabella.jimenez@example.com', '1234', 'cliente', 'activo', '1997-03-03', '3202345678', 'Cali', 3, 'Especial', 'Femenino'),
('Juan Ruiz', '10100112', 'juan.ruiz@example.com', '1234', 'cliente', 'activo', '1980-05-19', '3213456789', 'Barranquilla', 4, 'Contributivo', 'Masculino'),
('María Suárez', '10100113', 'maria.suarez@example.com', '1234', 'cliente', 'inactivo', '1999-08-28', '3224567890', 'Cartagena', 5, 'Subsidiado', 'Femenino')
ON CONFLICT (cedula) DO NOTHING;


-- ** SECCIÓN 3: INSERCIÓN MASIVA DE ALERTAS **
WITH data (usuario_email, medicamento_nombre, dosis, frecuencia, fecha_inicio_offset, fecha_fin_offset, hora, estado) AS (
    VALUES
    ('laura.gomez@example.com', 'Paracetamol 500mg', '1 comprimido', 'Cada 8 horas', 0, 30, '08:00:00', 'activa'),
    ('laura.gomez@example.com', 'Ibuprofeno 400mg', '1 tableta', 'Cada 12 horas', -10, 5, '12:00:00', 'activa'),
    ('carlos.rodriguez@example.com', 'Losartán 50mg', '1 tableta', 'Cada 12 horas', -90, NULL, '09:00:00', 'activa'),
    ('carlos.rodriguez@example.com', 'Metformina 850mg', '1 tableta', 'Con cada comida', -90, NULL, '21:00:00', 'activa'),
    ('ana.martinez@example.com', 'Amoxicilina 500mg', '1 cápsula', 'Cada 8 horas', -7, 0, '06:00:00', 'completada'),
    ('jorge.hernandez@example.com', 'Salbutamol 100mcg', '2 inhalaciones', 'Cada 6 horas', -180, NULL, '07:30:00', 'activa'),
    ('luis.diaz@example.com', 'Sertralina 50mg', '1 tableta', 'Una vez al día', -60, NULL, '10:00:00', 'activa'),
    ('valentina.torres@example.com', 'Levotiroxina 50mcg', '1 comprimido', 'Antes de dormir', -365, NULL, '22:00:00', 'activa'),
    ('andres.ramirez@example.com', 'Amlodipino 5mg', '1 tableta', 'Una vez al día', -50, 100, '20:00:00', 'activa'),
    ('camila.vargas@example.com', 'Vitamina D3 1000UI', '1 cápsula', 'Cada 24 horas', -20, 20, '13:00:00', 'activa'),
    ('diego.moreno@example.com', 'Warfarina 5mg', '1/2 tableta', 'Cada día', -400, NULL, '19:00:00', 'activa'),
    ('isabella.jimenez@example.com', 'Atorvastatina 20mg', '1 comprimido', 'Cada noche', -150, NULL, '21:30:00', 'activa'),
    ('juan.ruiz@example.com', 'Hierro Fumarato 200mg', '1 cápsula', 'Con almuerzo', -10, 80, '12:30:00', 'activa'),
    ('santiago.garcia@example.com', 'Pregabalina 75mg', '1 cápsula', 'Cada 12 horas', -25, 5, '10:00:00', 'completada'),
    ('santiago.garcia@example.com', 'Pregabalina 75mg', '1 cápsula', 'Cada 12 horas', -25, 5, '22:00:00', 'completada'),
    ('daniela.ortiz@example.com', 'Enalapril 10mg', '1 tableta', 'Cada 24 horas', -200, NULL, '07:00:00', 'activa'),
    ('eineralvear77@gmail.com', 'Paracetamol 500mg', '2 tabletas', 'Si hay dolor', 0, 10, '10:00:00', 'activa'),
    ('eineralvear77@gmail.com', 'Loratadina 10mg', '1 tableta', 'En la mañana', -5, 25, '06:30:00', 'activa'),
    ('brayanamadoitg7c@gmail.com', 'Metformina 850mg', '1 tableta', 'Después del desayuno', -80, NULL, '08:30:00', 'activa')
)
INSERT INTO alertas (usuario_id, medicamento_id, dosis, frecuencia, fecha_inicio, fecha_fin, hora_preferida, estado, asignado_por_usuario_id)
SELECT u.id, m.id, d.dosis, d.frecuencia, CURRENT_DATE + d.fecha_inicio_offset, CASE WHEN d.fecha_fin_offset IS NOT NULL THEN CURRENT_DATE + d.fecha_fin_offset ELSE NULL END, d.hora::time, d.estado::varchar, (SELECT id FROM usuarios WHERE rol='admin' LIMIT 1)
FROM data d
JOIN usuarios u ON d.usuario_email = u.email
JOIN medicamentos m ON d.medicamento_nombre = m.nombre
ON CONFLICT DO NOTHING;