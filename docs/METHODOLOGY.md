# Metodología Científica y Evidencia Clínica de BiosenseLink

## 1. Generación de ECG Sintético

### Modelo Dinámico de McSharry et al. (2003)

La simulación de señales ECG en este proyecto se basa en el **modelo dinámico
tridimensional** propuesto por McSharry, Clifford, Tarassenko y Smith, publicado
en *IEEE Transactions on Biomedical Engineering* (Vol. 50, No. 3, Marzo 2003).

Este modelo es el estándar de referencia de la comunidad científica internacional
para la generación de ECG sintéticos con morfología realista. El modelo representa
la actividad eléctrica cardíaca mediante un sistema de ecuaciones diferenciales
ordinarias (ODEs) que producen las cinco ondas características del complejo PQRST
en un plano angular:

```
dx/dt = alpha * x - omega * y
dy/dt = alpha * y + omega * x

donde alpha = 1 - sqrt(x^2 + y^2)

dz/dt = -sum_i [ a_i * delta_theta_i * exp(-delta_theta_i^2 / (2*b_i^2)) ] - (z - z0)
```

Cada onda (P, Q, R, S, T) se modela mediante un conjunto de parámetros gaussianos
(amplitud `a_i`, anchura `b_i`, y posición angular `theta_i`) que determinan su
morfología exacta. Este enfoque permite:

- Modificar la frecuencia cardíaca de forma continua y realista.
- Simular variabilidad fisiológica del ritmo (HRV - Heart Rate Variability).
- Introducir patologías específicas modificando los parámetros de las ondas.

> **Referencia primaria:**
> McSharry PE, Clifford GD, Tarassenko L, Smith LA. "A dynamical model for
> generating synthetic electrocardiogram signals." IEEE Trans Biomed Eng.
> 2003;50(3):289-294. doi:10.1109/TBME.2003.808805

---

## 2. Detección de Complejos QRS

### Algoritmo de Pan-Tompkins (1985)

Para la detección robusta de los complejos QRS, se implementa el algoritmo
clásico de **Pan y Tompkins**, publicado en *IEEE Transactions on Biomedical
Engineering* (Vol. BME-32, No. 3, Marzo 1985). Este algoritmo sigue siendo,
cuatro décadas después, el método de referencia más citado y validado
clínicamente para la detección de latidos cardíacos en tiempo real.

El pipeline del algoritmo consiste en 5 etapas secuenciales:

1. **Filtro paso banda** (5-15 Hz): Aísla las frecuencias dominantes del QRS.
2. **Derivación**: Resalta las pendientes abruptas del complejo QRS.
3. **Elevación al cuadrado**: Amplifica no linealmente las componentes de
   alta frecuencia y convierte todo a valores positivos.
4. **Integración con ventana móvil**: Suaviza la señal para obtener un
   envolvente del complejo QRS.
5. **Umbral adaptativo dual**: Aplica umbrales dinámicos que se ajustan
   latido a latido para clasificar picos como señal o ruido.

> **Referencia primaria:**
> Pan J, Tompkins WJ. "A real-time QRS detection algorithm." IEEE Trans
> Biomed Eng. 1985;BME-32(3):230-236. doi:10.1109/TBME.1985.325532

---

## 3. Delineación Completa de la Onda PQRST

### Algoritmo Basado en Transformada Wavelet (Martínez et al. 2004)

Para la delineación precisa de los puntos de inicio, pico y fin de cada onda
(P, QRS, T), se utiliza el enfoque basado en la **transformada wavelet
continua (CWT)** descrito por Martínez, Almeida, Olmos, Rocha y Laguna,
publicado en *IEEE Transactions on Biomedical Engineering* (2004).

Este método detecta los cruces por cero y los máximos/mínimos de la CWT
a múltiples escalas para localizar con precisión submuestra los puntos
fiduciales de cada componente del ECG.

> **Referencia:**
> Martínez JP, Almeida R, Olmos S, Rocha AP, Laguna P. "A wavelet-based
> ECG delineator: evaluation on standard databases." IEEE Trans Biomed Eng.
> 2004;51(4):570-581. doi:10.1109/TBME.2003.821031

---

## 4. Criterios Clínicos de Interpretación

### Guías de la AHA/ACC/HRS y la ESC

La interpretación clínica automatizada sigue los criterios diagnósticos
establecidos por las sociedades científicas de referencia:

| Parámetro | Rango Normal | Criterio Patológico | Fuente |
|:---|:---|:---|:---|
| Frecuencia Cardíaca | 60-100 lpm | <60 Bradicardia, >100 Taquicardia | AHA/ACC 2018 |
| Intervalo PR | 120-200 ms | >200 ms: Bloqueo AV 1er grado | ESC 2021 |
| Duración QRS | 80-120 ms | >120 ms: Bloqueo de rama | AHA/ACC 2009 |
| Intervalo QT corregido (QTc) | 350-450 ms (H), 350-460 ms (M) | >500 ms: Alto riesgo de torsades | ESC 2015 |
| Amplitud onda P | <0.25 mV | >0.25 mV: Crecimiento auricular | AHA/ACC 2009 |
| Segmento ST | Isoeléctrico (+/- 0.1 mV) | >0.1 mV elevación: Lesión/Isquemia | ESC 2017 (STEMI) |
| Onda T | Concordante con QRS | Inversión: Isquemia subepicárdica | AHA 2018 |

> **Referencias clínicas:**
> - Kligfield P, et al. "Recommendations for the Standardization and
>   Interpretation of the Electrocardiogram." Circulation. 2007;115:1306-1324.
> - Rautaharju PM, et al. "AHA/ACCF/HRS Recommendations for the
>   Standardization and Interpretation of the Electrocardiogram: Part IV."
>   J Am Coll Cardiol. 2009;53(11):982-991.
> - Priori SG, et al. "2015 ESC Guidelines for the management of patients
>   with ventricular arrhythmias." Eur Heart J. 2015;36(41):2793-2867.

---

## 5. Herramientas de Software Validadas

### NeuroKit2 (Makowski et al. 2021)

Este proyecto utiliza la librería **NeuroKit2** como motor principal de
análisis de señales fisiológicas. NeuroKit2 es una librería de Python
de código abierto, revisada por pares y publicada en *Behavior Research
Methods* (2021). Implementa algoritmos validados clínicamente para:

- Simulación ECG basada en ECGSYN (McSharry).
- Detección QRS (Pan-Tompkins, Hamilton, Christov, Engelse-Zeelenberg,
  Kalidas, Nabian, Rodrigues, entre otros).
- Delineación PQRST completa.
- Análisis de variabilidad de frecuencia cardíaca (HRV) en dominio
  temporal, frecuencial y no lineal.

> **Referencia:**
> Makowski D, Pham T, Lau ZJ, et al. "NeuroKit2: A Python toolbox for
> neurophysiological signal processing." Behav Res Methods. 2021;53:1689-1696.
> doi:10.3758/s13428-020-01516-y

### SciPy Signal (Virtanen et al. 2020)

Los filtros digitales IIR (Butterworth, Chebyshev, Notch) se implementan
mediante el módulo `scipy.signal`, parte del ecosistema SciPy publicado
en *Nature Methods*.

> **Referencia:**
> Virtanen P, et al. "SciPy 1.0: fundamental algorithms for scientific
> computing in Python." Nat Methods. 2020;17:261-272.
> doi:10.1038/s41592-019-0686-2
