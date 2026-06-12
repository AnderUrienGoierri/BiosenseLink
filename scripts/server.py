import asyncio
import json
import os
import logging
import psycopg2
import sys
import io

# Forzar UTF-8 en stdout/stderr para compatibilidad con Windows (CP1252 no soporta emojis)
if sys.stdout.encoding and sys.stdout.encoding.upper() != 'UTF-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.upper() != 'UTF-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import subprocess
import urllib.request
import random
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Modulos locales (BiosenseLink Core)
from ecg_simulator import SCENARIOS
from signal_processor import pipeline_clinical_standard
from pqrst_analyzer import analyze_ecg
from fhir_exporter import export_to_fhir_bundle

# Configuracion de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BiosenseLink-Server")

app = FastAPI(title="BiosenseLink IoMT Backend", version="1.0")

# Permitir CORS para el frontend (Capacitor/Browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global del backend
state = {
    "current_scenario": "normal",
    "sampling_rate": 500,
    "duration": 10,
    "time": None,
    "raw_ecg": None,
    "filtered_ecg": None,
    "report": None,
    "active_connections": [],
    
    # Nuevas variables de estado clínico para el puerto 8081
    "interval": 5.0,
    "noise": 0.0,
    "is_paused": False,
    "active_device": "welch-allyn",
    "active_state": "normal",
    "current_patient_id": "ander-patient",
    "current_patient_name": "Ander Unicornio",
    "current_patient_age": 28,
    "current_patient_gender": "MALE",
    "current_patient_pathology": "NONE"
}

cycle_counter = 0
_fhir_id_counter = random.randint(95000, 99000)

POC_METRICS_METADATA = [
    # Welch Allyn
    {"device": "WELCH-ALLYN", "name": "Heart rate", "loinc": "8867-4", "unit": "beats/min", "unit_code": "/min", "key": "hr"},
    {"device": "WELCH-ALLYN", "name": "Oxygen saturation (SpO2)", "loinc": "2708-6", "unit": "%", "unit_code": "%", "key": "spo2"},
    {"device": "WELCH-ALLYN", "name": "Body temperature", "loinc": "8310-5", "unit": "C", "unit_code": "Cel", "key": "temp"},
    {"device": "WELCH-ALLYN", "name": "Systolic blood pressure", "loinc": "8480-6", "unit": "mmHg", "unit_code": "mm[Hg]", "key": "sbp"},
    {"device": "WELCH-ALLYN", "name": "Diastolic blood pressure", "loinc": "8462-4", "unit": "mmHg", "unit_code": "mm[Hg]", "key": "dbp"},
    
    # i-STAT Gas
    {"device": "ISTAT-GAS", "name": "pH of Arterial blood", "loinc": "11557-6", "unit": "pH", "unit_code": "pH", "key": "ph"},
    {"device": "ISTAT-GAS", "name": "pCO2 (Arterial blood)", "loinc": "2019-8", "unit": "mmHg", "unit_code": "mm[Hg]", "key": "pco2"},
    {"device": "ISTAT-GAS", "name": "pO2 (Arterial blood)", "loinc": "2703-7", "unit": "mmHg", "unit_code": "mm[Hg]", "key": "po2"},
    {"device": "ISTAT-GAS", "name": "Lactate in Blood", "loinc": "2524-7", "unit": "mmol/L", "unit_code": "mmol/L", "key": "lactate"},
    
    # Accu-Chek
    {"device": "ACCU-CHEK", "name": "Glucose in Blood", "loinc": "2339-0", "unit": "mg/dL", "unit_code": "mg/dL", "key": "glucose"},
    {"device": "ACCU-CHEK", "name": "Ketones in Blood", "loinc": "3167-4", "unit": "mg/dL", "unit_code": "mg/dL", "key": "ketones"},
    
    # CoaguChek
    {"device": "COAGUCHEK", "name": "Prothrombin time (PT)", "loinc": "46418-2", "unit": "s", "unit_code": "s", "key": "pt"},
    {"device": "COAGUCHEK", "name": "INR (Coagulation)", "loinc": "34714-6", "unit": "{INR}", "unit_code": "{INR}", "key": "inr"},
    
    # Alere Triage
    {"device": "ALERE-TRIAGE", "name": "Troponin I (Cardiac)", "loinc": "10839-9", "unit": "ng/mL", "unit_code": "ng/mL", "key": "troponin"},
    {"device": "ALERE-TRIAGE", "name": "Natriuretic peptide B (BNP)", "loinc": "30934-4", "unit": "pg/mL", "unit_code": "pg/mL", "key": "bnp"},
    
    # HIV Monitor
    {"device": "HIV-MONITOR", "name": "HIV 1 Viral Load", "loinc": "70241-5", "unit": "copies/mL", "unit_code": "copies/mL", "key": "viral_load"},
    {"device": "HIV-MONITOR", "name": "CD4 Cells count", "loinc": "24467-3", "unit": "cells/uL", "unit_code": "cells/uL", "key": "cd4"}
]

def generate_poc_metrics(active_state: str):
    # Base presets for all metrics under normal conditions
    metrics = {
        # Welch Allyn (Vital Signs)
        "hr": 72.0,
        "spo2": 98.0,
        "temp": 36.6,
        "sbp": 120.0,
        "dbp": 80.0,
        
        # i-STAT Gas (Arterial Blood Gas)
        "ph": 7.40,
        "pco2": 40.0,
        "po2": 95.0,
        "lactate": 0.9,
        
        # Accu-Chek (Metabolic)
        "glucose": 90.0,
        "ketones": 0.2,
        
        # CoaguChek (Coagulation)
        "pt": 12.0,
        "inr": 1.0,
        
        # Alere Triage (Cardiac Markers)
        "troponin": 0.02,
        "bnp": 35.0,
        
        # HIV Monitor (Virology)
        "viral_load": 0.0,
        "cd4": 650.0
    }
    
    # Modify based on active_state
    if active_state == "pcr":
        metrics["hr"] = 0.0
        metrics["spo2"] = 0.0
        metrics["temp"] = 35.5
        metrics["sbp"] = 0.0
        metrics["dbp"] = 0.0
        metrics["ph"] = 7.15
        metrics["pco2"] = 65.0
        metrics["po2"] = 25.0
        metrics["lactate"] = 8.5
    elif active_state == "shock":
        metrics["hr"] = 125.0
        metrics["spo2"] = 88.0
        metrics["temp"] = 36.8
        metrics["sbp"] = 85.0
        metrics["dbp"] = 50.0
        metrics["lactate"] = 4.2
    elif active_state == "crisis":
        metrics["hr"] = 95.0
        metrics["spo2"] = 97.0
        metrics["temp"] = 36.6
        metrics["sbp"] = 185.0
        metrics["dbp"] = 115.0
    elif active_state == "epoc":
        metrics["hr"] = 110.0
        metrics["spo2"] = 82.0
        metrics["temp"] = 37.2
        metrics["sbp"] = 130.0
        metrics["dbp"] = 85.0
        metrics["pco2"] = 58.0
        metrics["po2"] = 55.0
    elif active_state == "sepsis":
        metrics["hr"] = 118.0
        metrics["spo2"] = 96.0
        metrics["temp"] = 39.1
        metrics["sbp"] = 95.0
        metrics["dbp"] = 55.0
        metrics["lactate"] = 3.1
    elif active_state == "acidosis":
        metrics["ph"] = 7.21
        metrics["pco2"] = 32.0
        metrics["lactate"] = 5.2
    elif active_state == "alkalosis":
        metrics["ph"] = 7.52
        metrics["pco2"] = 28.0
    elif active_state == "diabetic-keto":
        metrics["glucose"] = 385.0
        metrics["ketones"] = 4.5
        metrics["ph"] = 7.18
    elif active_state == "hypoglycemia":
        metrics["glucose"] = 42.0
    elif active_state == "warfarin-overdose":
        metrics["pt"] = 45.0
        metrics["inr"] = 4.8
    elif active_state == "ami-infarct":
        metrics["hr"] = 115.0
        metrics["troponin"] = 3.8
        metrics["bnp"] = 245.0
    elif active_state == "therapeutic-failure":
        metrics["viral_load"] = 12500.0
        metrics["cd4"] = 380.0
    elif active_state == "aids-crisis":
        metrics["viral_load"] = 280000.0
        metrics["cd4"] = 85.0
        metrics["temp"] = 38.5
        
    # Introduce physiological fluctuations (if not flatlined by PCR)
    if active_state != "pcr":
        metrics["hr"] = max(30.0, min(220.0, metrics["hr"] + random.uniform(-1.5, 1.5)))
        metrics["spo2"] = max(40.0, min(100.0, metrics["spo2"] + random.uniform(-0.5, 0.5)))
        metrics["temp"] = max(34.0, min(43.0, metrics["temp"] + random.uniform(-0.05, 0.05)))
        metrics["sbp"] = max(50.0, min(240.0, metrics["sbp"] + random.uniform(-2.0, 2.0)))
        metrics["dbp"] = max(30.0, min(150.0, metrics["dbp"] + random.uniform(-1.5, 1.5)))
        
        metrics["ph"] = max(6.8, min(7.8, metrics["ph"] + random.uniform(-0.01, 0.01)))
        metrics["pco2"] = max(10.0, min(100.0, metrics["pco2"] + random.uniform(-0.8, 0.8)))
        metrics["po2"] = max(20.0, min(200.0, metrics["po2"] + random.uniform(-1.2, 1.2)))
        metrics["lactate"] = max(0.2, min(25.0, metrics["lactate"] + random.uniform(-0.05, 0.05)))
        
        metrics["glucose"] = max(10.0, min(600.0, metrics["glucose"] + random.uniform(-3.0, 3.0)))
        metrics["ketones"] = max(0.0, min(10.0, metrics["ketones"] + random.uniform(-0.02, 0.02)))
        
        metrics["pt"] = max(5.0, min(100.0, metrics["pt"] + random.uniform(-0.15, 0.15)))
        metrics["inr"] = max(0.5, min(15.0, metrics["inr"] + random.uniform(-0.05, 0.05)))
        
        metrics["troponin"] = max(0.01, min(50.0, metrics["troponin"] + random.uniform(-0.002, 0.002)))
        metrics["bnp"] = max(5.0, min(5000.0, metrics["bnp"] + random.uniform(-1.5, 1.5)))
        
        metrics["viral_load"] = max(0.0, metrics["viral_load"] + random.uniform(-10.0, 10.0) if metrics["viral_load"] > 0 else 0)
        metrics["cd4"] = max(10.0, min(1500.0, metrics["cd4"] + random.uniform(-4.0, 4.0)))
        
    return metrics

def post_fhir_observation(obs_payload) -> str:
    global _fhir_id_counter
    try:
        req_data = json.dumps(obs_payload).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8080/fhir/Observation",
            data=req_data,
            headers={
                "Content-Type": "application/fhir+json; charset=utf-8",
                "Accept": "application/fhir+json"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status in [200, 201]:
                res_body = json.loads(resp.read().decode('utf-8'))
                return res_body.get("id", str(_fhir_id_counter))
    except Exception:
        pass
    
    # Fallback to auto-incrementing ID if HAPI FHIR is not responding
    _fhir_id_counter += 1
    return str(_fhir_id_counter)

def update_simulation():
    """Genera nueva senal basada en el escenario actual."""
    scenario_func = SCENARIOS[state["current_scenario"]][1]
    t, df = scenario_func(duration=state["duration"], sampling_rate=state["sampling_rate"])
    state["time"] = t
    state["raw_ecg"] = df
    
    # Pre-procesar para analisis
    df_filt = pipeline_clinical_standard(df, state["sampling_rate"])
    state["filtered_ecg"] = df_filt
    
    # Pre-analizar
    try:
        report = analyze_ecg(df_filt, state["sampling_rate"])
        state["report"] = report
    except Exception as e:
        logger.error(f"Error en analisis: {e}")
        state["report"] = None

# Inicializar primera simulacion
update_simulation()


# --- MODELOS PYDANTIC ---
class LoginRequest(BaseModel):
    pin: str

class TriageRequest(BaseModel):
    triage: str

class PatientConfigRequest(BaseModel):
    id: str
    name: str
    gender: str
    age: int
    weight: float
    height: float
    pathology: str


# --- FUNCIONES AUXILIARES DE INTEGRACIÓN FHIR ---
# --- FUNCIONES AUXILIARES DE INTEGRACIÓN FHIR ---
async def post_single_obs(met, value, patient_id, now_str):
    obs_payload = {
        "resourceType": "Observation",
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": met["loinc"],
                    "display": met["name"]
                }
            ]
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": now_str,
        "valueQuantity": {
            "value": round(float(value), 3),
            "unit": met["unit"],
            "system": "http://unitsofmeasure.org",
            "code": met["unit_code"]
        }
    }
    fhir_id = await asyncio.to_thread(post_fhir_observation, obs_payload)
    return met, value, fhir_id

def inject_fhir_observations(patient_id: str, state_code: str):
    """
    Genera e inyecta TODOS los recursos FHIR Observation correspondientes a todos los dispositivos PoC
    en el servidor HAPI FHIR (puerto 8080) según el estado clínico inducido.
    """
    now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    presets = generate_poc_metrics(state_code)
    
    success_count = 0
    results = []
    
    for met in POC_METRICS_METADATA:
        value = presets[met["key"]]
        obs_payload = {
            "resourceType": "Observation",
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs"
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": met["loinc"],
                        "display": met["name"]
                    }
                ]
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "effectiveDateTime": now_str,
            "valueQuantity": {
                "value": round(float(value), 3),
                "unit": met["unit"],
                "system": "http://unitsofmeasure.org",
                "code": met["unit_code"]
            }
        }
        
        fhir_id = post_fhir_observation(obs_payload)
        if fhir_id != str(_fhir_id_counter):
            success_count += 1
        results.append((met, value, fhir_id))
            
    # Print beautiful telemetry log in the console even for manual injection
    now_time = datetime.now().strftime("%H:%M:%S")
    print("\n" + "═" * 102)
    print(f"📥 \033[93m[Inyección Manual - {now_time}] Detección de Evento Clínico en Tiempo Real\033[0m")
    print(f"\033[37m[Paciente: {state.get('current_patient_name', 'Desconocido')} ({state.get('current_patient_age', 0)} años, {state.get('current_patient_gender', 'MALE')}) - Diagnóstico Crónico: {state.get('current_patient_pathology', 'NONE')}]\033[0m")
    print(f"\033[37m[Dispositivo Principal Activo: {state.get('active_device', 'welch-allyn').upper()} - Triage Solicitado: {state_code.upper()}]\033[0m")
    
    # Box-drawing table header
    print("┌" + "─" * 58 + "┬" + "─" * 12 + "┬" + "─" * 15 + "┬" + "─" * 12 + "┐")
    print(f"│ ⚡ \033[97m{'Dispositivo e Indicador Clínico':<53}\033[0m │ \033[97m{'Valor':>10}\033[0m │ \033[97m{'Unidad':<13}\033[0m │ \033[97m{'FHIR ID':<10}\033[0m │")
    print("├" + "─" * 58 + "┼" + "─" * 12 + "┼" + "─" * 15 + "┼" + "─" * 12 + "┤")
    
    for met, val, fhir_id in results:
        device_part = f"[{met['device']}]"
        metric_name = met['name']
        left_side = f"{device_part} {metric_name}"
        print(f"│   \033[37m{left_side:<54}\033[0m │ \033[92m{val:>10.3f}\033[0m │ \033[36m{met['unit']:<13}\033[0m │ \033[90m{fhir_id:<10}\033[0m │")
        
    print("└" + "─" * 58 + "┴" + "─" * 12 + "┴" + "─" * 15 + "┴" + "─" * 12 + "┘")
    
    # EKG real-time lead monitoring section
    df_filt = state.get("filtered_ecg")
    if df_filt is not None and not df_filt.empty:
        s = df_filt.iloc[random.randint(0, len(df_filt) - 1)]
        print("🩺 \033[93m[MONITOREO DE SEÑAL EKG - 12 DERIVACIONES EN TIEMPO REAL (Muestra instantánea, mV)]\033[0m")
        print("┌" + "─" * 27 + "┬" + "─" * 27 + "┬" + "─" * 27 + "┐")
        print("│ \033[95mBipolares (Einthoven)\033[0m     │ \033[95mAumentadas (Goldberger)\033[0m   │ \033[95mPrecordiales (Wilson)\033[0m     │")
        print("├" + "─" * 27 + "┼" + "─" * 27 + "┼" + "─" * 27 + "┤")
        rows = [
            ("I:   ", s.get("I", 0.0), "aVR: ", s.get("aVR", 0.0), "V1:  ", s.get("V1", 0.0)),
            ("II:  ", s.get("II", 0.0), "aVL: ", s.get("aVL", 0.0), "V2:  ", s.get("V2", 0.0)),
            ("III: ", s.get("III", 0.0), "aVF: ", s.get("aVF", 0.0), "V3:  ", s.get("V3", 0.0)),
            ("", None, "", None, "V4:  ", s.get("V4", 0.0)),
            ("", None, "", None, "V5:  ", s.get("V5", 0.0)),
            ("", None, "", None, "V6:  ", s.get("V6", 0.0)),
        ]
        for r1_lbl, r1_val, r2_lbl, r2_val, r3_lbl, r3_val in rows:
            c1_str = f"{r1_lbl}{r1_val:>7.3f} mV" if r1_val is not None else ""
            c1_color = f" {r1_lbl}\033[36m{r1_val:>7.3f} mV\033[0m" + " " * (26 - len(c1_str)) if r1_val is not None else " " * 27
            
            c2_str = f"{r2_lbl}{r2_val:>7.3f} mV" if r2_val is not None else ""
            c2_color = f" {r2_lbl}\033[36m{r2_val:>7.3f} mV\033[0m" + " " * (26 - len(c2_str)) if r2_val is not None else " " * 27
            
            c3_str = f"{r3_lbl}{r3_val:>7.3f} mV" if r3_val is not None else ""
            c3_color = f" {r3_lbl}\033[36m{r3_val:>7.3f} mV\033[0m" + " " * (26 - len(c3_str)) if r3_val is not None else " " * 27
            
            print(f"│{c1_color}│{c2_color}│{c3_color}│")
        print("└" + "─" * 27 + "┴" + "─" * 27 + "┴" + "─" * 27 + "┘")
        
    print("═" * 102)


async def continuous_vitals_simulator():
    """
    Tarea en segundo plano que inyecta vitales de todos los dispositivos PoC
    con fluctuaciones fisiológicas continuas cada 'interval' segundos.
    """
    global cycle_counter
    logger.info("Iniciando bucle continuo de telemetría médica descentralizada...")
    await asyncio.sleep(2.0)
    
    while True:
        try:
            is_paused = state["is_paused"]
            interval = state["interval"]
            active_state = state["active_state"]
            patient_id = state["current_patient_id"]
            
            if not is_paused:
                cycle_counter += 1
                now_str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                generated_values = generate_poc_metrics(active_state)
                
                # Post all observations concurrently in parallel to HAPI FHIR!
                tasks = [
                    post_single_obs(met, generated_values[met["key"]], patient_id, now_str)
                    for met in POC_METRICS_METADATA
                ]
                results = await asyncio.gather(*tasks)
                
                # Print beautiful clinical logs
                now_time = datetime.now().strftime("%H:%M:%S")
                print("\n" + "═" * 102)
                print(f"🗂️  \033[96m[Ciclo #{cycle_counter} - {now_time}] Transmitiendo telemetría con transiciones fluidas hacia HAPI FHIR\033[0m")
                print(f"\033[37m[Paciente: {state.get('current_patient_name', 'Desconocido')} ({state.get('current_patient_age', 0)} años, {state.get('current_patient_gender', 'MALE')}) - Diagnóstico Crónico: {state.get('current_patient_pathology', 'NONE')}]\033[0m")
                print(f"\033[37m[Dispositivo Principal Activo: {state.get('active_device', 'welch-allyn').upper()} - Escenario Triage: {active_state.upper()}]\033[0m")
                
                # Box-drawing table header
                print("┌" + "─" * 58 + "┬" + "─" * 12 + "┬" + "─" * 15 + "┬" + "─" * 12 + "┐")
                print(f"│ ⚡ \033[97m{'Dispositivo e Indicador Clínico':<53}\033[0m │ \033[97m{'Valor':>10}\033[0m │ \033[97m{'Unidad':<13}\033[0m │ \033[97m{'FHIR ID':<10}\033[0m │")
                print("├" + "─" * 58 + "┼" + "─" * 12 + "┼" + "─" * 15 + "┼" + "─" * 12 + "┤")
                
                for met, val, fhir_id in results:
                    device_part = f"[{met['device']}]"
                    metric_name = met['name']
                    left_side = f"{device_part} {metric_name}"
                    print(f"│   \033[37m{left_side:<54}\033[0m │ \033[92m{val:>10.3f}\033[0m │ \033[36m{met['unit']:<13}\033[0m │ \033[90m{fhir_id:<10}\033[0m │")
                    
                print("└" + "─" * 58 + "┴" + "─" * 12 + "┴" + "─" * 15 + "┴" + "─" * 12 + "┘")
                
                # EKG real-time lead monitoring section
                df_filt = state.get("filtered_ecg")
                if df_filt is not None and not df_filt.empty:
                    s = df_filt.iloc[random.randint(0, len(df_filt) - 1)]
                    print("🩺 \033[93m[MONITOREO DE SEÑAL EKG - 12 DERIVACIONES EN TIEMPO REAL (Muestra instantánea, mV)]\033[0m")
                    print("┌" + "─" * 27 + "┬" + "─" * 27 + "┬" + "─" * 27 + "┐")
                    print("│ \033[95mBipolares (Einthoven)\033[0m     │ \033[95mAumentadas (Goldberger)\033[0m   │ \033[95mPrecordiales (Wilson)\033[0m     │")
                    print("├" + "─" * 27 + "┼" + "─" * 27 + "┼" + "─" * 27 + "┤")
                    rows = [
                        ("I:   ", s.get("I", 0.0), "aVR: ", s.get("aVR", 0.0), "V1:  ", s.get("V1", 0.0)),
                        ("II:  ", s.get("II", 0.0), "aVL: ", s.get("aVL", 0.0), "V2:  ", s.get("V2", 0.0)),
                        ("III: ", s.get("III", 0.0), "aVF: ", s.get("aVF", 0.0), "V3:  ", s.get("V3", 0.0)),
                        ("", None, "", None, "V4:  ", s.get("V4", 0.0)),
                        ("", None, "", None, "V5:  ", s.get("V5", 0.0)),
                        ("", None, "", None, "V6:  ", s.get("V6", 0.0)),
                    ]
                    for r1_lbl, r1_val, r2_lbl, r2_val, r3_lbl, r3_val in rows:
                        c1_str = f"{r1_lbl}{r1_val:>7.3f} mV" if r1_val is not None else ""
                        c1_color = f" {r1_lbl}\033[36m{r1_val:>7.3f} mV\033[0m" + " " * (26 - len(c1_str)) if r1_val is not None else " " * 27
                        
                        c2_str = f"{r2_lbl}{r2_val:>7.3f} mV" if r2_val is not None else ""
                        c2_color = f" {r2_lbl}\033[36m{r2_val:>7.3f} mV\033[0m" + " " * (26 - len(c2_str)) if r2_val is not None else " " * 27
                        
                        c3_str = f"{r3_lbl}{r3_val:>7.3f} mV" if r3_val is not None else ""
                        c3_color = f" {r3_lbl}\033[36m{r3_val:>7.3f} mV\033[0m" + " " * (26 - len(c3_str)) if r3_val is not None else " " * 27
                        
                        print(f"│{c1_color}│{c2_color}│{c3_color}│")
                    print("└" + "─" * 27 + "┴" + "─" * 27 + "┴" + "─" * 27 + "┘")
                
                print("═" * 102 + "\n")
                
        except Exception as e:
            logger.error(f"Error en bucle automático de telemetría: {e}")
            
        await asyncio.sleep(state["interval"])


@app.on_event("startup")
async def startup_event():
    print("\033[92m[OK] Servidor HTTP de control interactivo activo en: http://localhost:8081/api/control\033[0m")
    print("\033[32m[ON] Capa de telemetria e inyeccion activa hacia HAPI FHIR en el puerto 8080.\033[0m")
    # Lanzar la tarea asíncrona en el loop de FastAPI
    asyncio.create_task(continuous_vitals_simulator())


# --- ENDPOINTS REST ---

# --- ENDPOINTS CONTROL HOMER DOCKER ---
@app.get("/api/homer/status")
async def get_homer_status():
    try:
        process = await asyncio.create_subprocess_exec(
            "docker", "inspect", "-f", "{{.State.Status}}", "homer",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            status = stdout.decode().strip()
            return {"status": "ok", "container_status": status}
        else:
            return {"status": "error", "message": stderr.decode().strip(), "container_status": "not_found"}
    except Exception as e:
        return {"status": "error", "message": str(e), "container_status": "error"}

@app.post("/api/homer/start")
async def start_homer_container():
    try:
        process = await asyncio.create_subprocess_exec(
            "docker", "start", "homer",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return {"status": "ok", "message": "Homer iniciado con éxito"}
        else:
            return {"status": "error", "message": stderr.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/homer/stop")
async def stop_homer_container():
    try:
        process = await asyncio.create_subprocess_exec(
            "docker", "stop", "homer",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return {"status": "ok", "message": "Homer detenido con éxito"}
        else:
            return {"status": "error", "message": stderr.decode().strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}
db_connection_allowed = True

@app.get("/api/db/status")
async def get_db_status():
    global db_connection_allowed
    import psycopg2
    try:
        # Intentar conectar para verificar disponibilidad real
        conn = psycopg2.connect(
            host='localhost', 
            port=5432, 
            user='dbadmin', 
            password='SecuredHospitalPass2026!', 
            dbname='medical_platform',
            connect_timeout=2
        )
        conn.close()
        db_available = True
        details = "Base de datos PostgreSQL en puerto 5432 disponible."
    except Exception as e:
        db_available = False
        details = str(e)
        
    return {
        "status": "ok",
        "db_available": db_available,
        "db_connection_allowed": db_connection_allowed,
        "details": details
    }

@app.post("/api/db/connect")
async def post_db_connect():
    global db_connection_allowed
    db_connection_allowed = True
    return {"status": "ok", "db_connection_allowed": True}

@app.post("/api/db/disconnect")
async def post_db_disconnect():
    global db_connection_allowed
    db_connection_allowed = False
    return {"status": "ok", "db_connection_allowed": False}

@app.post("/api/auth")
async def authenticate(req: LoginRequest):
    global db_connection_allowed
    if not db_connection_allowed:
        return {"status": "error", "message": "Conexión a la base de datos deshabilitada por el administrador."}
    try:
        conn = psycopg2.connect(host='localhost', port=5432, user='dbadmin', password='SecuredHospitalPass2026!', dbname='medical_platform')
        cursor = conn.cursor()
        
        # Consultar BBDD Postgres por el PIN
        cursor.execute("SELECT role, display_name, title FROM clinical_users WHERE pin = %s", (req.pin,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            return {"status": "ok", "role": user[0], "display_name": user[1], "title": user[2]}
        else:
            return {"status": "error", "message": "Credenciales inválidas"}
            
    except Exception as e:
        logger.error(f"Error DB Auth: {e}")
        return {"status": "error", "message": "Error interno del servidor DB"}

@app.get("/api/scenarios")
async def get_scenarios():
    """Devuelve la lista de escenarios disponibles."""
    return [{"id": k, "name": v[0]} for k, v in SCENARIOS.items()]

@app.post("/api/scenario/{scenario_id}")
async def set_scenario(scenario_id: str):
    """Cambia el escenario fisiologico y fuerza actualizacion."""
    if scenario_id in SCENARIOS:
        state["current_scenario"] = scenario_id
        update_simulation()
        logger.info(f"Escenario cambiado a: {scenario_id}")
        return {"status": "ok", "message": f"Scenario changed to {scenario_id}"}
    return {"status": "error", "message": "Invalid scenario"}

@app.get("/api/analyze")
async def get_analysis_fhir():
    """Ejecuta CDSS y devuelve un FHIR Bundle."""
    if not state["report"]:
        return {"status": "error", "message": "No analysis available"}
        
    rep = state["report"]
    # Simulamos salida Ollama rapida para la demo online (CDSS)
    fake_cdss = {
        "differential_diagnosis": [{"condition": f.interpretation, "probability": "HIGH"} for f in rep.findings if f.severity in ["CRITICO", "ALERTA"]],
        "reasoning_chain": "Analisis topografico automatizado via motor Python en red local."
    }
    if not fake_cdss["differential_diagnosis"]:
        fake_cdss["differential_diagnosis"].append({"condition": "Normal Sinus Rhythm", "probability": "HIGH"})
        
    fhir_json = export_to_fhir_bundle(rep, fake_cdss)
    return {"status": "ok", "fhir_bundle": json.loads(fhir_json)}


# --- NUEVOS ENDPOINTS DE CONTROL REST PARA LA SUITE ---

@app.get("/api/control")
async def get_control(
    device: str = None,
    state_param: str = None,
    interval: float = None,
    noise: float = None,
    action: str = None,
    state: str = None
):
    """Controlador REST general de telemetria."""
    global_state = globals()["state"]
    if device is not None:
        global_state["active_device"] = device
        
    target_state = state if state is not None else state_param
    if target_state is not None:
        global_state["active_state"] = target_state
        
        # Mapear estado clinico a escenario de simulador de ECG
        scenario_map = {
            "normal": "normal",
            "pcr": "bradycardia", # La visualizacion simula asistolia en el frontend si es PCR
            "shock": "tachycardia",
            "crisis": "normal",
            "epoc": "tachycardia",
            "sepsis": "tachycardia"
        }
        mapped_scenario = scenario_map.get(target_state, "normal")
        if mapped_scenario in SCENARIOS:
            global_state["current_scenario"] = mapped_scenario
            update_simulation()
            
        # Inyectar automaticamente Observations en HAPI FHIR (8080)
        inject_fhir_observations(global_state["current_patient_id"], target_state)
        
    if interval is not None:
        global_state["interval"] = interval
        
    if noise is not None:
        global_state["noise"] = noise
        
    if action is not None:
        if action == "pause":
            global_state["is_paused"] = True
        elif action == "resume":
            global_state["is_paused"] = False
            
    return {
        "interval": global_state["interval"],
        "noise": global_state["noise"],
        "is_paused": global_state["is_paused"]
    }

@app.post("/api/config/triage")
async def config_triage(req: TriageRequest):
    """Sintoniza el simulador de biosensores con un triage especifico."""
    state["active_state"] = req.triage
    scenario_map = {
        "normal": "normal",
        "pcr": "bradycardia",
        "shock": "tachycardia",
        "crisis": "normal",
        "epoc": "tachycardia",
        "sepsis": "tachycardia"
    }
    mapped_scenario = scenario_map.get(req.triage, "normal")
    if mapped_scenario in SCENARIOS:
        state["current_scenario"] = mapped_scenario
        update_simulation()
    
    # Inyectar vitales en HAPI FHIR (8080)
    inject_fhir_observations(state["current_patient_id"], req.triage)
    
    logger.info(f"Escenario de triage inyectado: {req.triage} -> {mapped_scenario}")
    return {"status": "ok", "message": f"Triage {req.triage} configurado"}

@app.post("/api/config/patient")
async def config_patient(req: PatientConfigRequest):
    """Sincroniza el paciente activo en los biosensores."""
    state["current_patient_id"] = req.id
    state["current_patient_name"] = req.name
    state["current_patient_gender"] = req.gender
    state["current_patient_age"] = req.age
    state["current_patient_pathology"] = req.pathology
    logger.info(f"Paciente configurado en simulador Edge: {req.name} (ID: {req.id})")
    
    # Inyectar vitales base inmediatamente para el nuevo paciente
    inject_fhir_observations(req.id, state["active_state"])
    
    return {"status": "ok", "message": f"Paciente {req.name} sincronizado"}

@app.post("/api/run-launcher")
async def run_launcher():
    """Ejecuta Lanzar_BiosenseLink.sh en un terminal visible en Linux."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        sh_path = os.path.join(base_dir, "../Lanzar_BiosenseLink.sh")
        abs_sh_path = os.path.abspath(sh_path)
        logger.info(f"Ejecutando lanzador desde: {abs_sh_path}")
        
        # Detect available terminal emulators in order of preference
        terminals = [
            ["kitty", "--title", "BiosenseLink Telemetría IoMT", "bash", abs_sh_path],
            ["alacritty", "--title", "BiosenseLink Telemetría IoMT", "-e", "bash", abs_sh_path],
            ["konsole", "--title", "BiosenseLink Telemetría IoMT", "-e", "bash", abs_sh_path],
            ["gnome-terminal", "--title", "BiosenseLink Telemetría IoMT", "--", "bash", abs_sh_path],
            ["xterm", "-title", "BiosenseLink Telemetría IoMT", "-e", "bash", abs_sh_path],
        ]
        
        import shutil
        for term_args in terminals:
            if shutil.which(term_args[0]):
                subprocess.Popen(term_args, cwd=os.path.dirname(abs_sh_path), close_fds=True,
                                 start_new_session=True)
                return {"status": "ok", "message": f"Lanzador iniciado en terminal {term_args[0]}"}
        
        # Fallback: run in background without terminal
        subprocess.Popen(["bash", abs_sh_path], cwd=os.path.dirname(abs_sh_path), close_fds=True,
                         start_new_session=True)
        return {"status": "ok", "message": "Lanzador iniciado (sin terminal visual)"}
    except Exception as e:
        logger.error(f"Error al ejecutar lanzador: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/run-desktop-visualizer")
async def run_desktop_visualizer():
    """Ejecuta el visualizador de escritorio main.py en segundo plano en la PC."""
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        main_path = os.path.join(base_dir, "main.py")
        
        logger.info(f"Lanzando visualizador de escritorio desde: {main_path}")
        subprocess.Popen([sys.executable, main_path], close_fds=True)
        return {"status": "ok", "message": "Visualizador de escritorio iniciado"}
    except Exception as e:
        logger.error(f"Error iniciando visualizador de escritorio: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/gosasun/launch")
async def launch_gosasun():
    """Ejecuta la aplicación de escritorio GOsasun (C#) en segundo plano."""
    try:
        exe_path = r"C:\Dev\05_Projects\Goierri_MAD\PROGRAMAZIOA\C\proiektuak\GOsasun_app\publish\win-x64\GOsasun_app.exe"
        logger.info(f"Lanzando GOsasun App desde: {exe_path}")
        
        if not os.path.exists(exe_path):
            return {"status": "error", "message": f"No se encontró el ejecutable en {exe_path}"}
            
        subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path), close_fds=True)
        return {"status": "ok", "message": "GOsasun App iniciada correctamente"}
    except Exception as e:
        logger.error(f"Error iniciando GOsasun App: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/mysql-workbench/launch")
async def launch_mysql_workbench():
    """Ejecuta MySQL Workbench en segundo plano si está instalado en la ruta predeterminada."""
    try:
        paths = [
            r"C:\Program Files\MySQL\MySQL Workbench 8.0\MySQLWorkbench.exe",
            r"C:\Program Files\MySQL\MySQL Workbench 8.0 CE\MySQLWorkbench.exe"
        ]
        exe_path = None
        for p in paths:
            if os.path.exists(p):
                exe_path = p
                break
                
        if not exe_path:
            return {"status": "error", "message": "No se encontró MySQL Workbench en las rutas predeterminadas"}
            
        logger.info(f"Lanzando MySQL Workbench desde: {exe_path}")
        subprocess.Popen([exe_path], cwd=os.path.dirname(exe_path), close_fds=True)
        return {"status": "ok", "message": "MySQL Workbench iniciado"}
    except Exception as e:
        logger.error(f"Error iniciando MySQL Workbench: {e}")
        return {"status": "error", "message": str(e)}


import httpx
import urllib.parse
from fastapi import Request, Response

@app.get("/api/proxy")
async def web_proxy(request: Request, url: str):
    """
    Proxy que obtiene el contenido de una URL externa o local,
    elimina las cabeceras que bloquean el iframe (X-Frame-Options, CSP)
    e inyecta la etiqueta <base href="..."> y un script para notificar
    el éxito de carga al dashboard de Homer.
    """
    raw_query = request.url.query
    if "url=" in raw_query:
        target_url = raw_query.split("url=", 1)[1]
        target_url = urllib.parse.unquote(target_url)
    else:
        target_url = url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Desactivamos verificación SSL para Cockpit y otros servicios locales autoprofirmados
        async with httpx.AsyncClient(verify=False) as client:
            resp = await client.get(target_url, headers=headers, follow_redirects=True, timeout=10.0)
    except Exception as e:
        logger.error(f"Error en proxy al conectar con {target_url}: {e}")
        return Response(
            content=f"<h3>Error de Conexión en el Proxy</h3><p>No se pudo conectar con <b>{target_url}</b>.</p><p>Detalle: {str(e)}</p>",
            status_code=502,
            media_type="text/html"
        )

    content_type = resp.headers.get("content-type", "")
    body = resp.content

    # Si la respuesta es HTML, inyectamos la etiqueta <base> y el script de notificación de carga
    if "text/html" in content_type:
        try:
            html = resp.text
            final_url = str(resp.url)
            base_tag = f'<base href="{final_url}"><style>html {{ display: block !important; }}</style>'
            
            parsed = urllib.parse.urlparse(final_url)
            target_origin = f"{parsed.scheme}://{parsed.netloc}"
            ws_scheme = "wss" if parsed.scheme == "https" else "ws"
            target_ws_origin = f"{ws_scheme}://{parsed.netloc}"
            
            interceptor_script = f"""
<script>
  (function() {{
    const targetOrigin = '{target_origin}';
    const targetWsOrigin = '{target_ws_origin}';
    
    // Interceptar fetch
    const originalFetch = window.fetch;
    window.fetch = function(input, init) {{
      let url = typeof input === 'string' ? input : (input instanceof Request ? input.url : '');
      if (url) {{
        if (url.startsWith('/')) {{
          url = targetOrigin + url;
        }} else if (url.startsWith('http://localhost:8081/')) {{
          url = url.replace('http://localhost:8081', targetOrigin);
        }} else if (url.startsWith('http://127.0.0.1:8081/')) {{
          url = url.replace('http://127.0.0.1:8081', targetOrigin);
        }}
        if (typeof input === 'string') {{
          input = url;
        }} else if (input instanceof Request) {{
          input = new Request(url, input);
        }}
      }}
      return originalFetch(input, init);
    }};
    
    // Interceptar XMLHttpRequest (XHR)
    const OriginalXHR = window.XMLHttpRequest;
    window.XMLHttpRequest = function() {{
      const xhr = new OriginalXHR();
      const originalOpen = xhr.open;
      xhr.open = function(method, url, ...args) {{
        if (typeof url === 'string') {{
          if (url.startsWith('/')) {{
            url = targetOrigin + url;
          }} else if (url.startsWith('http://localhost:8081/')) {{
            url = url.replace('http://localhost:8081', targetOrigin);
          }} else if (url.startsWith('http://127.0.0.1:8081/')) {{
            url = url.replace('http://127.0.0.1:8081', targetOrigin);
          }}
        }}
        return originalOpen.call(this, method, url, ...args);
      }};
      return xhr;
    }};
    
    // Interceptar WebSocket
    const OriginalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {{
      if (typeof url === 'string') {{
        if (url.startsWith('/')) {{
          url = targetWsOrigin + url;
        }} else if (url.startsWith('ws://localhost:8081/')) {{
          url = url.replace('ws://localhost:8081', targetWsOrigin);
        }} else if (url.startsWith('wss://localhost:8081/')) {{
          url = url.replace('wss://localhost:8081', targetWsOrigin);
        }} else if (url.startsWith('ws://127.0.0.1:8081/')) {{
          url = url.replace('ws://127.0.0.1:8081', targetWsOrigin);
        }} else if (url.startsWith('wss://127.0.0.1:8081/')) {{
          url = url.replace('wss://127.0.0.1:8081', targetWsOrigin);
        }}
        
        // Ajustar el puerto para el WebSocket de sensing si es necesario
        if (url.includes('/ws/sensing')) {{
          url = url.replace(':3030/ws/sensing', ':3031/ws/sensing')
                   .replace(':3000/ws/sensing', ':3001/ws/sensing')
                   .replace(':8080/ws/sensing', ':8765/ws/sensing');
        }}
      }}
      return new OriginalWebSocket(url, protocols);
    }};
    window.WebSocket.prototype = OriginalWebSocket.prototype;
  }})();
</script>
"""
            combined_tag = base_tag + interceptor_script
            
            # Script inline que envía un mensaje postMessage al padre (Homer Dashboard) al cargar con éxito
            status_script = """
<script>
  try {
    if (window.parent) {
      window.parent.postMessage({ type: 'iframe_load_status', status: 'success' }, '*');
    }
  } catch (e) {
    console.error("Error al enviar estado de carga del iframe:", e);
  }
</script>
"""
            # Insertar base_tag e interceptor_script en <head>
            if "<head>" in html:
                html = html.replace("<head>", f"<head>{combined_tag}", 1)
            elif "<HEAD>" in html:
                html = html.replace("<HEAD>", f"<HEAD>{combined_tag}", 1)
            elif "<html>" in html:
                html = html.replace("<html>", f"<html>{combined_tag}", 1)
            elif "<HTML>" in html:
                html = html.replace("<HTML>", f"<HTML>{combined_tag}", 1)
            else:
                html = combined_tag + html
                
            # Insertar status_script antes de </body> o al final del archivo
            if "</body>" in html:
                html = html.replace("</body>", f"{status_script}</body>", 1)
            elif "</BODY>" in html:
                html = html.replace("</BODY>", f"{status_script}</BODY>", 1)
            else:
                html = html + status_script
                
            body = html.encode("utf-8")
        except Exception as e:
            logger.error(f"Error al procesar HTML en proxy para {target_url}: {e}")

    # Limpiar cabeceras de respuesta conflictivas
    exclude_headers = {
        "content-length",
        "content-encoding",
        "transfer-encoding",
        "x-frame-options",
        "content-security-policy",
        "x-content-security-policy",
        "connection",
        "keep-alive"
    }
    
    resp_headers = {}
    for k, v in resp.headers.items():
        if k.lower() not in exclude_headers:
            resp_headers[k] = v

    return Response(
        content=body,
        status_code=resp.status_code,
        headers=resp_headers,
        media_type=content_type
    )


# --- ENDPOINTS WEBSOCKET ---

@app.websocket("/ws/ecg")
async def websocket_ecg_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint que envia chunks del ECG 12-lead a alta velocidad
    para simular un monitor en tiempo real en el dashboard frontend.
    """
    await websocket.accept()
    state["active_connections"].append(websocket)
    logger.info("Cliente Web/Movil conectado al stream ECG.")
    
    try:
        chunk_size = 50 # Enviar de 50 en 50 muestras (100ms a 500Hz)
        idx = 0
        df = state["filtered_ecg"]
        t = state["time"]
        max_len = len(t)
        
        while True:
            # Si la visualizacion es PCR, sobreescribir la señal con asistolia (plana/0) en el stream
            is_pcr = (state["active_state"] == "pcr")
            
            # Si cambiaron el escenario, actualizamos variables locales
            df = state["filtered_ecg"]
            t = state["time"]
            
            end_idx = idx + chunk_size
            if end_idx >= max_len:
                # Resetear y generar nueva variabilidad (nuevo latido)
                update_simulation()
                df = state["filtered_ecg"]
                t = state["time"]
                idx = 0
                end_idx = chunk_size
                
            # Extraer chunk
            chunk_time = t[idx:end_idx].tolist()
            if is_pcr:
                # Flatline para PCR (asistolia)
                chunk_data = {lead: [0.0] * (end_idx - idx) for lead in df.columns}
            else:
                chunk_data = {lead: df[lead].values[idx:end_idx].tolist() for lead in df.columns}
            
            payload = {
                "type": "ecg_stream",
                "scenario": state["current_scenario"],
                "time": chunk_time,
                "leads": chunk_data
            }
            
            await websocket.send_json(payload)
            idx = end_idx
            
            # Pausa para sincronizar con tiempo real (100ms)
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        logger.info("Cliente Web/Movil desconectado.")
        state["active_connections"].remove(websocket)
    except Exception as e:
        logger.error(f"Error WS: {e}")
        if websocket in state["active_connections"]:
            state["active_connections"].remove(websocket)


# Servir estaticos para el dashboard web (pruebas en PC local)
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../frontend/www"), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    # Forzar UTF-8 también en el proceso hijo del reloader
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Lanzar servidor en el puerto 8081 para que encaje con el frontend
    logger.info("Iniciando motor BiosenseLink IoMT Backend en Puerto 8081...")
    uvicorn.run("server:app", host="0.0.0.0", port=8081, reload=True)

