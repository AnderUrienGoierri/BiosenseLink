# ⚙️ Guía de Despliegue e Instalación (Setup Guide)

Este manual proporciona las instrucciones paso a paso para levantar el ecosistema **BiosenseLink** en un entorno de desarrollo o simulación clínica (Windows/Linux/Mac).

---

## 1. Prerrequisitos del Sistema

Antes de iniciar la plataforma, asegúrate de tener instalados los siguientes componentes:

1.  **Docker Desktop / Docker Engine**: Requerido para virtualizar los servidores de PostgreSQL y HAPI FHIR. Asegúrate de que el demonio de Docker esté corriendo.
2.  **Python 3.10 o superior**: Requerido para el Gateway FastAPI y los motores DSP (SciPy/NeuroKit2).
3.  **Ollama**: Instalado localmente para inferencia Air-Gapped de Inteligencia Artificial.
4.  **PowerShell (Windows) o Bash (Linux)**: Para la ejecución del orquestador.

---

## 2. Preparación del Motor de IA (Ollama)

BiosenseLink utiliza **DeepSeek-R1 (8B)** para el motor CDSS, garantizando que los datos de los pacientes no salgan de la intranet del hospital (cumplimiento normativo HIPAA/GDPR).

1. Abre tu terminal.
2. Descarga el modelo base:
   ```bash
   ollama pull deepseek-r1:8b
   ```
3. Verifica que el servidor de Ollama esté expuesto en su puerto por defecto (`http://localhost:11434`).

---

## 3. Instalación de Dependencias Backend (Python)

El servidor Edge y los algoritmos biomédicos requieren librerías matemáticas específicas.

Abre la consola en el directorio raíz de BiosenseLink (`C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink`) e instala las librerías:

```bash
pip install fastapi uvicorn websockets psycopg2-binary numpy pandas scipy neurokit2 matplotlib httpx
```

---

## 4. Despliegue Total (Orquestador Automático)

Para simplificar la puesta en marcha, no es necesario levantar los contenedores o el backend manualmente. El repositorio incluye un orquestador maestro en PowerShell.

### En Windows (PowerShell):
Ejecuta el script desde la raíz del proyecto:
```powershell
.\Lanzar_BiosenseLink.ps1
```

**¿Qué hace este script?**
1. Levanta `HAPI FHIR` en el puerto `8080` a través de Docker.
2. Levanta `PostgreSQL` en el puerto `5432`.
3. Inyecta el esquema de la base de datos y los usuarios (Dr. Ander, Enfermera Amaia).
4. Levanta el servidor `FastAPI` (Gateway) en el puerto `8081`.
5. Sirve el Frontend (HTML5 Canvas) al navegador automáticamente.

---

## 5. Resolución de Incidencias Frecuentes (Troubleshooting)

### Problema: "No se conecta a la base de datos PostgreSQL"
*   **Causa**: Docker no está corriendo o las contraseñas en `docs/postgre_pass.txt` han sido modificadas o no coinciden con el contenedor instanciado previamente.
*   **Solución**: Abre Docker Desktop, borra el contenedor `clinical-db` y el volumen `postgres_data`, y vuelve a ejecutar el script `Lanzar_BiosenseLink.ps1` para que se recreen con las contraseñas de fábrica.

### Problema: "El CDSS tarda demasiado o da Timeout"
*   **Causa**: El hardware local (GPU/CPU) está sufriendo para mantener el modelo LLM en memoria, o Ollama no está arrancado.
*   **Solución**: Asegúrate de tener al menos 8GB de RAM libre. Verifica en un navegador que `http://localhost:11434` responde con "Ollama is running".

### Problema: "La gráfica del Osciloscopio se ve lenta o a trompicones"
*   **Causa**: Tu navegador tiene deshabilitada la aceleración por hardware para el HTML5 Canvas.
*   **Solución**: Ve a las preferencias de Chrome/Edge (`chrome://settings/system`) y asegúrate de que "Usar aceleración por hardware cuando esté disponible" está activado.
