# 🔐 Usuarios Clínicos y Administración de Pacientes (HL7 FHIR)

Este documento detalla la estructura y el acceso de los profesionales sanitarios al sistema **BiosenseLink**, así como el flujo de gestión e interoperabilidad de los pacientes utilizando el estándar internacional **HL7 FHIR R4**.

---

## 1. Usuarios Clínicos (Almacenados en PostgreSQL) 🔐

Los profesionales de la salud que acceden a la consola de simulación y monitorización se gestionan mediante una base de datos local **PostgreSQL** (contenedor `clinical-postgres-db`). La tabla `clinical_users` almacena las credenciales y los roles que regulan los permisos en la plataforma:

| Profesional | ID de Usuario | PIN de Acceso | Rol en la Plataforma | Especialidad / Cargo |
| :--- | :--- | :--- | :--- | :--- |
| **Dr. Ander Otxoa** | `ander` | `1234` | Médico / Administrador Clínico | Jefe de Servicio de Cardiología |
| **Enf. Amaia Ruiz** | `amaia` | `5678` | Enfermera de Guardia | Unidad de Cuidados Intensivos (UCI) |
| **Administrador del Sistema** | `sysadmin` | `9999` | Administrador de Sistema | Soporte Técnico / Ingeniería Biomédica |

> [!IMPORTANT]
> **Autenticación:** El acceso se valida directamente comparando el PIN de acceso ingresado en la interfaz con los registros de la base de datos PostgreSQL. Esto permite simular escenarios de control de accesos basados en roles (RBAC).

---

## 2. Pacientes (Almacenados en HAPI FHIR R4) 🏥

A diferencia de los usuarios de la plataforma, la información clínica e identificativa de los pacientes no se guarda en el esquema relacional de PostgreSQL. En su lugar, se gestiona como recursos estandarizados bajo el protocolo de interoperabilidad médica **HL7 FHIR R4**, y se almacena directamente en el contenedor del servidor de interoperabilidad (**HAPI FHIR Starter**).

### El Paciente por Defecto
Al arrancar la plataforma, el sistema carga de forma predeterminada al siguiente paciente:
*   **Nombre:** `Ander Unicornio`
*   **ID de Recurso FHIR:** `ander-patient`
*   **Edad:** 28 años
*   **Sexo:** Varón
*   **Historial:** Sin patologías previas registradas.

### Dar de Alta Nuevos Pacientes
Para registrar y simular nuevos perfiles clínicos en tiempo real, la plataforma dispone de una sección específica:

1.  **Formulario de Registro:** En el panel lateral izquierdo del navegador web, accede a la sección llamada **"Creación de Pacientes HL7 FHIR"** (o *"HL7 FHIR Pazienteen Sorkuntza"* si alternas al idioma euskera).
2.  **Campos Clínicos:** Introduce los datos del nuevo paciente:
    *   Nombre y Apellidos.
    *   Edad (años).
    *   Peso (kg) y Altura (cm).
    *   Diagnóstico Crónico (ej. *Infarto Agudo de Miocardio (STEMI)*, *Fibrilación Auricular (FA)*, etc.).
3.  **Inyección en Servidor FHIR:** Al hacer clic en **"Dar de Alta Nuevo Paciente"**, el backend de BiosenseLink realiza las siguientes acciones:
    *   Instancia un recurso FHIR estándar de tipo `Patient`.
    *   Envía una petición HTTP POST/PUT al servidor HAPI FHIR (`http://localhost:8080/fhir/Patient`).
    *   Una vez guardado, el nuevo paciente se añade dinámicamente al selector superior de **pacientes activos** de tu consola para que puedas simular y monitorizar su telemetría fisiológica en tiempo real.

> [!TIP]
> **Flujo de prueba:** 
> 1. Inicia sesión con el PIN `1234`.
> 2. Dirígete a la sección de creación de pacientes.
> 3. Registra un paciente de prueba y verifica cómo aparece automáticamente en el menú desplegable superior listo para iniciar la simulación de trazado de 12 derivaciones.
