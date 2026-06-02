"""
==============================================================================
BiosenseLink - Exportador HL7 FHIR (R4)
==============================================================================
Convierte los informes de analisis PQRST y la interpretacion del modelo
CDSS a un 'Bundle' estandarizado HL7 FHIR (Fast Healthcare Interoperability
Resources) Release 4.

Utiliza la libreria oficial `fhir.resources` para garantizar el cumplimiento
estricto del esquema, permitiendo interoperabilidad directa con sistemas
EHR (Electronic Health Records) y HAPI FHIR Servers.

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import uuid
from datetime import datetime, timezone
import json

# Importaciones de recursos FHIR
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

# Importacion local
from pqrst_analyzer import ECGAnalysisReport


def export_to_fhir_bundle(report: ECGAnalysisReport, cdss_report: dict) -> str:
    """
    Genera un Bundle FHIR R4 en formato JSON string a partir del reporte ECG
    y la interpretacion de la IA.
    """
    # 1. Generar paciente simulado (John Doe)
    patient = _create_patient()
    patient_ref = Reference(reference=f"Patient/{patient.id}")

    # 2. Crear las observaciones (Métricas cuantitativas)
    observations = []
    
    # Frecuencia cardiaca (LOINC: 8867-4)
    obs_hr = _create_observation(
        code="8867-4", display="Heart rate", system="http://loinc.org",
        value=report.mean_heart_rate, unit="/min", unit_code="/min",
        patient_ref=patient_ref
    )
    observations.append(obs_hr)

    # Intervalo PR (LOINC: 46087-3)
    obs_pr = _create_observation(
        code="46087-3", display="PR interval", system="http://loinc.org",
        value=report.mean_pr_interval_ms, unit="ms", unit_code="ms",
        patient_ref=patient_ref
    )
    observations.append(obs_pr)

    # Duracion QRS (LOINC: 46088-1)
    obs_qrs = _create_observation(
        code="46088-1", display="QRS duration", system="http://loinc.org",
        value=report.mean_qrs_duration_ms, unit="ms", unit_code="ms",
        patient_ref=patient_ref
    )
    observations.append(obs_qrs)

    # QTc Interval (LOINC: 8636-4)
    obs_qtc = _create_observation(
        code="8636-4", display="QTc interval", system="http://loinc.org",
        value=report.mean_qtc_ms, unit="ms", unit_code="ms",
        patient_ref=patient_ref
    )
    observations.append(obs_qtc)

    # 3. Crear el DiagnosticReport
    diag_report = _create_diagnostic_report(patient_ref, observations, cdss_report)

    # 4. Empaquetar todo en un Bundle (tipo collection o document)
    entries = []
    
    # Añadir Patient
    entries.append(BundleEntry(fullUrl=f"urn:uuid:{patient.id}", resource=patient))

    # Añadir Observations
    for obs in observations:
        entries.append(BundleEntry(fullUrl=f"urn:uuid:{obs.id}", resource=obs))

    # Añadir DiagnosticReport
    entries.append(BundleEntry(fullUrl=f"urn:uuid:{diag_report.id}", resource=diag_report))

    bundle = Bundle(
        type="collection",
        timestamp=datetime.now(timezone.utc).isoformat(),
        entry=entries
    )

    # Validar y exportar a JSON
    return bundle.json(indent=2)


def _create_patient() -> Patient:
    return Patient(id=str(uuid.uuid4()), active=True)


def _create_observation(code, display, system, value, unit, unit_code, patient_ref) -> Observation:
    coding = Coding(system=system, code=code, display=display)
    cc = CodeableConcept(coding=[coding])
    val = Quantity(value=float(value), unit=unit, system="http://unitsofmeasure.org", code=unit_code)
    
    return Observation(
        id=str(uuid.uuid4()),
        status="final",
        subject=patient_ref,
        code=cc,
        valueQuantity=val
    )


def _create_diagnostic_report(patient_ref, observations, cdss_report) -> DiagnosticReport:
    coding = Coding(system="http://loinc.org", code="11524-6", display="EKG study")
    cc = CodeableConcept(coding=[coding])
    
    result_refs = [Reference(reference=f"Observation/{obs.id}") for obs in observations]
    
    conclusions = []
    if "differential_diagnosis" in cdss_report and isinstance(cdss_report["differential_diagnosis"], list) and len(cdss_report["differential_diagnosis"]) > 0:
        top_dx = cdss_report["differential_diagnosis"][0]
        conclusions.append(f"Primary DX: {top_dx.get('condition', 'Unknown')} (Prob: {top_dx.get('probability', '')})")
    
    if "reasoning_chain" in cdss_report:
        conclusions.append(f"AI Reasoning: {cdss_report['reasoning_chain'][:500]}...")

    return DiagnosticReport(
        id=str(uuid.uuid4()),
        status="final",
        subject=patient_ref,
        code=cc,
        result=result_refs,
        conclusion=" | ".join(conclusions)
    )


if __name__ == "__main__":
    from ecg_simulator import generate_stemi_anterior
    from signal_processor import pipeline_clinical_standard
    from pqrst_analyzer import analyze_ecg
    
    # Prueba rapida
    _, df = generate_stemi_anterior(duration=5)
    clean = pipeline_clinical_standard(df)
    rep = analyze_ecg(clean)
    
    fake_cdss = {
        "reasoning_chain": "ST elevation in V2-V4 implies anterior STEMI.",
        "differential_diagnosis": [
            {"condition": "Anterior STEMI", "probability": "HIGH"}
        ]
    }
    
    fhir_json = export_to_fhir_bundle(rep, fake_cdss)
    print(fhir_json[:500] + "\n...\n")
    print("FHIR Bundle validado generado exitosamente.")
