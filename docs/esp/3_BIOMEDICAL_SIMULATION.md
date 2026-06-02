# 🫀 Simulación Biomédica y Procesamiento Digital de Señal (DSP)

Este documento expone las bases matemáticas e ingenieriles detrás del motor de generación electrofisiológica y el filtrado digital que BiosenseLink ejecuta en tiempo real para simular un monitor Point-of-Care (PoC) de grado clínico.

---

## 1. Simulación Dinámica del ECG (Modelo de McSharry)

Para evitar la limitación de reproducir archivos estáticos pregrabados, BiosenseLink genera la actividad eléctrica cardíaca "sobre la marcha" (en vivo) utilizando el modelo matemático avanzado propuesto por McSharry et al. (IEEE Transactions on Biomedical Engineering, 2003).

### 1.1. Bucle de Generación Vectorial (Vectorcardiograma 3D)

El script `ecg_simulator.py` utiliza un sistema de tres ecuaciones diferenciales ordinarias (ODEs) acopladas que simulan la trayectoria tridimensional del vector dipolo eléctrico del corazón (VCG: $x, y, z$).

La morfología del ECG (las ondas P, Q, R, S, T) se modela empujando el atractor hacia un ciclo límite en un espacio de estados 3D, donde cada onda se define matemáticamente mediante funciones Gaussianas parametrizadas por:
*   $\theta_i$: Ángulo de la onda.
*   $a_i$: Amplitud de la onda.
*   $b_i$: Anchura de la onda.

**Ecuaciones Base:**
$$ \dot{x} = \alpha x - \omega y $$
$$ \dot{y} = \alpha y + \omega x $$
$$ \dot{z} = -\sum a_i \cdot \Delta \theta_i \cdot e^{-\frac{\Delta \theta_i^2}{2b_i^2}} - (z - z_0) $$

### 1.2. Transformación Espacial a 12 Derivaciones (Matriz de Dower)

El dipolo tridimensional (VCG) obtenido se proyecta sobre la superficie del torso humano mediante la **Transformada de Dower Inversa**. Esto permite obtener las **12 derivaciones estándar** (I, II, III, aVR, aVL, aVF, V1-V6) que utilizan los cardiólogos, a partir de solo tres vectores ortogonales generados matemáticamente.

---

## 2. Inyección de Artefactos y Modos de Falla (Triage)

El simulador no genera señales perfectas, sino realistas. Por defecto, en el script, se inyectan dos artefactos clínicos:

1.  **Deriva de la Línea Base (Baseline Wander)**: Modulación de baja frecuencia ($0.15 - 0.30$ Hz) que simula el movimiento de la caja torácica causado por la respiración del paciente.
2.  **Ruido Mioeléctrico e Interferencias de Red (EMG / 50Hz)**: Ruido Gaussiano y sinusoidal de alta frecuencia acoplado que simula contracciones musculares menores y acoplamiento electromagnético de la toma de corriente local.

### 2.1 Escenarios Clínicos (Modificación de Parámetros)

El simulador permite variar en caliente los atractores de las ODEs para inducir:
*   **Taquicardia Ventricular (TV)**: Alterando masivamente la amplitud de QRS y colapsando el tiempo interlatido.
*   **Isquemia Miocárdica (STEMI)**: Aumentando el voltaje asimétrico del segmento ST (fase de repolarización temprana) sobre las derivaciones precordiales.
*   **Fibrilación Auricular (FA)**: Aleatorizando la frecuencia cardíaca (distribución bimodal) y suprimiendo la amplitud de la onda P.

---

## 3. Procesamiento Digital de Señal (DSP) - `signal_processor.py`

Dado que la IA y el frontend reciben la señal cruda mezclada con ruido, el Gateway debe acondicionarla usando `scipy.signal`.

### 3.1. Filtrado Butterworth de Fase Cero
Para evitar la distorsión de fase (que podría alterar clínicamente la lectura del intervalo PR o QT), se emplea el método de filtrado hacia adelante y hacia atrás (`scipy.signal.filtfilt`).

**Pipeline de Filtrado Clínico:**
1.  **Filtro Paso Alto (High-pass) a 0.5 Hz:** Elimina la deriva respiratoria de la línea base manteniendo intacto el segmento ST.
2.  **Filtro Paso Bajo (Low-pass) a 40 Hz:** Corta el ruido electromiográfico. (De acuerdo a las normativas de la AHA para monitoreo clínico rutinario).
3.  **Filtro Notch (Rechazo de Banda) a 50 Hz:** Suprime el pico de interferencia armónica de la red eléctrica europea. (Factor de Calidad $Q = 30$).

```python
from scipy.signal import butter, filtfilt, iirnotch

def pipeline_clinical_standard(signal, fs=500):
    # 1. Filtro Paso Banda (0.5 - 40 Hz)
    nyq = 0.5 * fs
    b, a = butter(4, [0.5 / nyq, 40.0 / nyq], btype='band')
    sig_band = filtfilt(b, a, signal)
    
    # 2. Filtro Notch (50 Hz)
    b_n, a_n = iirnotch(50.0, 30.0, fs)
    sig_clean = filtfilt(b_n, a_n, sig_band)
    
    return sig_clean
```

### 3.2. Extracción de Características (Delineación)
Una vez limpia, `pqrst_analyzer.py` usa Wavelets continuas (CWT) y el algoritmo **Pan-Tompkins modificado** a través de `NeuroKit2` para marcar los puntos de inicio y fin métrico de cada onda, proveyendo al CDSS con intervalos cronometrados en milisegundos con alta fiabilidad geométrica.
