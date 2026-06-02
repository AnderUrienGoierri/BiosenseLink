"""
==============================================================================
BiosenseLink - Interprete Clinico con IA Local (CDSS Engine)
==============================================================================
Modulo de alto nivel que orquesta la interpretacion clinica avanzada de
senales ECG mediante el modelo de lenguaje local biosenselink-cdss.

Este modulo actua como el puente entre el analisis cuantitativo del
pqrst_analyzer.py y el motor de razonamiento de Ollama. Construye
prompts clinicos estructurados, envia los datos al LLM local, parsea
la respuesta JSON y genera un informe CDSS completo.

Pipeline:
  1. Recibe el ECGAnalysisReport del pqrst_analyzer.
  2. Serializa las metricas cuantitativas a JSON.
  3. Construye un prompt clinico estructurado con contexto del paciente.
  4. Envia la peticion a Ollama con formato JSON forzado.
  5. Parsea la respuesta y genera el informe CDSS final.

Principios de diseño:
  - Trazabilidad: Cada hallazgo incluye la cadena de razonamiento del LLM.
  - Reproducibilidad: Temperatura 0.0 garantiza resultados deterministas.
  - Interoperabilidad: Salida codificada en SNOMED CT, LOINC e ICD-11.
  - Privacidad: TODA la inferencia se ejecuta localmente (RGPD compliant).

Referencia:
  Sutton RT, et al. "An overview of clinical decision support systems:
  benefits, risks, and strategies for success." NPJ Digit Med. 2020;3:68.
  doi:10.1038/s41746-020-0221-y

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from pqrst_analyzer import ECGAnalysisReport
from ollama_connector import (
    generate,
    parse_json_response,
    check_server_health,
    check_model_available,
    OLLAMA_MODEL,
)


def build_clinical_prompt(report: ECGAnalysisReport, scenario_name: str = "") -> str:
    """
    Construye un prompt clinico estructurado para el modelo CDSS.

    El prompt sigue la metodologia de ingenieria de prompts medicos
    descrita por Nori et al. (2023), estructurandose en:
      1. Contexto del paciente y la senal.
      2. Datos cuantitativos extraidos del analisis PQRST.
      3. Instrucciones explicitas de formato de salida.

    Args:
        report: Informe de analisis PQRST del modulo pqrst_analyzer.
        scenario_name: Nombre descriptivo del escenario clinico simulado.

    Returns:
        Prompt formateado listo para enviar a Ollama.
    """
    # Serializar las metricas cuantitativas
    quantitative_data = {
        "signal_metadata": {
            "source": "Simulated single-lead ECG (Lead II equivalent)",
            "sampling_rate_hz": 500,
            "duration_seconds": 10,
            "simulation_scenario": scenario_name if scenario_name else "Unknown",
        },
        "global_metrics": {
            "mean_heart_rate_bpm": round(report.mean_heart_rate, 1),
            "heart_rate_std_bpm": round(report.heart_rate_std, 1),
            "rr_regularity_cv_percent": round(report.rr_regularity_cv, 1),
            "mean_pr_interval_ms": round(report.mean_pr_interval_ms, 0),
            "mean_qrs_duration_ms": round(report.mean_qrs_duration_ms, 0),
            "mean_qtc_bazett_ms": round(report.mean_qtc_ms, 0),
            "mean_st_deviation_mv": round(report.mean_st_deviation_mv, 4),
            "total_beats_analyzed": report.n_beats_analyzed,
        },
        "beat_by_beat_metrics": [],
    }

    # Incluir las primeras 5 morfologias latido a latido
    for beat in report.beat_morphologies[:5]:
        quantitative_data["beat_by_beat_metrics"].append({
            "beat_index": beat.beat_index,
            "rr_interval_ms": round(beat.rr_interval_ms, 1),
            "instantaneous_hr_bpm": round(beat.heart_rate_instantaneous, 1),
            "p_amplitude_mv": round(beat.p_amplitude_mv, 3),
            "pr_interval_ms": round(beat.pr_interval_ms, 0),
            "qrs_duration_ms": round(beat.qrs_duration_ms, 0),
            "qtc_bazett_ms": round(beat.qtc_bazett_ms, 0),
            "st_deviation_mv": round(beat.st_deviation_mv, 4),
            "t_amplitude_mv": round(beat.t_amplitude_mv, 3),
            "r_amplitude_mv": round(beat.r_amplitude_mv, 3),
        })

    # Incluir hallazgos del analisis algoritmico previo
    algorithmic_findings = []
    for finding in report.findings:
        algorithmic_findings.append({
            "parameter": finding.parameter,
            "value": finding.value,
            "severity": finding.severity,
            "interpretation": finding.interpretation,
            "reference": finding.reference,
        })

    quantitative_data["algorithmic_findings"] = algorithmic_findings

    # Construir el prompt final
    prompt = (
        "Analyze the following ECG data from the BiosenseLink IoMT gateway. "
        "Provide a comprehensive clinical interpretation following the JSON "
        "schema defined in your system prompt.\n\n"
        "IMPORTANT INSTRUCTIONS:\n"
        "1. Reason step-by-step through each parameter before reaching conclusions.\n"
        "2. Cross-reference findings (e.g., if HR is irregular AND P-waves are absent, "
        "consider atrial fibrillation).\n"
        "3. Provide differential diagnoses ordered by clinical probability.\n"
        "4. Include SNOMED CT codes for each finding and ICD-11 codes for diagnoses.\n"
        "5. Recommend specific clinical actions with urgency levels.\n\n"
        f"ECG DATA (JSON):\n```json\n{json.dumps(quantitative_data, indent=2)}\n```"
    )

    return prompt


def interpret_ecg(
    report: ECGAnalysisReport,
    scenario_name: str = "",
    timeout: int = 300,
) -> Dict[str, Any]:
    """
    Ejecuta la interpretacion clinica completa de un analisis ECG
    utilizando el modelo CDSS local.

    Este es el punto de entrada principal de la Fase 2 del pipeline.

    Args:
        report: Informe de analisis PQRST generado por pqrst_analyzer.
        scenario_name: Nombre del escenario clinico simulado.
        timeout: Timeout para la inferencia del LLM (segundos).

    Returns:
        Diccionario con el informe CDSS completo, incluyendo:
        - Datos cuantitativos del ECG.
        - Razonamiento clinico explicable (Chain-of-Thought).
        - Hallazgos diagnosticos con codificacion SNOMED/LOINC.
        - Diagnostico diferencial con probabilidades.
        - Acciones recomendadas con niveles de urgencia.
        - Metricas de rendimiento de la inferencia.
    """
    # Paso 1: Verificar infraestructura
    if not check_server_health():
        return _error_response("Servidor de Ollama no disponible en localhost:11434.")

    if not check_model_available():
        return _error_response(
            f"Modelo '{OLLAMA_MODEL}' no encontrado. "
            "Compilalo con: ollama create biosenselink-cdss -f BiosenseLinkCDSS.Modelfile"
        )

    # Paso 2: Construir prompt clinico
    prompt = build_clinical_prompt(report, scenario_name)

    # Paso 3: Enviar a Ollama
    print(f"\n  [CDSS] Enviando datos a {OLLAMA_MODEL}...")
    print(f"  [CDSS] Modo: JSON forzado | Temperatura: 0.0 | Timeout: {timeout}s")
    start_time = time.time()

    try:
        raw_result = generate(
            prompt=prompt,
            model=OLLAMA_MODEL,
            json_mode=True,
            temperature=0.0,
            timeout=timeout,
        )
    except (ConnectionError, TimeoutError) as e:
        return _error_response(str(e))

    elapsed = time.time() - start_time

    # Paso 4: Parsear respuesta JSON
    try:
        cdss_report = parse_json_response(raw_result)
    except ValueError as e:
        return _error_response(
            f"El modelo no devolvio JSON valido: {e}. "
            f"Respuesta cruda: {raw_result.get('response', '')[:300]}"
        )

    # Paso 5: Enriquecer con metadatos del pipeline
    cdss_report["_pipeline_metadata"] = {
        "biosenselink_version": "1.0.0",
        "cdss_model": OLLAMA_MODEL,
        "inference_time_seconds": round(elapsed, 2),
        "performance": raw_result.get("_performance", {}),
        "execution_mode": "LOCAL (RGPD compliant)",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

    return cdss_report


def format_cdss_report(cdss_report: Dict[str, Any]) -> str:
    """
    Formatea el informe CDSS en texto legible para la consola.

    Args:
        cdss_report: Diccionario con el informe CDSS de interpret_ecg().

    Returns:
        Texto formateado del informe clinico completo.
    """
    lines = []
    lines.append("")
    lines.append("=" * 72)
    lines.append("  INFORME CDSS - BiosenseLink Clinical Decision Support System")
    lines.append("=" * 72)

    # Verificar si hay error
    if "error" in cdss_report:
        lines.append(f"\n  [ERROR] {cdss_report['error']}")
        lines.append("=" * 72)
        return "\n".join(lines)

    # Disclaimer
    disclaimer = cdss_report.get("disclaimer", "")
    if disclaimer:
        lines.append(f"\n  AVISO: {disclaimer}")

    # Resumen cuantitativo
    quant = cdss_report.get("quantitative_summary", {})
    if quant:
        lines.append("\n  --- RESUMEN CUANTITATIVO ---")
        lines.append(f"  FC:  {quant.get('heart_rate_bpm', 'N/A')} lpm "
                     f"({quant.get('heart_rate_classification', 'N/A')})")
        lines.append(f"  PR:  {quant.get('pr_interval_ms', 'N/A')} ms")
        lines.append(f"  QRS: {quant.get('qrs_duration_ms', 'N/A')} ms")
        lines.append(f"  QTc: {quant.get('qtc_bazett_ms', 'N/A')} ms")
        lines.append(f"  ST:  {quant.get('st_deviation_mv', 'N/A')} mV")

    # Razonamiento clinico (Chain-of-Thought)
    reasoning = cdss_report.get("clinical_reasoning", "")
    if reasoning:
        lines.append("\n  --- RAZONAMIENTO CLINICO (Chain-of-Thought) ---")
        # Formatear en lineas de 68 caracteres
        words = reasoning.split()
        current_line = "  "
        for word in words:
            if len(current_line) + len(word) + 1 > 68:
                lines.append(current_line)
                current_line = "  " + word
            else:
                current_line += " " + word
        if current_line.strip():
            lines.append(current_line)

    # Hallazgos
    findings = cdss_report.get("findings", [])
    if findings:
        lines.append("\n  --- HALLAZGOS CLINICOS ---")
        severity_icon = {
            "NORMAL": "[OK]", "ATTENTION": "[!]",
            "ALERT": "[!!]", "CRITICAL": "[!!!]"
        }
        for f in findings:
            sev = f.get("severity", "N/A")
            icon = severity_icon.get(sev, "[?]")
            lines.append(f"\n  {icon} {sev}: {f.get('parameter', 'N/A')}")
            lines.append(f"      Valor:         {f.get('value', 'N/A')}")
            lines.append(f"      Interpretacion: {f.get('interpretation', 'N/A')}")
            snomed = f.get("snomed_ct_code")
            if snomed:
                lines.append(f"      SNOMED CT:     {snomed}")
            loinc = f.get("loinc_code")
            if loinc:
                lines.append(f"      LOINC:         {loinc}")
            lines.append(f"      Referencia:    {f.get('guideline_reference', 'N/A')}")

    # Diagnostico diferencial
    differentials = cdss_report.get("differential_diagnosis", [])
    if differentials:
        lines.append("\n  --- DIAGNOSTICO DIFERENCIAL ---")
        for i, dx in enumerate(differentials, 1):
            prob = dx.get("probability", "N/A")
            lines.append(f"\n  {i}. {dx.get('diagnosis', 'N/A')} "
                         f"[Probabilidad: {prob}]")
            icd = dx.get("icd11_code")
            if icd:
                lines.append(f"     ICD-11:     {icd}")
            lines.append(f"     Evidencia:  {dx.get('supporting_evidence', 'N/A')}")
            contra = dx.get("contradicting_evidence")
            if contra:
                lines.append(f"     Contra:     {contra}")

    # Acciones recomendadas
    actions = cdss_report.get("recommended_actions", [])
    if actions:
        lines.append("\n  --- ACCIONES RECOMENDADAS ---")
        for a in actions:
            urgency = a.get("urgency", "N/A")
            lines.append(f"\n  [{urgency}] {a.get('action', 'N/A')}")
            lines.append(f"    Justificacion: {a.get('rationale', 'N/A')}")

    # Metadatos de rendimiento
    meta = cdss_report.get("_pipeline_metadata", {})
    if meta:
        perf = meta.get("performance", {})
        lines.append("\n  --- METRICAS DEL PIPELINE ---")
        lines.append(f"  Modelo:            {meta.get('cdss_model', 'N/A')}")
        lines.append(f"  Tiempo inferencia: {meta.get('inference_time_seconds', 'N/A')}s")
        lines.append(f"  Tokens generados:  {perf.get('tokens_generated', 'N/A')}")
        lines.append(f"  Velocidad:         {perf.get('generation_speed_tps', 'N/A')} tokens/s")
        lines.append(f"  Modo:              {meta.get('execution_mode', 'N/A')}")

    lines.append("")
    lines.append("=" * 72)
    lines.append("  Este informe ha sido generado por BiosenseLink-CDSS v1.0")
    lines.append("  y requiere validacion por un profesional sanitario.")
    lines.append("=" * 72)

    return "\n".join(lines)


def _error_response(message: str) -> Dict[str, Any]:
    """Genera una respuesta de error estandarizada."""
    return {
        "error": message,
        "_pipeline_metadata": {
            "biosenselink_version": "1.0.0",
            "cdss_model": OLLAMA_MODEL,
            "execution_mode": "LOCAL",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    }


# ---------------------------------------------------------------------------
# Ejecucion standalone: Pipeline completo de analisis con IA
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from ecg_simulator import SCENARIOS
    from signal_processor import pipeline_clinical_standard
    from pqrst_analyzer import analyze_ecg

    print("=" * 72)
    print("  BiosenseLink CDSS - Pipeline Completo de Analisis ECG con IA")
    print("=" * 72)

    # Seleccionar escenario
    print("\n  Escenarios disponibles:")
    scenario_keys = list(SCENARIOS.keys())
    for i, key in enumerate(scenario_keys):
        print(f"    {i+1}. {SCENARIOS[key][0]}")

    try:
        choice = int(input("\n  Selecciona escenario (1-6): ")) - 1
        if choice < 0 or choice >= len(scenario_keys):
            choice = 0
    except (ValueError, EOFError):
        choice = 0

    scenario_key = scenario_keys[choice]
    scenario_name, generator = SCENARIOS[scenario_key]
    print(f"\n  Escenario seleccionado: {scenario_name}")

    # Paso 1: Generar senal ECG
    print("  [1/4] Generando senal ECG sintetica...")
    t, raw_ecg = generator(duration=10, sampling_rate=500)

    # Paso 2: Filtrar senal
    print("  [2/4] Aplicando pipeline clinico AHA (0.5-40 Hz)...")
    clean_ecg = pipeline_clinical_standard(raw_ecg, fs=500)

    # Paso 3: Analisis PQRST
    print("  [3/4] Ejecutando analisis PQRST algoritmico...")
    report = analyze_ecg(clean_ecg, sampling_rate=500)

    # Paso 4: Interpretacion CDSS con IA
    print("  [4/4] Solicitando interpretacion clinica al modelo CDSS...")
    cdss_result = interpret_ecg(report, scenario_name=scenario_name)

    # Mostrar informe
    print(format_cdss_report(cdss_result))

    # Guardar JSON crudo
    output_path = "../data/cdss_report.json"
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cdss_result, f, indent=2, ensure_ascii=False)
        print(f"\n  Informe JSON guardado en: {output_path}")
    except Exception as e:
        print(f"\n  [AVISO] No se pudo guardar el JSON: {e}")
