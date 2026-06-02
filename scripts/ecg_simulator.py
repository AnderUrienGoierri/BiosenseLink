"""
==============================================================================
BiosenseLink - Modulo de Simulacion de ECG de 12 Derivaciones
==============================================================================
Genera senales de electrocardiograma (ECG) sinteticas de 12 derivaciones
estandar (I, II, III, aVR, aVL, aVF, V1-V6) para diagnostico clinico.

Capacidades:
  - ECG normal sinusal de 12 derivaciones.
  - Taquicardia y Bradicardia sinusal.
  - Fibrilacion auricular (alta variabilidad RR, f-waves).
  - Infarto Agudo de Miocardio (STEMI) Anterior: Elevacion ST en V1-V4.
  - Infarto Agudo de Miocardio (STEMI) Inferior: Elevacion ST en II, III, aVF
    con cambios reciprocos en aVL.

Referencia:
  Implementado utilizando neurokit2 (simulacion multilead) e inyeccion
  parametrizada de anomalias espaciales en ventanas del segmento ST.

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import numpy as np
import pandas as pd
import neurokit2 as nk
from typing import Tuple, Dict, Callable

DEFAULT_SAMPLING_RATE = 500
DEFAULT_DURATION      = 10
LEADS = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']


def generate_base_12lead(
    duration: float = DEFAULT_DURATION,
    sampling_rate: int = DEFAULT_SAMPLING_RATE,
    heart_rate: float = 72,
    heart_rate_std: float = 1,
    noise_level: float = 0.01
) -> pd.DataFrame:
    """Genera un ECG base de 12 derivaciones usando NeuroKit2."""
    df = nk.ecg_simulate(
        duration=duration,
        sampling_rate=sampling_rate,
        heart_rate=heart_rate,
        heart_rate_std=heart_rate_std,
        method="multileads"
    )
    # Anadir ruido base
    if noise_level > 0:
        rng = np.random.default_rng(42)
        for col in df.columns:
            df[col] += rng.normal(0, noise_level, len(df))
    return df


def _inject_st_anomaly(
    df: pd.DataFrame,
    sampling_rate: int,
    target_leads: list,
    elevation_mv: float,
    reciprocal_leads: list = None,
    reciprocal_mv: float = 0.0
) -> pd.DataFrame:
    """
    Inyecta una elevacion/depresion del segmento ST en derivaciones especificas
    buscando los picos R y modificando la ventana de 60-120ms posterior.
    """
    # Usar Derivacion II para localizar los picos R
    _, rpeaks = nk.ecg_peaks(df["II"], sampling_rate=sampling_rate)
    peaks = rpeaks["ECG_R_Peaks"]

    for lead in df.columns:
        if lead not in target_leads and (reciprocal_leads is None or lead not in reciprocal_leads):
            continue

        signal = df[lead].values
        mod_val = elevation_mv if lead in target_leads else reciprocal_mv

        for r in peaks:
            st_start = r + int(0.06 * sampling_rate)
            st_end = r + int(0.18 * sampling_rate) # ST segment + T wave fusion

            if st_end < len(signal):
                window_len = st_end - st_start
                # Forma de media campana (plateau que cae)
                modifier = np.sin(np.linspace(0, np.pi, window_len)) * mod_val
                signal[st_start:st_end] += modifier

        df[lead] = signal

    return df


def generate_normal_sinus(duration=10, sampling_rate=500, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]:
    """ECG normal sinusal de 12 derivaciones."""
    df = generate_base_12lead(duration, sampling_rate, heart_rate=72, heart_rate_std=1, **kwargs)
    time_axis = np.linspace(0, duration, len(df), endpoint=False)
    return time_axis, df


def generate_bradycardia(duration=10, sampling_rate=500, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]:
    """Bradicardia sinusal."""
    df = generate_base_12lead(duration, sampling_rate, heart_rate=45, heart_rate_std=1, **kwargs)
    time_axis = np.linspace(0, duration, len(df), endpoint=False)
    return time_axis, df


def generate_tachycardia(duration=10, sampling_rate=500, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]:
    """Taquicardia sinusal."""
    df = generate_base_12lead(duration, sampling_rate, heart_rate=130, heart_rate_std=2, **kwargs)
    time_axis = np.linspace(0, duration, len(df), endpoint=False)
    return time_axis, df


def generate_stemi_anterior(duration=10, sampling_rate=500, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]:
    """STEMI Anterior: Elevacion ST en V2, V3, V4."""
    df = generate_base_12lead(duration, sampling_rate, heart_rate=90, heart_rate_std=2, **kwargs)
    df = _inject_st_anomaly(df, sampling_rate, target_leads=['V2', 'V3', 'V4'], elevation_mv=0.35)
    time_axis = np.linspace(0, duration, len(df), endpoint=False)
    return time_axis, df


def generate_stemi_inferior(duration=10, sampling_rate=500, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]:
    """STEMI Inferior: Elevacion ST en II, III, aVF. Depresion en aVL."""
    df = generate_base_12lead(duration, sampling_rate, heart_rate=85, heart_rate_std=2, **kwargs)
    df = _inject_st_anomaly(
        df, sampling_rate,
        target_leads=['II', 'III', 'aVF'], elevation_mv=0.30,
        reciprocal_leads=['aVL', 'I'], reciprocal_mv=-0.15
    )
    time_axis = np.linspace(0, duration, len(df), endpoint=False)
    return time_axis, df


def generate_atrial_fibrillation(duration=10, sampling_rate=500, **kwargs) -> Tuple[np.ndarray, pd.DataFrame]:
    """Fibrilacion Auricular: Ritmo irregular, variabilidad alta, f-waves."""
    df = generate_base_12lead(duration, sampling_rate, heart_rate=95, heart_rate_std=15, **kwargs)
    time_axis = np.linspace(0, duration, len(df), endpoint=False)

    # Inyectar f-waves (ruido fibrilatorio ~4-8 Hz)
    rng = np.random.default_rng(123)
    f_wave = 0.05 * np.sin(2 * np.pi * 6 * time_axis) + 0.02 * rng.normal(0, 1, len(time_axis))
    for lead in df.columns:
        df[lead] += f_wave

    return time_axis, df


# Catalogo
SCENARIOS = {
    "normal":         ("Ritmo Sinusal Normal (12 Leads)",         generate_normal_sinus),
    "bradycardia":    ("Bradicardia Sinusal (12 Leads)",          generate_bradycardia),
    "tachycardia":    ("Taquicardia Sinusal (12 Leads)",         generate_tachycardia),
    "stemi_ant":      ("STEMI Anterior (V2-V4)",                 generate_stemi_anterior),
    "stemi_inf":      ("STEMI Inferior (II, III, aVF)",          generate_stemi_inferior),
    "afib":           ("Fibrilacion Auricular (12 Leads)",       generate_atrial_fibrillation),
}

if __name__ == "__main__":
    t, df = generate_stemi_inferior(duration=5)
    print(f"ECG 12 Leads generado. Shape: {df.shape}")
    print(f"Columnas: {list(df.columns)}")
