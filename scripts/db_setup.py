import psycopg2
import logging
import urllib.request
import json
import platform
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB-Setup")

def update_homer_footer():
    try:
        config_path = os.path.join(os.path.dirname(__file__), "homer-dashboard-assets", "config.yml")
        if not os.path.exists(config_path):
            config_path = os.path.join("scripts", "homer-dashboard-assets", "config.yml")
        if not os.path.exists(config_path):
            config_path = os.path.join("homer-dashboard-assets", "config.yml")

        if os.path.exists(config_path):
            sys_name = platform.system()
            if sys_name == 'Windows':
                os_name = 'Windows Host'
            elif sys_name == 'Linux':
                if 'microsoft' in platform.release().lower():
                    os_name = 'Windows Host (WSL2)'
                else:
                    os_name = 'Linux'
            else:
                os_name = sys_name

            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()

            new_footer = f"footer: '<p>Biomedical Hub © 2026 | Entorno de Desarrollo y Simulación Clínico | {os_name}</p>'"
            content = re.sub(r'^footer:.*', new_footer, content, flags=re.MULTILINE)

            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Homer footer updated dynamically on startup to: {os_name}")
        else:
            logger.warning(f"No se encontró el archivo de configuración de Homer en: {config_path}")
    except Exception as e:
        logger.warning(f"No se pudo actualizar el footer de Homer: {e}")

def setup_db():
    conn_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'dbadmin',
        'password': 'SecuredHospitalPass2026!',
        'dbname': 'medical_platform'
    }

    try:
        conn = psycopg2.connect(**conn_params)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info("Conectado a PostgreSQL. Creando esquema de seguridad...")
        
        # 1. Crear tabla de usuarios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clinical_users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                pin VARCHAR(10) NOT NULL,
                role VARCHAR(20) NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                title VARCHAR(100)
            );
        """)

        # 2. Limpiar tabla (para reinicios seguros)
        cursor.execute("TRUNCATE TABLE clinical_users RESTART IDENTITY;")

        # 3. Insertar roles (admin, tutoria, medicina, enfermeria)
        users = [
            ('sysadmin', '9999', 'admin', 'Soporte TI / Ing. Biomédica', 'Administrador del Sistema'),
            ('Tutor_1', '4321', 'tutoria', 'Dr. Kepa Arana (Tutor)', 'Instructor de Simulación Clínica'),
            ('Medikua_1', '1234', 'medicina', 'Dr. Ander Otxoa', 'Médico Especialista (Medikua_1)'),
            ('Erizaina_1', '5678', 'enfermeria', 'Enf. Amaia Ruiz', 'Enfermera de Guardia (Erizaina_1)')
        ]



        cursor.executemany("""
            INSERT INTO clinical_users (username, pin, role, display_name, title)
            VALUES (%s, %s, %s, %s, %s)
        """, users)

        logger.info("Usuarios creados exitosamente en PostgreSQL:")
        for u in users:
            logger.info(f" -> {u[3]} (Role: {u[2]}, PIN: {u[1]})")

        cursor.close()
        conn.close()
        logger.info("Proceso de inicialización de BBDD completado.")
        
        # 4. Inicializar paciente por defecto en HAPI FHIR R4
        setup_fhir_patient()

        # 5. Actualizar dinámicamente el footer de Homer
        update_homer_footer()

    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")

def setup_fhir_patient():
    patient_payload = {
        "resourceType": "Patient",
        "id": "ander-patient",
        "name": [
            {
                "use": "official",
                "family": "Unicornio",
                "given": ["Ander"]
            }
        ],
        "gender": "male",
        "birthDate": "1998-06-04",
        "telecom": [
            {
                "system": "email",
                "value": "ander@example.com"
            }
        ],
        "managingOrganization": {
            "display": "Hospital General"
        },
        "extension": [
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-weight",
                "valueDecimal": 70.0
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-height",
                "valueDecimal": 175.0
            },
            {
                "url": "http://hl7.org/fhir/StructureDefinition/patient-pathology",
                "valueString": "none"
            }
        ]
    }
    
    url = "http://localhost:8080/fhir/Patient/ander-patient"
    req_data = json.dumps(patient_payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/fhir+json; charset=utf-8"},
        method="PUT"
    )
    
    try:
        logger.info("Inicializando paciente por defecto (ander-patient) en HAPI FHIR...")
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            if resp.status in [200, 201]:
                logger.info("✔️ Paciente 'ander-patient' registrado con éxito en HAPI FHIR.")
    except Exception as e:
        logger.warning(f"⚠️ No se pudo inicializar el paciente en HAPI FHIR: {e}")

if __name__ == "__main__":
    setup_db()

