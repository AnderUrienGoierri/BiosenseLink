import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DB-Setup")

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

        # 3. Insertar roles (System Admin, Clinical Admin, Nurse)
        users = [
            ('sysadmin', '9999', 'admin', 'Administrador del Sistema', 'Ingeniería Biomédica'),
            ('ander', '1234', 'admin', 'Dr. Ander Otxoa', 'Jefe de Servicio de Cardiología'),
            ('amaia', '5678', 'nurse', 'Enf. Amaia Ruiz', 'Enfermera de Guardia')
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

    except Exception as e:
        logger.error(f"Error inicializando base de datos: {e}")

if __name__ == "__main__":
    setup_db()
