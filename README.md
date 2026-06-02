# 📟 BiosenseLink: Gateway IoMT Inteligente y Sistema de Soporte a Decisiones Clínicas (CDSS)

**BiosenseLink** representa el estado del arte en telemedicina y monitorización continua. Concebido desde la óptica de la **Ingeniería Biomédica** y el **Desarrollo de Aplicaciones Multiplataforma (DAM)**, esta solución actúa como un **Gateway Edge IoMT (Internet of Medical Things)** unificado.

El sistema es capaz de simular, adquirir, procesar e interpretar de forma autónoma bioseñales complejas (ECG de 12 derivaciones a 500Hz) y métricas hemodinámicas continuas, integrando a su vez el volcado de datos in vitro de múltiples dispositivos *Point-of-Care (PoC)* críticos. Su motor de razonamiento impulsado por Inteligencia Artificial (Ollama - DeepSeek R1) y su arquitectura basada en el estándar interoperable **HL7 FHIR R4** lo convierten en una plataforma robusta preparada para su despliegue en entornos hospitalarios (p. ej., Osakidetza).

---

## ✨ Características Principales y Arquitectura DAM

Desde la perspectiva del **Desarrollo de Aplicaciones Multiplataforma**, BiosenseLink está diseñado como un ecosistema distribuido y altamente reactivo:

1. **Telemetría de Alta Frecuencia (WebSockets)**: El núcleo del servidor (`FastAPI` en Python) transmite en tiempo real una matriz de tensiones eléctricas (mV) a 500 Hz a los clientes web y de escritorio, garantizando un retardo sub-milisegundo crucial en monitorización crítica.
2. **Interfaces Reactivas Multi-Dispositivo**: 
   - *Cliente Web*: Un dashboard interactivo construido con HTML5 Canvas y JavaScript Vanilla (con estilado Tailwind) que implementa algoritmos de renderizado por *ring-buffer* para simular osciloscopios de fósforo (CRT) de calidad médica sin parpadeos.
   - *Cliente Java*: Aplicación Swing (`java_client`) estructurada de forma modular.
3. **Procesamiento Digital de Señal (DSP)**: Limpieza heurística y matemática en vivo del ruido electromiográfico, respiratorio e interferencias de la red eléctrica mediante filtros Butterworth de Fase Cero y rechazo de banda (Notch IIR a 50Hz) implementados en SciPy/NumPy.
4. **Agente IA Clínico Air-Gapped (CDSS)**: Un pipeline LLM seguro que evalúa parámetros cuantitativos extraídos matemáticamente de las ondas (PR, QRS, QTc, segmento ST) emitiendo juicios diagnósticos como si se tratara de un especialista en cardiología.
5. **Autenticación Basada en Roles (RBAC)**: Login biométrico/pin seguro gestionado localmente.
6. **Localización Bilingüe In-Vivo (i18n)**: Sistema robusto para cambiar dinámicamente entre Castellano y Euskera en todas las plataformas.

---

## 🫀 Fisiología y Telemetría: Signos Vitales y ECG 12-Leads

El simulador implementa el **Modelo Dinámico de ECG de McSharry (Dower Transform)** modificado para proporcionar las **12 derivaciones estándar** simultáneas (I, II, III, aVR, aVL, aVF, V1-V6). 

*   **Derivaciones Bipolares y Monopolares (Limb Leads)**: Analizan el vector eléctrico en el plano frontal.
*   **Derivaciones Precordiales (V1-V6)**: Permiten la localización exacta de zonas de isquemia subendocárdica o necrosis transmural en el ventrículo izquierdo y el tabique.
*   **Análisis QRS y Repolarización**: Los algoritmos extraen automáticamente la longitud del intervalo PR, la anchura del QRS y el QTc (fórmula de Bazett), alertando de bloqueos AV, taquicardias ventriculares o prolongaciones peligrosas asociadas a arritmias letales (Torsades de Pointes).

A nivel sistémico, BiosenseLink orquesta parámetros como **SpO2** (saturación de oxígeno), **NIBP** (presión arterial no invasiva), **FC** (frecuencia cardíaca), **FR** (frecuencia respiratoria), **EtCO2** (capnografía) y **Temperatura** corporal, correlacionando en tiempo real el deterioro hemodinámico.

---

## 🔬 Ecosistema de Dispositivos Point-of-Care (PoC)

El Gateway integra de forma transparente seis ecosistemas de laboratorio *Point-of-Care*, cruciales en unidades de cuidados intensivos (UCI) y urgencias:

1. **Welch Allyn Connex (Vital Signs Monitor)**
   Monitor multiparamétrico primario que captura las bioseñales analógicas del paciente (ECG continuo, pulsioximetría óptica, manguito de presión). Es el responsable de enviar los flujos de telemetría a la red IoMT a alta frecuencia.

2. **Abbott i-STAT Alinity (Gasometría Arterial)**
   Analizador de sangre portátil avanzado. Aporta información vital instantánea sobre gases en sangre (PaO2, PaCO2), equilibrio ácido-base (pH, HCO3, Exceso de Bases) y electrolitos críticos (K+, Na+, iCa++). Indispensable para diagnosticar acidosis respiratoria o metabólica en pacientes críticos.

3. **Roche Accu-Chek Inform II (Glucómetro e Hitos)**
   Permite la medición precisa y conectada de la glucemia capilar en el punto de atención. Fundamental en el ajuste de infusiones de insulina endovenosa en pacientes diabéticos o en estados de shock.

4. **Roche CoaguChek Pro II (Coagulómetro)**
   Dispositivo PoC para el control del INR y del Tiempo de Protrombina (TP). Crucial para el ajuste rápido de terapias anticoagulantes (como heparinas o dicumarínicos) ante riesgo de trombosis o hemorragia activa.

5. **Alere Triage MeterPro (Inmunología Cardíaca)**
   Analizador de biomarcadores cardíacos por fluorescencia. Su función en la plataforma es reportar cuantitativamente la Troponina I/T, CK-MB y el BNP (Péptido Natriurético Cerebral), determinando el nivel de daño miocárdico en un infarto agudo y la insuficiencia cardíaca congestiva.

6. **m-PIMA & GeneXpert (Seguimiento VIH PoC)**
   Sistemas de diagnóstico molecular rápido. Aportan el recuento de linfocitos CD4 y cargas virales para la monitorización de pacientes inmunodeprimidos, permitiendo la adaptación inmediata de profilaxis ante infecciones oportunistas detectadas por el sistema.

---

## 🔄 Pipeline del Flujo de Datos Biomédicos (HL7 FHIR)

1. **Ingesta y Streaming**: El servidor adquiere y digitaliza (simula) bioseñales.
2. **Filtrado (DSP)**: Eliminación matemática de artefactos, estabilizando la isoclínica.
3. **Análisis Morfológico**: Los algoritmos extraen y miden el complejo PQRST.
4. **Razonamiento Cognitivo (AI)**: Inyección estructurada de hallazgos hacia el modelo **DeepSeek-R1 (8B)**.
5. **Transaccionalidad**: Las respuestas y métricas se traducen al estándar semántico **HL7 FHIR R4**. Los recursos (`Patient`, `Observation`, `DiagnosticReport`) se envían vía peticiones POST RESTful a un servidor de interoperabilidad centralizado (**HAPI FHIR**), cerrando el ciclo con la Historia Clínica Electrónica.

---

## 🚀 Guía de Implementación y Ejecución Local

Para levantar todo el ecosistema de *Simulation Suite PoC*, los requisitos son:

*   **Docker Desktop** (Para levantar la BBDD PostgreSQL y HAPI FHIR).
*   **Python 3.10+** (Para el gateway y DSP).
*   **Ollama** instalado localmente con el modelo `deepseek-r1:8b` (`ollama run deepseek-r1:8b`).

### Pasos de Arranque:

1. **Instalar dependencias Python:**
   ```bash
   pip install fastapi uvicorn websockets psycopg2-binary numpy pandas scipy neurokit2 matplotlib
   ```
2. **Orquestar Contenedores y el Gateway:**
   Ejecuta el script orquestador maestro desde la raíz. Este inicia los contenedores FHIR/DB y levanta el servidor Edge FastAPI de telemetría (Puerto 8081).
   ```cmd
   Lanzar_BiosenseLink.bat
   ```
3. **Acceder a la Consola Web:**
   Navega a `http://localhost:8081`. 
   > **Credenciales (PIN):** Dr. Ander Otxoa (`1234`), Enfermera Amaia (`5678`).

---

## 📂 Organización del Directorio

*   **`frontend/`**: Cliente interactivo Web (HTML5 Canvas).
*   **`java_client/`**: Aplicación de escritorio Java Swing (Contiene su propio launcher `Lanzar_Java.bat`).
*   **`scripts/`**: Lógica central en Python (Servidor FastAPI, simulador de ECG, Procesamiento Digital de Señal).
*   **`scripts/launchers/`**: Scripts secundarios de orquestación (Powershell).
*   **`data/`**: Caché de bases de datos locales y payloads FHIR JSON.
*   **`docs/`**: Documentación técnica bilingüe.

---

## 🔬 Módulos de Profundización (Documentación Oficial)

La plataforma contiene una suite de manuales técnicos avanzados que cubren la validación de software en el entorno médico. Accede a ellos desde el directorio principal de documentación:

🔗 **[Ir al Portal de Documentación (docs/INDEX.md)](./docs/INDEX.md)**

*Todo el ecosistema ha sido desarrollado con el máximo rigor académico aplicable a entornos de simulación Point-of-Care.*
