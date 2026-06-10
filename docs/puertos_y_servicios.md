# Guía de Puertos y Servicios de BiosenseLink (Entorno Fedora VM)

Este documento detalla los puertos de red utilizados en el entorno de desarrollo y simulación de **BiosenseLink** ejecutándose en la máquina virtual Fedora.

## Mapa General de Puertos

| Puerto (Host) | Puerto (Guest) | Servicio | Tipo | Acceso Externo | Descripción |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **8081** | `8081` | **BiosenseLink Backend** | HTTP/WS | Sí | Servidor FastAPI de telemetría y API Gateway, y servidor de archivos estáticos para la consola web. |
| **8080** | `8080` | **HAPI FHIR Server** | HTTP | Sí | Servidor de interoperabilidad clínica estándar HL7 FHIR R4. |
| **9000** | `9000` | **Portainer CE** | HTTP | Sí | Panel de control web para la gestión de contenedores Docker. |
| **8010** | `8000` | **Paperless-ngx** | HTTP | Sí | Gestor documental con OCR inteligente multilingüe integrado. |
| **5050** | `80` | **pgAdmin 4** | HTTP | Sí | Consola web de administración de la base de datos PostgreSQL. |
| **8082** | `80` | **phpMyAdmin** | HTTP | Sí | Consola web de administración de la base de datos MySQL. |
| **8000** | `80` | **Apache/PHP** | HTTP | Sí | Servidor Web de uso general. |
| **3030** | `3000` | **Sensing Server** | TCP | Sí | Servidor receptor de telemetría WiFi para biosensores. |
| **3000** | `3000` | **Gotenberg** | HTTP | Sí | Motor de generación de reportes y conversión PDF clínicos. |
| **5432** | `5432` | **PostgreSQL DB** | TCP | Sí | Base de datos relacional para control de seguridad y credenciales. |
| **3306** | `3306` | **MySQL DB** | TCP | Sí | Base de datos de desarrollo general. |
| **5678** | `5678` | **n8n Automation** | HTTP | Sí | Orquestador de flujos de trabajo e integraciones automatizadas. |
| **2222** | `22` | **SSH Server** | TCP/SSH | Sí | Acceso por terminal segura al entorno virtual Fedora. |
| **11434**| `11434`| **Ollama Service** | HTTP | Local | Servidor local de Modelos de Lenguaje (LLMs) como `qwen2.5`. |
| **8085** | `8080` | **Homer Dashboard** | HTTP | Sí | Portal y lanzador web centralizado para todos los puertos locales. |

---

## Servicios Destacados y Enlaces de Acceso (desde Windows)

### 0. Portal y Lanzador de Enlaces Central (Homer)
* **Dirección:** [http://localhost:8085](http://localhost:8085)
* **Descripción:** Panel de control centralizado y moderno (diseño oscuro y glassmorphism) para acceder de forma rápida a todos los servicios de la infraestructura con un solo clic.

### 1. Consola de Telemetría BiosenseLink (Point-of-Care)
* **Dirección:** [http://localhost:8081](http://localhost:8081)
* **Descripción:** Panel principal de simulación e integración de dispositivos y pacientes en tiempo real.

### 2. Panel de Control de Docker (Portainer)
* **Dirección:** [http://localhost:9000](http://localhost:9000)
* **Descripción:** Panel gráfico para encender, apagar y reiniciar los contenedores. 
* **Acceso:** Crea tu cuenta inicial al acceder por primera vez.

### 3. Gestor Documental (Paperless-ngx)
* **Dirección:** [http://localhost:8010](http://localhost:8010)
* **Credenciales por defecto:**
* **Usuario:** `admin`
* **Contraseña:** `admin_password`
* **Idiomas de Reconocimiento de Texto (OCR) soportados:** Español (`spa`), Inglés (`eng`), Alemán (`deu`), Francés (`fra`), Ruso (`rus`), Japonés (`jpn`), Chino Simplificado (`chi_sim`) y Chino Tradicional (`chi_tra`).

### 4. Servidor de Interoperabilidad (HAPI FHIR)
* **Dirección:** [http://localhost:8080](http://localhost:8080)
* **Descripción:** Repositorio oficial para registros médicos estructurados de los pacientes.


---

## Comandos Útiles para el Control de Puertos en Fedora

* **Ver puertos a la escucha en tiempo real:**
  ```bash
  ss -tulpn
  ```
* **Ver qué servicio está ocupando un puerto específico (ejemplo, 8081):**
  ```bash
  sudo lsof -i :8081
  ```
* **Reiniciar el puerto de un contenedor (ejemplo, portainer):**
  ```bash
  docker restart portainer
  ```
