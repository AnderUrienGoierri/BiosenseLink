"""
==============================================================================
BiosenseLink - Motor de Procesamiento Digital de Senales (DSP)
==============================================================================
Implementa filtros digitales IIR validados clinicamente para la limpieza
de senales ECG, eliminando artefactos fisicos sin distorsionar la morfologia
de las ondas PQRST.

Filtros disponibles:
  1. Butterworth Paso Banda (0.5-40 Hz) - Filtro clinico estandar.
  2. Butterworth Paso Bajo (configurable) - Eliminacion de ruido de alta frecuencia.
  3. Butterworth Paso Alto (configurable) - Eliminacion de deriva de linea de base.
  4. Notch 50 Hz - Eliminacion de interferencia de red electrica europea.
  5. Notch 60 Hz - Eliminacion de interferencia de red electrica americana.

IMPORTANTE - Todos los filtros utilizan filtfilt() (fase cero):
  El filtrado convencional (lfilter) introduce un desfase temporal que
  distorsiona los intervalos PR, QRS y QT, invalidando el diagnostico
  clinico. La funcion filtfilt() de SciPy aplica el filtro en ambos sentidos
  (forward-backward), cancelando totalmente el desfase de fase. Esto es
  un requisito obligatorio en electrocardiografia clinica.

  Referencia:
  Gustafsson F. "Determining the initial states in forward-backward
  filtering." IEEE Trans Signal Process. 1996;44(4):988-992.

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch, sosfiltfilt, sosfilt
from typing import Tuple


# ---------------------------------------------------------------------------
# Filtros Butterworth IIR (Respuesta Infinita al Impulso)
# ---------------------------------------------------------------------------

import pandas as pd

def _apply_filter(signal, b, a):
    """Aplica filtfilt soportando tanto np.ndarray 1D como pd.DataFrame multicanal."""
    if isinstance(signal, pd.DataFrame):
        # Aplicar a cada columna del DataFrame
        filtered_df = signal.copy()
        for col in filtered_df.columns:
            filtered_df[col] = filtfilt(b, a, signal[col].values)
        return filtered_df
    else:
        return filtfilt(b, a, signal)


def butterworth_bandpass(
    signal,
    fs: int = 500,
    lowcut: float = 0.5,
    highcut: float = 40.0,
    order: int = 4,
):
    """
    Filtro paso banda Butterworth de fase cero.

    Este es el filtro estandar recomendado por la AHA para ECG clinico.
    Elimina simultaneamente:
      - Deriva de linea base (< 0.5 Hz) causada por respiracion y movimiento.
      - Ruido de alta frecuencia (> 40 Hz) causado por EMG y electronica.

    El orden 4 proporciona una atenuacion de -80 dB/decada fuera de la banda
    de paso, suficiente para aislar las componentes PQRST sin distorsion.

    Args:
        signal: Senal ECG cruda (mV) o DataFrame de 12 derivaciones.
        fs: Frecuencia de muestreo (Hz).
        lowcut: Frecuencia de corte inferior (Hz).
        highcut: Frecuencia de corte superior (Hz).
        order: Orden del filtro (4 = -80 dB/dec de roll-off).

    Returns:
        Senal ECG filtrada (mV), sin desfase temporal.
    """
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist

    # Validacion de frecuencias
    if low <= 0 or high >= 1:
        raise ValueError(
            f"Frecuencias de corte fuera de rango. Nyquist={nyquist} Hz, "
            f"lowcut={lowcut} Hz, highcut={highcut} Hz"
        )

    b, a = butter(order, [low, high], btype='band')
    return _apply_filter(signal, b, a)


def butterworth_lowpass(
    signal,
    fs: int = 500,
    cutoff: float = 40.0,
    order: int = 4,
):
    """
    Filtro paso bajo Butterworth de fase cero.

    Elimina frecuencias por encima del corte (ruido muscular EMG,
    interferencias electronicas y artefactos de alta frecuencia).
    Preserva intacta la morfologia de las ondas PQRST.

    Args:
        signal: Senal ECG cruda (mV) o DataFrame de 12 derivaciones.
        fs: Frecuencia de muestreo (Hz).
        cutoff: Frecuencia de corte (Hz).
        order: Orden del filtro.

    Returns:
        Senal filtrada.
    """
    nyquist = 0.5 * fs
    normalized_cutoff = cutoff / nyquist
    b, a = butter(order, normalized_cutoff, btype='low')
    return _apply_filter(signal, b, a)


def butterworth_highpass(
    signal,
    fs: int = 500,
    cutoff: float = 0.5,
    order: int = 4,
):
    """
    Filtro paso alto Butterworth de fase cero.

    Elimina la deriva de la linea de base causada por:
      - Movimiento respiratorio del paciente (0.15-0.3 Hz).
      - Variaciones de impedancia electrodo-piel.
      - Artefactos de movimiento del cable.

    La frecuencia de corte de 0.5 Hz es el estandar AHA para monitorizacion
    ambulatoria. Para ECG diagnostico de alta fidelidad se recomienda 0.05 Hz.

    Args:
        signal: Senal ECG cruda (mV) o DataFrame de 12 derivaciones.
        fs: Frecuencia de muestreo (Hz).
        cutoff: Frecuencia de corte (Hz).
        order: Orden del filtro.

    Returns:
        Senal filtrada.
    """
    nyquist = 0.5 * fs
    normalized_cutoff = cutoff / nyquist
    b, a = butter(order, normalized_cutoff, btype='high')
    return _apply_filter(signal, b, a)


# ---------------------------------------------------------------------------
# Filtros Notch (Elimina-Banda Estrecha)
# ---------------------------------------------------------------------------

def notch_filter(
    signal,
    fs: int = 500,
    freq: float = 50.0,
    quality_factor: float = 30.0,
):
    """
    Filtro Notch (elimina-banda) de fase cero.

    Elimina de forma quirurgica la interferencia de la red electrica
    a una frecuencia especifica sin afectar las bandas adyacentes.

    En Europa la frecuencia de red es 50 Hz.
    En America es 60 Hz.

    El factor de calidad Q determina la estrechez del notch:
      - Q=30: Notch estrecho, minima distorsion de la senal.
      - Q=10: Notch ancho, mayor eliminacion pero mas distorsion.

    Args:
        signal: Senal ECG cruda (mV) o DataFrame de 12 derivaciones.
        fs: Frecuencia de muestreo (Hz).
        freq: Frecuencia a eliminar (Hz).
        quality_factor: Factor Q del notch.

    Returns:
        Senal filtrada.
    """
    b, a = iirnotch(freq, quality_factor, fs)
    return _apply_filter(signal, b, a)


# ---------------------------------------------------------------------------
# Cadenas de procesamiento predefinidas (Pipelines)
# ---------------------------------------------------------------------------

def pipeline_clinical_standard(
    signal,
    fs: int = 500,
):
    """
    Pipeline clinico estandar AHA/IEC 60601-2-25 para ECG diagnostico:
      1. Notch 50 Hz (eliminacion de red electrica).
      2. Paso banda Butterworth 0.05-40 Hz orden 4.
      
    Nota: Es critico usar 0.05 Hz y no 0.5 Hz como limite inferior para no 
    distorsionar el segmento ST (necesario para detectar infartos).
    """
    # Paso 1: Eliminar interferencia de red
    clean = notch_filter(signal, fs, freq=50.0)
    # Paso 2: Aislar banda de interes clinico (0.05 Hz para preservar ST)
    clean = butterworth_bandpass(clean, fs, lowcut=0.05, highcut=40.0, order=4)
    return clean


def pipeline_monitoring(
    signal,
    fs: int = 500,
):
    """
    Pipeline de monitorizacion ambulatoria:
      1. Notch 50 Hz.
      2. Paso banda 0.5-150 Hz (banda ancha para capturer armonicos QRS).

    Utilizado en monitores Holter y sistemas de telemetria donde se necesita
    la banda completa de frecuencias del ECG para analisis de arritmias.
    """
    clean = notch_filter(signal, fs, freq=50.0)
    clean = butterworth_bandpass(clean, fs, lowcut=0.5, highcut=min(150.0, fs/2 - 1), order=3)
    return clean


# ---------------------------------------------------------------------------
# Catalogo de filtros disponibles
# ---------------------------------------------------------------------------
FILTERS = {
    "raw":              ("Senal Cruda (Sin Filtrar)",          lambda s, fs: s),
    "clinical":         ("Pipeline Clinico AHA (0.5-40 Hz)",   pipeline_clinical_standard),
    "monitoring":       ("Pipeline Monitorizacion (0.5-150 Hz)", pipeline_monitoring),
    "bandpass_narrow":  ("Paso Banda Estrecho (1-30 Hz)",      lambda s, fs: butterworth_bandpass(s, fs, 1.0, 30.0, 4)),
    "bandpass_wide":    ("Paso Banda Ancho (0.05-100 Hz)",     lambda s, fs: butterworth_bandpass(s, fs, 0.05, 100.0, 4)),
    "lowpass_25":       ("Paso Bajo 25 Hz",                    lambda s, fs: butterworth_lowpass(s, fs, 25.0, 4)),
    "lowpass_40":       ("Paso Bajo 40 Hz",                    lambda s, fs: butterworth_lowpass(s, fs, 40.0, 4)),
    "highpass_0.5":     ("Paso Alto 0.5 Hz",                   lambda s, fs: butterworth_highpass(s, fs, 0.5, 4)),
    "highpass_1.0":     ("Paso Alto 1.0 Hz",                   lambda s, fs: butterworth_highpass(s, fs, 1.0, 4)),
    "notch_50":         ("Notch 50 Hz (Red Electrica EU)",     lambda s, fs: notch_filter(s, fs, 50.0)),
    "notch_60":         ("Notch 60 Hz (Red Electrica US)",     lambda s, fs: notch_filter(s, fs, 60.0)),
}


if __name__ == "__main__":
    from ecg_simulator import generate_normal_sinus

    t, raw = generate_normal_sinus(duration=5)
    clean = pipeline_clinical_standard(raw, fs=500)
    print(f"Senal cruda:   rango [{raw.min():.3f}, {raw.max():.3f}] mV")
    print(f"Senal filtrada: rango [{clean.min():.3f}, {clean.max():.3f}] mV")
    print(f"Reduccion de ruido: {((np.std(raw) - np.std(clean)) / np.std(raw) * 100):.1f}%")
