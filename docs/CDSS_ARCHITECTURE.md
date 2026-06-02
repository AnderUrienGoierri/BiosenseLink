# Arquitectura del Sistema de Soporte de Decision Clinica (CDSS)

## 1. Fundamento Cientifico

### 1.1 Definicion y Marco Regulatorio

Un Sistema de Soporte de Decision Clinica (CDSS, *Clinical Decision Support
System*) es un sistema de informacion sanitaria diseñado para asistir a los
profesionales clinicos en la toma de decisiones diagnosticas y terapeuticas,
proporcionando conocimiento relevante filtrado y presentado en el momento
y contexto adecuados (Sutton RT, et al. *NPJ Digital Medicine*. 2020;3:68).

BiosenseLink implementa un **CDSS basado en conocimiento** (*knowledge-based*)
que opera en tres capas:

```
[Capa 1: Base de Conocimiento]
    Criterios diagnosticos AHA/ACC/HRS 2009/2018, ESC 2015/2017/2020/2021
    Ontologias medicas: SNOMED CT, LOINC, ICD-11
    Guias de practica clinica basadas en la evidencia (GRADE)

[Capa 2: Motor de Inferencia]
    Modelo de lenguaje local (DeepSeek-R1 8B) con razonamiento explicable
    Chain-of-Thought (CoT) para trazabilidad del razonamiento diagnostico
    Temperatura 0.0 para reproducibilidad determinista

[Capa 3: Interfaz de Comunicacion]
    Informe clinico estructurado en JSON (FHIR-compatible)
    Salida en lenguaje natural para el profesional sanitario
    Niveles de severidad graduados (NORMAL/ATENCION/ALERTA/CRITICO)
```

### 1.2 Evidencia Cientifica del Uso de LLMs en Cardiologia

Estudios recientes han demostrado la viabilidad de modelos de lenguaje
de gran tamaño (LLMs) como herramientas de soporte en la interpretacion
de electrocardiogramas:

- **Noseworthy PA, et al.** "Artificial intelligence-guided screening for
  atrial fibrillation using electrocardiogram during sinus rhythm."
  *The Lancet*. 2019;394(10201):861-867.
  Demostro que la IA puede detectar fibrilacion auricular paroxistica
  incluso a partir de ECGs obtenidos durante ritmo sinusal normal.

- **Hannun AY, et al.** "Cardiologist-level arrhythmia detection and
  classification in ambulatory electrocardiograms using a deep neural
  network." *Nature Medicine*. 2019;25:65-69.
  Modelo DNN que alcanzo rendimiento a nivel de cardiologo en la
  clasificacion de 12 tipos de arritmias.

- **Singhal K, et al.** "Large language models encode clinical knowledge."
  *Nature*. 2023;620:172-180.
  Demostro que los LLMs pueden alcanzar el nivel de aprobado en
  examenes de medicina clinica (USMLE) y razonar sobre casos clinicos.

### 1.3 Privacidad de Datos y Ejecucion Local

Un requisito critico en la implementacion de CDSS con IA en entornos
sanitarios es la proteccion de datos del paciente, regulada por:

- **RGPD** (Reglamento General de Proteccion de Datos, UE 2016/679)
- **LOPDGDD** (Ley Organica de Proteccion de Datos, España)
- **Ley 41/2002** de autonomia del paciente

BiosenseLink ejecuta TODA la inferencia de IA de forma **local** mediante
Ollama, sin transmitir datos del paciente a servidores externos. Esto
garantiza el cumplimiento normativo absoluto y la soberania de los datos.

---

## 2. Arquitectura Tecnica del Motor CDSS

### 2.1 Flujo de Datos

```
                                 BiosenseLink CDSS Pipeline
                                 ==========================

    [ecg_simulator.py]           [signal_processor.py]         [pqrst_analyzer.py]
         |                              |                              |
    Senal ECG cruda            Senal ECG filtrada              Informe PQRST
    (mV, fs=500 Hz)            (Butterworth + Notch)           (metricas numericas)
         |                              |                              |
         +------------------------------+------------------------------+
                                        |
                                        v
                              [clinical_interpreter.py]
                                        |
                            +-----------+-----------+
                            |                       |
                    Prompt Estructurado      Datos Cuantitativos
                    (System + User)         (JSON con metricas)
                            |                       |
                            +-----------+-----------+
                                        |
                                        v
                              [Ollama API Local]
                              deepseek-r1:8b
                              Puerto 11434
                              Temp=0.0 | JSON mode
                                        |
                                        v
                              [Informe CDSS]
                              - Diagnostico diferencial
                              - Nivel de severidad
                              - Acciones recomendadas
                              - Codigos SNOMED/LOINC
                              - Justificacion explicable
```

### 2.2 Ingenieria de Prompts Clinicos

El diseño del prompt de sistema sigue los principios de la ingenieria de
prompts medicos descritos por Nori H, et al. ("Can Generalist Foundation
Models Outcompete Special-Purpose Tuning?", *arXiv*. 2023;2311.16452):

1. **Identidad y Alcance**: Define el rol exacto del modelo como cardiologo.
2. **Restricciones**: Prohibe diagnosticos definitivos sin correlacion clinica.
3. **Formato de Salida**: Fuerza JSON estructurado para interoperabilidad.
4. **Trazabilidad**: Exige cadena de razonamiento explicable (Chain-of-Thought).
5. **Determinismo**: Temperatura 0.0 para reproducibilidad inter-sesion.

### 2.3 Estructura del Modelfile de Ollama

El agente clinico se compila como un modelo personalizado de Ollama
(BiosenseLink-CDSS) con los siguientes parametros:

| Parametro | Valor | Justificacion |
|:---|:---|:---|
| Modelo base | deepseek-r1:8b | Capacidad CoT, razonamiento logico superior |
| Temperatura | 0.0 | Reproducibilidad determinista (requisito CDSS) |
| num_predict | 4096 | Espacio suficiente para razonamiento extenso |
| top_p | 0.1 | Muestreo conservador para precision diagnostica |
| repeat_penalty | 1.1 | Evitar repeticiones en la cadena de razonamiento |

---

## 3. Limitaciones y Aviso de Responsabilidad Clinica

> **AVISO LEGAL OBLIGATORIO:**
> BiosenseLink es un sistema de soporte de decision clinica (CDSS) de
> clase investigacional. NO constituye un dispositivo medico certificado
> bajo el Reglamento (UE) 2017/745 (MDR). Los resultados generados por
> el motor de IA requieren siempre validacion y correlacion clinica por
> un profesional sanitario cualificado. El uso de este sistema para la
> toma de decisiones diagnosticas o terapeuticas sin supervision medica
> queda bajo la exclusiva responsabilidad del usuario.

### Limitaciones conocidas:

1. El modelo de IA no ha sido entrenado especificamente en datos clinicos
   de electrocardiografia. Su rendimiento puede ser inferior al de
   sistemas especializados (ej. redes convolucionales entrenadas en MIT-BIH).
2. Las señales ECG sinteticas no capturan la totalidad de la variabilidad
   morfologica presente en pacientes reales.
3. El sistema analiza una unica derivacion simulada. Un ECG diagnostico
   completo requiere 12 derivaciones simultaneas.
4. La correccion QTc por formula de Bazett sobrestima el QTc a frecuencias
   cardiacas elevadas. Las formulas de Fridericia o Framingham pueden ser
   mas precisas en contextos de taquicardia.
