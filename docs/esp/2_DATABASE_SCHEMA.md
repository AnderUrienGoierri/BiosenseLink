# 🗄️ Esquema de Base de Datos y Seguridad Clínica (RBAC)

Este documento detalla la topología de la base de datos relacional PostgreSQL desplegada en el ecosistema **BiosenseLink**, enfocada en el control de acceso, la trazabilidad y la seguridad técnica en un entorno médico simulado.

---

## 1. Arquitectura de Almacenamiento Local

Mientras que la telemetría continua y los diagnósticos estructurados se inyectan dinámicamente en el servidor **HAPI FHIR R4** (Puerto `8080`), la plataforma requiere un sistema robusto, de baja latencia y fuertemente tipado para gestionar la Identidad y Acceso de los Profesionales (IAM/RBAC). Para ello, se emplea **PostgreSQL 15** corriendo en un contenedor de Docker local.

| Servicio / Parámetro | Configuración Técnica |
| :--- | :--- |
| **Motor de BD** | PostgreSQL 15 (Docker: `postgres:15-alpine`) |
| **Puerto Expuesto** | `5432` |
| **Volumen Persistente** | `postgres_data` (Mapeado a disco físico para evitar pérdida de datos) |
| **Consola de Administración** | `pgAdmin 4` (Puerto `5050`) |
| **Credenciales Globales** | `postgre_pass.txt` (Raíz de `docs/`) |

---

## 2. El Paradigma "Edge Gateway": Separación de Responsabilidades

Una pregunta técnica frecuente al revisar este esquema es: **¿Dónde están las tablas de pacientes (`patients`) y constantes vitales (`vital_signs`)?**

La respuesta radica en el diseño avanzado de BiosenseLink como un **Gateway de Borde (Edge Device) IoMT**. En el ecosistema hospitalario moderno, un monitor clínico a pie de cama nunca debe almacenar localmente la Historia Clínica Electrónica (HCE) de forma persistente utilizando esquemas SQL clásicos, por estrictas razones de seguridad (HIPAA/GDPR) y de sincronización de datos.

Por tanto, el almacenamiento se divide en dos silos conceptuales:

1.  **PostgreSQL (Operativa Local y RBAC):** Se utiliza única y exclusivamente para gobernar el propio dispositivo local. Su única tabla es `clinical_users` para responder inmediatamente al intento de acceso del personal sanitario, permitiendo autenticación de baja latencia incluso si se pierde la conexión a internet del hospital.
2.  **Servidor HAPI FHIR (Repositorio Clínico de Datos - CDR):** Los datos generados (constantes a 500Hz, diagnósticos de la IA) no se estructuran en columnas SQL. El Gateway empaqueta los hallazgos al vuelo en recursos estándar internacionales JSON (como `Observation` y `DiagnosticReport`) y los inyecta directamente al servidor central **HAPI FHIR** del hospital. Esto garantiza una interoperabilidad clínica inmediata con plataformas como Osabide Global o Epic.

*(Para más información sobre cómo se guardan los datos de los pacientes, consultar el documento `4_FHIR_INTEGRATION.md`)*.

---

## 3. Esquema Relacional (DDL)

El script de despliegue inicial (`db_setup.py`) ejecuta sentencias DDL (Data Definition Language) de forma asíncrona sobre PostgreSQL usando la librería `psycopg2`. La estructura de las tablas está optimizada para lectura rápida en el proceso de autenticación.

### Tabla: `clinical_users`

Almacena la fuerza laboral clínica con acceso al sistema Gateway.

```sql
CREATE TABLE IF NOT EXISTS clinical_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    pin VARCHAR(4) NOT NULL,
    role VARCHAR(20) NOT NULL,
    display_name VARCHAR(100) NOT NULL
);
```

**Restricciones de Integridad:**
*   `username` debe ser estrictamente único para evitar colisiones de sesión.
*   `pin` de longitud exacta 4. *En un entorno de producción estricto (HIPAA/GDPR), este campo estaría hasheado mediante algoritmos bcrypt/Argon2. En esta PoC, se utiliza texto plano cifrado en tránsito.*
*   `role`: Enumeración lógica (`admin`, `nurse`). Define el alcance de acceso en la consola.

---

## 3. Control de Acceso Basado en Roles (RBAC)

El Control de Acceso se resuelve en la capa de la API (`server.py`) interrogando a la base de datos PostgreSQL en el momento de la autenticación. 

Existen dos roles troncales desplegados por defecto:

1. **Jefe de Cardiología / Administrador (`admin`)**
   *   **Identidad:** Dr. Ander Otxoa
   *   **PIN:** `1234`
   *   **Permisos:** Privilegios de superusuario. Acceso total a la modificación del motor DSP, inyección en vivo de artefactos fisiológicos, alteración de la frecuencia de telemetría y uso de la API FHIR.

2. **Enfermera de Guardia / Operador (`nurse`)**
   *   **Identidad:** Enf. Amaia Ruiz
   *   **PIN:** `5678`
   *   **Permisos:** Visualización (Solo Lectura) del monitor de constantes vitales, osciloscopio ECG (WebSockets) y reporte del CDSS. No puede alterar los parámetros físicos de la simulación mediante comandos REST.

---

## 4. Auditoría y Trazabilidad

En el ámbito biomédico, la trazabilidad de las acciones clínicas sobre un monitor es mandatoria (Ej: Normativas FDA 21 CFR Part 11).

*   **Intrusión y Bloqueo**: El frontend de BiosenseLink registra los intentos de acceso fallidos. Cuando la respuesta de PostgreSQL para el emparejamiento Usuario-PIN devuelve `NULL`, la API responde con un `HTTP 401 Unauthorized`.
*   **Logging en Backend**: El backend FastApi escribe eventos de inicio de sesión de forma persistente a través del módulo `logging` estándar de Python, permitiendo una reconstrucción forense de las interacciones con la Consola Clínica.

---

## 5. Script de Inicialización Automática

El script `scripts/db_setup.py` actúa como una semilla (*seed*) idempotente:

1. Intenta conectar usando credenciales temporales.
2. Comprueba si la base de datos `clinical_db` existe. Si no, la crea.
3. Se conecta a `clinical_db`.
4. Crea la tabla `clinical_users` si no existe.
5. Inyecta los roles iniciales ("Ander" y "Amaia") utilizando `INSERT ... ON CONFLICT DO NOTHING`.

Esto garantiza que el entorno médico esté operativa de inmediato al pulsar el botón "Play" en el script de orquestación `Lanzar_BiosenseLink.ps1`.
