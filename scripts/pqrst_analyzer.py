"""
==============================================================================
BiosenseLink - Analizador PQRST y Detector de Anomalias Cardiacas (12 Leads)
==============================================================================
Realiza la delineacion completa de la onda PQRST y aplica criterios clinicos.
Soporta analisis espacial multiderivacion (12 leads) para detectar anomalias
topograficas como infartos de miocardio (STEMI anterior, inferior, etc.).

Algoritmos implementados:
  - Deteccion QRS: Pan-Tompkins (1985) via NeuroKit2.
  - Delineacion PQRST: Transformada Wavelet via NeuroKit2 en Derivacion II.
  - Criterios diagnosticos: AHA/ACC/HRS 2009, ESC 2015/2017/2021.

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import numpy as np
import pandas as pd
import neurokit2 as nk
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Estructuras de datos para resultados clinicos
# ---------------------------------------------------------------------------

@dataclass
class BeatMorphology:
    """Morfologia de un latido individual."""
    beat_index: int
    rr_interval_ms: float
    heart_rate_instantaneous: float
    pr_interval_ms: float
    qrs_duration_ms: float
    qt_interval_ms: float
    qtc_bazett_ms: float
    st_deviation_mv: float  # (Global o Lead II)


@dataclass
class ClinicalFinding:
    """Hallazgo clinico individual."""
    severity: str
    parameter: str
    value: str
    criterion: str
    interpretation: str
    reference: str


@dataclass
class ECGAnalysisReport:
    """Informe completo de analisis ECG de 12 derivaciones."""
    mean_heart_rate: float
    heart_rate_std: float
    rr_regularity_cv: float
    mean_pr_interval_ms: float
    mean_qrs_duration_ms: float
    mean_qtc_ms: float
    
    # Analisis espacial (12 derivaciones)
    st_deviations_per_lead_mv: Dict[str, float] = field(default_factory=dict)
    
    n_beats_analyzed: int = 0
    beat_morphologies: List[BeatMorphology] = field(default_factory=list)
    findings: List[ClinicalFinding] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constantes clinicas
# ---------------------------------------------------------------------------
HR_BRADYCARDIA_THRESHOLD    = 60
HR_TACHYCARDIA_THRESHOLD    = 100
HR_SEVERE_BRADY_THRESHOLD   = 40
HR_SEVERE_TACHY_THRESHOLD   = 150
PR_NORMAL_MIN_MS   = 120
PR_NORMAL_MAX_MS   = 200
QRS_NORMAL_MAX_MS  = 120
QRS_WIDE_MS        = 120
QRS_VERY_WIDE_MS   = 160
QTC_NORMAL_MAX_MALE_MS     = 450
QTC_DANGER_MS              = 500
ST_ELEVATION_THRESHOLD_MV   = 0.1
ST_DEPRESSION_THRESHOLD_MV  = -0.1
RR_IRREGULARITY_THRESHOLD   = 15.0


def analyze_ecg(
    ecg_data: Union[np.ndarray, pd.DataFrame],
    sampling_rate: int = 500,
) -> ECGAnalysisReport:
    """
    Realiza un analisis PQRST.
    Si ecg_data es un DataFrame de 12 derivaciones, usa Lead II para intervalos
    generales y calcula elevacion ST por cada derivacion.
    """
    is_multilead = isinstance(ecg_data, pd.DataFrame)
    
    if is_multilead:
        lead_ii = ecg_data["II"].values
    else:
        lead_ii = ecg_data

    # --- Paso 1: Procesamiento con NeuroKit2 (usando Lead II) ---
    try:
        signals, info = nk.ecg_process(lead_ii, sampling_rate=sampling_rate)
    except Exception as e:
        cleaned = nk.ecg_clean(lead_ii, sampling_rate=sampling_rate)
        r_peaks = nk.ecg_findpeaks(cleaned, sampling_rate=sampling_rate)
        signals = None
        info = r_peaks

    # --- Paso 2: Extraer picos R ---
    r_peaks_indices = info.get("ECG_R_Peaks", [])
    if len(r_peaks_indices) < 3:
        report = ECGAnalysisReport(0, 0, 0, 0, 0, 0)
        report.findings.append(ClinicalFinding("ALERTA", "Deteccion QRS", f"{len(r_peaks_indices)} picos", "Min 3 latidos", "Insuficiente calidad.", "N/A"))
        return report

    # --- Paso 3: Intervalos RR ---
    rr_samples = np.diff(r_peaks_indices)
    rr_ms = rr_samples / sampling_rate * 1000
    hrs = 60000.0 / rr_ms
    mean_hr = np.mean(hrs)
    std_hr  = np.std(hrs)
    cv_rr   = (np.std(rr_ms) / np.mean(rr_ms)) * 100 if np.mean(rr_ms) > 0 else 0

    # --- Paso 4: Morfologia (Global - Lead II) ---
    pr_intervals = []
    qrs_durations = []
    qtc_values = []
    
    for i in range(len(r_peaks_indices) - 1):
        r_peak = r_peaks_indices[i]
        curr_rr_ms = rr_ms[i] if i < len(rr_ms) else rr_ms[-1]
        
        pr_ms = _estimate_pr_interval(lead_ii, r_peak, sampling_rate, signals)
        qrs_ms = _estimate_qrs_duration(lead_ii, r_peak, sampling_rate, signals)
        qt_ms = _estimate_qt_interval(lead_ii, r_peak, sampling_rate, signals)
        
        qtc = qt_ms / np.sqrt(curr_rr_ms / 1000.0) if curr_rr_ms > 0 else qt_ms
        pr_intervals.append(pr_ms)
        qrs_durations.append(qrs_ms)
        qtc_values.append(qtc)

    # --- Paso 5: Analisis Espacial ST (12 Derivaciones) ---
    st_deviations = {}
    if is_multilead:
        for lead in ecg_data.columns:
            st_lead_vals = []
            for r_peak in r_peaks_indices[:-1]:
                st_lead_vals.append(_estimate_st_deviation(ecg_data[lead].values, r_peak, sampling_rate))
            st_deviations[lead] = np.mean(st_lead_vals) if st_lead_vals else 0.0
    else:
        st_vals = [_estimate_st_deviation(lead_ii, r, sampling_rate) for r in r_peaks_indices[:-1]]
        st_deviations["II"] = np.mean(st_vals) if st_vals else 0.0

    report = ECGAnalysisReport(
        mean_heart_rate=mean_hr,
        heart_rate_std=std_hr,
        rr_regularity_cv=cv_rr,
        mean_pr_interval_ms=np.mean(pr_intervals) if pr_intervals else 0,
        mean_qrs_duration_ms=np.mean(qrs_durations) if qrs_durations else 0,
        mean_qtc_ms=np.mean(qtc_values) if qtc_values else 0,
        st_deviations_per_lead_mv=st_deviations,
        n_beats_analyzed=len(r_peaks_indices)-1
    )

    # --- Paso 6: Criterios Clinicos ---
    _evaluate_heart_rate(report)
    _evaluate_rhythm_regularity(report)
    _evaluate_pr_interval(report)
    _evaluate_qrs_duration(report)
    _evaluate_qtc(report)
    _evaluate_st_segment_multilead(report)

    return report


# ---------------------------------------------------------------------------
# Estimadores Morfologicos
# ---------------------------------------------------------------------------
def _estimate_pr_interval(ecg, r_peak, fs, signals=None):
    if signals is not None and "ECG_P_Onsets" in signals.columns:
        p_onsets = signals["ECG_P_Onsets"].values
        cands = np.where((p_onsets == 1) & (np.arange(len(p_onsets)) < r_peak))[0]
        if len(cands) > 0:
            return (r_peak - cands[-1]) / fs * 1000
    return 160.0

def _estimate_qrs_duration(ecg, r_peak, fs, signals=None):
    if signals is not None and "ECG_R_Onsets" in signals.columns and "ECG_R_Offsets" in signals.columns:
        onsets = signals["ECG_R_Onsets"].values
        offsets = signals["ECG_R_Offsets"].values
        onc = np.where((onsets == 1) & (np.arange(len(onsets)) <= r_peak))[0]
        offc = np.where((offsets == 1) & (np.arange(len(offsets)) >= r_peak))[0]
        if len(onc) > 0 and len(offc) > 0:
            return (offc[0] - onc[-1]) / fs * 1000
    return 90.0

def _estimate_qt_interval(ecg, r_peak, fs, signals=None):
    if signals is not None and "ECG_T_Offsets" in signals.columns and "ECG_R_Onsets" in signals.columns:
        q_onsets = signals["ECG_R_Onsets"].values
        t_offsets = signals["ECG_T_Offsets"].values
        qc = np.where((q_onsets == 1) & (np.arange(len(q_onsets)) <= r_peak))[0]
        tc = np.where((t_offsets == 1) & (np.arange(len(t_offsets)) > r_peak))[0]
        if len(qc) > 0 and len(tc) > 0:
            return (tc[0] - qc[-1]) / fs * 1000
    return 380.0

def _estimate_st_deviation(ecg, r_peak, fs):
    j_point = r_peak + int(0.08 * fs)
    st_point = j_point + int(0.06 * fs)
    if st_point < len(ecg):
        st_seg = ecg[j_point:st_point]
        bl_s = max(0, r_peak - int(0.30 * fs))
        bl_e = max(0, r_peak - int(0.25 * fs))
        baseline = np.mean(ecg[bl_s:bl_e]) if bl_e > bl_s else 0
        return np.mean(st_seg) - baseline
    return 0.0


# ---------------------------------------------------------------------------
# Evaluadores Clinicos
# ---------------------------------------------------------------------------
def _evaluate_heart_rate(r: ECGAnalysisReport):
    if r.mean_heart_rate > HR_SEVERE_TACHY_THRESHOLD:
        r.findings.append(ClinicalFinding("CRITICO", "FC", f"{r.mean_heart_rate:.0f} lpm", ">150", "Taquicardia severa.", "ESC 2019"))
    elif r.mean_heart_rate > HR_TACHYCARDIA_THRESHOLD:
        r.findings.append(ClinicalFinding("ATENCION", "FC", f"{r.mean_heart_rate:.0f} lpm", ">100", "Taquicardia sinusal.", "ESC 2019"))
    elif r.mean_heart_rate < HR_SEVERE_BRADY_THRESHOLD:
        r.findings.append(ClinicalFinding("CRITICO", "FC", f"{r.mean_heart_rate:.0f} lpm", "<40", "Bradicardia severa.", "AHA 2018"))
    elif r.mean_heart_rate < HR_BRADYCARDIA_THRESHOLD:
        r.findings.append(ClinicalFinding("ATENCION", "FC", f"{r.mean_heart_rate:.0f} lpm", "<60", "Bradicardia sinusal.", "AHA 2018"))

def _evaluate_rhythm_regularity(r: ECGAnalysisReport):
    if r.rr_regularity_cv > RR_IRREGULARITY_THRESHOLD:
        r.findings.append(ClinicalFinding("ALERTA", "Ritmo", f"{r.rr_regularity_cv:.1f}%", ">15%", "Ritmo irregular. Sospecha FA.", "ESC 2020"))

def _evaluate_pr_interval(r: ECGAnalysisReport):
    if r.mean_pr_interval_ms > PR_NORMAL_MAX_MS:
        r.findings.append(ClinicalFinding("ALERTA", "PR", f"{r.mean_pr_interval_ms:.0f} ms", ">200", "Bloqueo AV 1er grado.", "AHA 2018"))

def _evaluate_qrs_duration(r: ECGAnalysisReport):
    if r.mean_qrs_duration_ms > QRS_WIDE_MS:
        r.findings.append(ClinicalFinding("ALERTA", "QRS", f"{r.mean_qrs_duration_ms:.0f} ms", ">120", "QRS ancho.", "AHA 2009"))

def _evaluate_qtc(r: ECGAnalysisReport):
    if r.mean_qtc_ms > QTC_DANGER_MS:
        r.findings.append(ClinicalFinding("CRITICO", "QTc", f"{r.mean_qtc_ms:.0f} ms", ">500", "Riesgo Torsades.", "ESC 2015"))


def _evaluate_st_segment_multilead(r: ECGAnalysisReport):
    elevated_leads = [lead for lead, val in r.st_deviations_per_lead_mv.items() if val > ST_ELEVATION_THRESHOLD_MV]
    depressed_leads = [lead for lead, val in r.st_deviations_per_lead_mv.items() if val < ST_ELEVATION_THRESHOLD_MV]
    
    anterior = [l for l in elevated_leads if l in ['V1', 'V2', 'V3', 'V4']]
    inferior = [l for l in elevated_leads if l in ['II', 'III', 'aVF']]
    lateral  = [l for l in elevated_leads if l in ['I', 'aVL', 'V5', 'V6']]
    
    if len(anterior) >= 2:
        r.findings.append(ClinicalFinding("CRITICO", "ST Anterior", f"Elevacion en {anterior}", ">0.1mV en 2+ leads", "STEMI Anterior.", "ESC 2017"))
    if len(inferior) >= 2:
        r.findings.append(ClinicalFinding("CRITICO", "ST Inferior", f"Elevacion en {inferior}", ">0.1mV en 2+ leads", "STEMI Inferior.", "ESC 2017"))
    if len(lateral) >= 2:
        r.findings.append(ClinicalFinding("CRITICO", "ST Lateral", f"Elevacion en {lateral}", ">0.1mV en 2+ leads", "STEMI Lateral.", "ESC 2017"))
