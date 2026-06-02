# Guia de Interpretacion Clinica Automatizada

## Criterios Diagnosticos Implementados en BiosenseLink

Este documento detalla los criterios clinicos basados en la evidencia medica
que el motor de analisis de BiosenseLink aplica de forma automatizada para
detectar anomalias cardiacas en el trazado ECG.

> **AVISO LEGAL:** BiosenseLink es un sistema de soporte de decision clinica
> (CDSS) y NO sustituye el juicio clinico de un profesional medico cualificado.
> Los hallazgos generados requieren siempre validacion y correlacion clinica
> por parte de un cardiologo o medico especialista.

---

## 1. Frecuencia Cardiaca

| Clasificacion | Rango | Severidad | Referencia |
|:---|:---|:---|:---|
| Bradicardia severa | < 40 lpm | CRITICO | AHA/ACC/HRS 2018 |
| Bradicardia sinusal | 40-59 lpm | ATENCION | AHA/ACC/HRS 2018 |
| Normal | 60-100 lpm | NORMAL | - |
| Taquicardia sinusal | 101-150 lpm | ATENCION | ESC 2019 SVT |
| Taquicardia severa | > 150 lpm | CRITICO | ESC 2019 SVT |

**Nota clinica:** La bradicardia sinusal puede ser fisiologica en atletas
de alto rendimiento (FC en reposo de 35-50 lpm). No debe interpretarse
como patologica sin correlacion clinica.

---

## 2. Regularidad del Ritmo (Coeficiente de Variacion RR)

El CV(RR) mide la dispersion relativa de los intervalos entre latidos.

| CV(RR) | Interpretacion |
|:---|:---|
| < 5% | Ritmo muy regular. Normal sinusal. |
| 5-15% | Variabilidad fisiologica normal (arritmia sinusal respiratoria). |
| > 15% | Ritmo irregularmente irregular. Sospecha de fibrilacion auricular. |

**Base cientifica:** La fibrilacion auricular se define clinicamente como un
ritmo auricular caotico sin ondas P organizadas y con intervalos RR
irregularmente irregulares. (Hindricks G, et al. ESC 2020 AF Guidelines.
Eur Heart J. 2021;42(5):373-498)

---

## 3. Intervalo PR

El intervalo PR mide el tiempo de conduccion desde la despolarizacion
auricular (onda P) hasta el inicio de la despolarizacion ventricular (QRS).

| Rango | Interpretacion | Criterio |
|:---|:---|:---|
| < 120 ms | PR corto: Sospecha pre-excitacion (WPW) | ESC 2019 SVT |
| 120-200 ms | Normal | AHA/ACC 2009 |
| > 200 ms | Bloqueo AV de 1er grado | AHA/ACC/HRS 2018 |

---

## 4. Duracion del QRS

La duracion del QRS refleja el tiempo de conduccion intraventricular.

| Duracion | Interpretacion | Referencia |
|:---|:---|:---|
| < 120 ms | Normal | AHA/ACCF/HRS 2009 |
| 120-159 ms | Bloqueo de rama incompleto o aberrancia | AHA/ACCF/HRS 2009 |
| >= 160 ms | Bloqueo completo de rama o TV | AHA/ACCF/HRS 2009 |

---

## 5. Intervalo QTc (Correccion de Bazett)

El QTc compensa la dependencia del intervalo QT con la frecuencia cardiaca.

**Formula de Bazett (1920):**
```
QTc = QT / sqrt(RR)    (donde RR en segundos)
```

| QTc | Interpretacion | Riesgo |
|:---|:---|:---|
| < 350 ms | QT corto | Riesgo de FV (sindrome QT corto) |
| 350-450 ms | Normal (hombres) | - |
| 350-460 ms | Normal (mujeres) | - |
| 450-500 ms | Prolongado | Riesgo moderado |
| > 500 ms | Prolongado critico | Alto riesgo de torsades de pointes |

**Farmacos que prolongan el QT (lista no exhaustiva):**
Antiarritmicos (amiodarona, sotalol), antibioticos (azitromicina, fluoroquinolonas),
antidepresivos (citalopram), antiemeticos (ondansetron), antipsicoticos (haloperidol).

> Referencia: Priori SG, et al. "2015 ESC Guidelines for the management of
> patients with ventricular arrhythmias." Eur Heart J. 2015;36(41):2793-2867.

---

## 6. Segmento ST

El segmento ST representa el periodo entre la despolarizacion y la
repolarizacion ventricular. Su desviacion de la linea isoelectrica es
un marcador critico de isquemia miocardica.

| Desviacion | Interpretacion | Accion |
|:---|:---|:---|
| > +0.1 mV | Elevacion ST (STEMI) | Activar Codigo Infarto |
| -0.1 a +0.1 mV | Isoelectrico (Normal) | - |
| < -0.1 mV | Depresion ST (Isquemia subendocardica) | Evaluar con troponinas |

> Referencia: Ibanez B, et al. "2017 ESC Guidelines for the management of
> acute myocardial infarction in patients presenting with ST-segment elevation."
> Eur Heart J. 2018;39(2):119-177.

---

## Niveles de Severidad del Sistema

BiosenseLink clasifica cada hallazgo en 4 niveles de severidad:

| Nivel | Significado | Color | Accion Recomendada |
|:---|:---|:---|:---|
| **NORMAL** | Parametro dentro de rango fisiologico | Verde | Ninguna |
| **ATENCION** | Desviacion menor, potencialmente benigna | Amarillo | Monitorizar |
| **ALERTA** | Anomalia significativa que requiere evaluacion | Naranja | Consulta medica |
| **CRITICO** | Hallazgo potencialmente vital | Rojo | Atencion urgente |
