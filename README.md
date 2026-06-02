# 📟 BiosenseLink: Gateway IoMT Inteligente y Sistema de Soporte a Decisiones Clínicas (CDSS)

**BiosenseLink** es una plataforma de software avanzado orientada a la telemedicina de próxima generación. Actúa como un **Gateway Edge IoMT (Internet of Medical Things)** unificado. El sistema es capaz de simular, procesar e interpretar de forma autónoma señales electrofisiológicas (ECG de 12 derivaciones a 500Hz) y constantes vitales continuas en entornos de *Point-of-Care (PoC)*. 

Mediante el uso de Procesamiento Digital de Señales (DSP) y una Inteligencia Artificial Generativa Local (Ollama - DeepSeek R1), el sistema emite deducciones diagnósticas que son consolidadas en el estándar oficial **HL7 FHIR R4 (Fast Healthcare Interoperability Resources)** para la interoperabilidad total con la Historia Clínica Electrónica (HCE).

Este proyecto ejemplifica la convergencia real de la **Ingeniería Biomédica**, la **Ciencia de Datos** y el **Desarrollo de Software Multiplataforma (DAM)**, preparado para despliegues reales en ecosistemas hospitalarios (p.ej. Osakidetza).

---

## ✨ Características Principales

1. **Telemetría de Alta Frecuencia**: Motor matemático basado en el Modelo Dinámico EKG de McSharry (Dower Transform) para generar señales eléctricas cardiológicas puras.
2. **Procesamiento Digital de Señal (DSP)**: Limpieza en vivo del ruido electromiográfico, respiratorio e interferencias eléctricas mediante filtros Butterworth de Fase Cero e IIR Notch a 50Hz.
3. **Dashboard Clínico Interactivo Web**: Consola renderizada en HTML5 Canvas con cuadrícula milimétrica, soporta layouts profesionales (4x3+1).
4. **Agente IA Clínico Air-Gapped**: Motor LLM estructurado en local que lee parámetros cuantitativos (PR, QRS, QTc, ST) y devuelve un razonamiento diagnóstico diferencial (Chain-of-Thought) totalmente seguro y privado.
5. **Autenticación Basada en Roles (RBAC)**: Login seguro respaldado por PostgreSQL.
6. **Localización Bilingüe In-Vivo**: Sistema I18N avanzado (Español / Euskara) que permite traducciones en vivo tanto en la web como en el visor Python.

---

## 📂 Organización y Arquitectura del Repositorio

```text
C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink\
│
├── 📁 frontend/                 # Interfaz Web del Cliente (HTML5 Canvas, Tailwind CSS, JS Vainilla).
│   └── 📁 www/                  # Archivos estáticos servidos por FastAPI.
│
├── 📁 scripts/                  # Núcleo del Backend (Motores en Python).
│   ├── server.py                # Servidor FastAPI principal (Gateway, WebSocket, Telemetría asíncrona).
│   ├── main.py                  # Visor de escritorio local interactivo en Matplotlib (12 Leads).
│   ├── ecg_simulator.py         # Modelo dinámico de simulación biomédica PQRST.
│   ├── signal_processor.py      # Filtros DSP (Butterworth, Notch, Baseline Wander).
│   ├── pqrst_analyzer.py        # Algoritmos de delineación matemática Wavelet.
│   ├── clinical_interpreter.py  # Agente conector CDSS hacia la red de Ollama local.
│   └── fhir_exporter.py         # Empaquetador semántico HL7 FHIR (JSON).
│
├── 📁 data/                     # Banco de datos de prueba local y copias en caché FHIR.
│
├── 📁 docs/                     # 📚 Documentación técnica profesional Bilingüe (Español / Euskara).
│   ├── 📁 esp/                  # Documentos técnicos en Español.
│   ├── 📁 eus/                  # Documentos técnicos en Euskara.
│   └── INDEX.md                 # Portal interactivo de la documentación.
│
├── Lanzar_BiosenseLink.ps1      # Orquestador maestro de la plataforma (PowerShell).
└── README.md                    # Documento principal del ecosistema (Este archivo).
```

---

## 🔄 Pipeline del Flujo de Datos Biomédicos

1. **Ingesta y Streaming (WebSocket)**: El servidor local (`server.py`) empuja un array de tensiones eléctricas (mV) a 500 Hz hacia el cliente frontend a través de una conexión WebSocket de baja latencia.
2. **Filtrado Biomédico (SciPy)**: La señal cruda atraviesa el puente DSP eliminando artefactos fisiológicos para asegurar la nitidez de la isoclínica.
3. **Medición Geométrica (NeuroKit2/CWT)**: Los algoritmos miden la anchura del QRS, la corrección del QTc de Bazett y la elevación o descenso isquémico del segmento ST.
4. **Razonamiento Cognitivo (Ollama AI)**: Los hallazgos se inyectan en un *Prompt* estructurado dirigido a **DeepSeek-R1 (8B)**, quien ejecuta un diagnóstico diferencial simulando las capacidades de un Cardiólogo.
5. **Transaccionalidad (HL7 FHIR)**: Todas las variables (LOINC) y los diagnósticos (SNOMED CT) se convierten en recursos `Observation` y `DiagnosticReport`, inyectándose mediante POST HTTP en el servidor de interoperabilidad local **HAPI FHIR** (Puerto 8080).

---

## 🚀 Guía de Implementación y Ejecución Local

Para levantar todo el ecosistema de *Simulation Suite PoC*, los requisitos son:

*   **Docker Desktop** (Para levantar PostgreSQL y HAPI FHIR).
*   **Python 3.10+** (Para el gateway y DSP).
*   **Ollama** instalado localmente con el modelo `deepseek-r1:8b` ya descargado (`ollama run deepseek-r1:8b`).

### Pasos de Arranque:

1. **Clonar e instalar dependencias:**
   ```bash
   pip install fastapi uvicorn websockets psycopg2-binary numpy pandas scipy neurokit2 matplotlib
   ```
2. **Orquestar Contenedores y Sistema Completo:**
   Simplemente ejecuta el script PowerShell ubicado en la raíz del proyecto. Este levantará las bases de datos (Puerto 5432 y 8080), inicializará a los usuarios y lanzará el backend FastAPI (Puerto 8081).
   ```powershell
   .\Lanzar_BiosenseLink.ps1
   ```
3. **Acceder a la Consola Web:**
   Tu navegador se abrirá automáticamente en `http://localhost:8081`. 
   > **Credenciales por defecto:** Dr. Ander Otxoa (PIN: `1234`), Enfermera Amaia (PIN: `5678`).

---

## 🔬 Módulos de Profundización (Documentación Oficial)

La plataforma contiene una suite de manuales técnicos avanzados que cubren la validación de software en el entorno médico. Accede a ellos desde el directorio principal de documentación:

🔗 **[Ir al Portal de Documentación (docs/INDEX.md)](file:///c:/Dev/05_Projects/Biomedical_IoMT/BiosenseLink/docs/INDEX.md)**

*Todo el ecosistema ha sido desarrollado con el máximo rigor académico aplicable a entornos de simulación Point-of-Care.*
