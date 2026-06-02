# 🔗 Interoperabilidad Clínica (HL7 FHIR R4) y Telemetría Asíncrona

El mayor desafío en la telemedicina moderna no es solo medir las bioseñales, sino estandarizarlas. BiosenseLink aborda este reto integrando de forma nativa el estándar internacional **HL7 FHIR R4** para transmitir y almacenar todas las observaciones biomédicas y reportes diagnósticos.

---

## 1. El Servidor Clínico: HAPI FHIR

La plataforma delega el almacenamiento a largo plazo y la lógica de validación semántica a un servidor dedicado **HAPI FHIR** (basado en Java) que se ejecuta en el contenedor Docker en el puerto `8080`.

**Ventajas Arquitectónicas:**
*   **Desacoplamiento:** BiosenseLink actúa como un "Edge Device" sin estado persistente; delega la historia clínica al HAPI FHIR.
*   **Agnosticismo:** Cualquier otro sistema hospitalario (p.ej., Osabide Global) puede interrogar al servidor HAPI FHIR independientemente de si usa Python, Java, o .NET.

---

## 2. Inyección Telemétrica Asíncrona (Background Tasks)

En lugar de requerir scripts externos como `run_simulation_lab.ps1`, el orquestador maestro de BiosenseLink (`server.py`) monta una Tarea Asíncrona (`asyncio.create_task`) utilizando el decorador `@app.on_event("startup")` de FastAPI.

Esta tarea funciona como un "demonio" (Daemon) ininterrumpido que simula las transmisiones cíclicas de los biosensores (ej. Welch Allyn Connex).

**Flujo del Bucle Asíncrono:**
1.  Espera `N` segundos (intervalo de telemetría definido en el estado global).
2.  Genera ruido aleatorio sobre la base de las constantes vitales del triage actual (Ej. Si el triage es FA, la frecuencia cardíaca base fluctúa agresivamente entre 110 y 160 lpm).
3.  Crea un payload JSON compatible con el esquema `Observation` de FHIR.
4.  Realiza una petición HTTP POST asíncrona (`httpx` o `aiohttp` / `urllib`) al endpoint `http://localhost:8080/fhir/Observation`.

---

## 3. Mapeo Semántico (LOINC y SNOMED CT)

Para que los datos tengan valor médico real, no basta con enviar números crudos. Se deben etiquetar mediante ontologías biomédicas controladas en el script `fhir_exporter.py`.

### 3.1. Vocabulario LOINC (Logical Observation Identifiers Names and Codes)
Se utiliza para codificar mediciones y resultados de laboratorio.
*   **Frecuencia Cardíaca**: `8867-4`
*   **Saturación de Oxígeno (SpO2)**: `2708-6`
*   **Presión Arterial Sistólica**: `8480-6`
*   **Presión Arterial Diastólica**: `8462-4`
*   **Temperatura Corporal**: `8310-5`

### 3.2. Vocabulario SNOMED CT (Systematized Nomenclature of Medicine)
Se utiliza por el agente CDSS (Ollama) para codificar los diagnósticos extraídos tras el análisis matemático del ECG.
*   **Ritmo Sinusal Normal**: `74864009`
*   **Fibrilación Auricular**: `49436004`
*   **Taquicardia Ventricular**: `253889003`
*   **Isquemia Aguda (STEMI)**: `401303003`
*   **Parada Cardíaca (Asistolia)**: `410429000`

---

## 4. Estructura de Recursos FHIR (JSON)

BiosenseLink produce dos tipos primarios de recursos: `Observation` y `DiagnosticReport`.

### Ejemplo de Recurso `Observation` (Frecuencia Cardíaca):
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "8867-4",
      "display": "Heart rate"
    }]
  },
  "subject": {
    "reference": "Patient/biosenselink-001"
  },
  "valueQuantity": {
    "value": 75.0,
    "unit": "beats/minute",
    "system": "http://unitsofmeasure.org",
    "code": "/min"
  }
}
```

### Ejemplo de Recurso `DiagnosticReport` (CDSS Generado por IA):
```json
{
  "resourceType": "DiagnosticReport",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11524-6",
      "display": "EKG Study"
    }]
  },
  "conclusion": "Paciente presenta Fibrilación Auricular con respuesta ventricular rápida. Ausencia de ondas P y R-R irregular.",
  "conclusionCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "49436004",
      "display": "Atrial Fibrillation"
    }]
  }]
}
```

---

## 5. Botón de Exportación del Cliente de Escritorio ("Exportar a HL7 FHIR")

En el cliente gráfico de escritorio (`main.py`), el botón **"Exportar a HL7 FHIR"** (o *"HL7 FHIRra esportatu"*) inicia un flujo asíncrono de interoperabilidad clínica estandarizada con cada clic.

### 5.1. Flujo de Ejecución Técnico
Al presionar el botón, la función de callback `on_export_fhir(event)` realiza los siguientes pasos secuenciales:
1. **Lectura de Datos Cuantitativos y Cualitativos:** Extrae del estado global de la aplicación (`state`) los parámetros calculados de la señal ECG (`ECGAnalysisReport`) y el diagnóstico diferencial del módulo CDSS.
2. **Estructuración FHIR R4:** Llama a la función `export_to_fhir_bundle` del módulo `fhir_exporter.py`. Esta función construye un paquete clínico (Bundle) FHIR validado utilizando la biblioteca `fhir.resources`.
3. **Persistencia JSON:** Escribe el paquete resultante (Bundle) en la ruta local `data/fhir_report.json` con codificación UTF-8.
4. **Interacción Asíncrona con el Usuario:** Cambia temporalmente el color de fondo del botón a verde (`#2ecc71`) y actualiza su etiqueta a **"¡Exportado!"** (o *"Esportatuta!"*). Se inicia un hilo asíncrono (`threading.Thread`) para esperar 1.5 segundos sin congelar la interfaz de usuario (UI), restaurando posteriormente el color y la etiqueta originales del botón.

### 5.2. Recursos Clínicos Mapeados y Estructura Semántica
El `Bundle` generado (de tipo `collection`) sigue una estructura médica profesional:
*   **Paciente (`Patient`):** Perfil de paciente simulado identificado mediante un UUID único universal.
*   **Observaciones (`Observation`):** Las métricas clave del análisis del ECG se etiquetan con sus códigos LOINC oficiales correspondientes:
    *   *Frecuencia Cardíaca (Heart Rate):* LOINC `8867-4` (unidad: `/min`)
    *   *Intervalo PR (PR Interval):* LOINC `46087-3` (unidad: `ms`)
    *   *Duración QRS (QRS Duration):* LOINC `46088-1` (unidad: `ms`)
    *   *Intervalo QTc (QTc Interval):* LOINC `8636-4` (unidad: `ms`)
*   **Reporte Diagnóstico (`DiagnosticReport`):** Representa el estudio ECG completo (LOINC `11524-6`), referenciando los recursos `Observation` anteriores y adjuntando las conclusiones del CDSS de IA (como *STEMI*, *Fibrilación Auricular*, etc. mediante la terminología **SNOMED CT**).

### 5.3. Relevancia del Paradigma IoMT Edge Gateway
Esta función consolida a BiosenseLink como un **Edge Gateway** inteligente. Transforma bioseñales físicas crudas y diagnósticos diferenciales complejos en estándares de comunicación médica internacionales, permitiendo que cualquier Sistema de Información Hospitalaria (EHR / HKE) los interprete de manera nativa sin necesidad de capas de adaptación personalizadas.

---

## 6. Por qué las Señales EKG Crudas no tienen un FHIR ID Independiente (Arquitectura Clínica)

Una pregunta habitual en el ámbito biomédico y de informática médica es por qué las constantes vitales independientes (como la frecuencia cardíaca) tienen un FHIR ID asignado, mientras que los valores de voltaje instantáneo de la señal de EKG cruda no lo tienen. Esto se debe enteramente al diseño de la arquitectura de HL7 FHIR y a la eficiencia informática:

### 6.1. Volumen de Datos y Colapso de Red (DDoS Clínico)
Las señales de EKG de 12 derivaciones son flujos continuos de alta frecuencia (en nuestro sistema, muestreadas a 500 Hz, lo que equivale a 500 muestras por segundo para cada una de las 12 señales).
* Si intentáramos registrar cada muestra temporal individual de voltaje (ej. *I: 0.470 mV*) como un recurso `Observation` HTTP POST independiente en el servidor FHIR, estaríamos realizando **6.000 peticiones por segundo**.
* Esto provocaría un colapso inmediato por denegación de servicio (DDoS) en la base de datos clínica del hospital y saturaría la red con peticiones redundantes.

### 6.2. Cómo maneja FHIR R4 las Bioseñales Continuas
El estándar HL7 FHIR define mecanismos específicos para almacenar bioseñales continuas sin tratar cada muestra como un recurso independiente:
* **El tipo de datos `SampledData`:** FHIR define el campo `valueSampledData` dentro de una `Observation`. En lugar de guardar un solo valor numérico, guarda la secuencia completa de miles de muestras en una única cadena de texto separada por espacios (ej. `"0.470 -0.170 -0.307..."`), detallando los parámetros de muestreo (500 Hz), factor de escala y origen. De esta forma, **toda la tira de señal de las 12 derivaciones se almacena en un único recurso con un solo FHIR ID**.
* **El recurso `DiagnosticReport` (Enfoque en BiosenseLink):** El estudio completo de un EKG representa un acto clínico integrado. Por tanto:
  1. Los valores de la lista superior (Frecuencia cardíaca, SpO₂, temperatura, etc.) son **métricas discretas e independientes**, por lo que cada una recibe su propia `Observation` y su **FHIR ID** exclusivo en cada ciclo de telemetría.
  2. Los voltajes que se visualizan en la parte inferior del log de la terminal son un visor en tiempo real (un "osciloscopio" de diagnóstico local) para validar el comportamiento físico de la pasarela Edge.
  3. El bloque completo del EKG de 12 derivaciones y el diagnóstico de la IA se empaquetan en un único reporte clínico unificado (`DiagnosticReport`) al presionar el botón **"HL7 FHIRra esportatu" / "Exportar a HL7 FHIR"**. Es en ese instante cuando todo el estudio recibe un FHIR ID oficial y se almacena en la historia clínica.


