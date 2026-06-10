/**
 * ESTADO CLÍNICO GLOBAL Y ORQUESTACIÓN DE LA SUITE (app.js)
 * Declaración de variables reactivas compartidas y escuchadores del ciclo de vida.
 */

// Direcciones URL de Microservicios Docker / Locales
const FHIR_URL = "http://localhost:8080/fhir";
const CONTROL_URL = "http://localhost:8081/api/control";

// Estado de la sesión clínica en pantalla
let PATIENT_ID = "ander-patient";
let activeDevice = "welch-allyn";
let activeState = "normal";
let pollingIntervalSec = 5;
let pollTimer = null;

let charts = {}; // Instancias activas de Chart.js
let lastLoggedTime = null;
let hasBeeped = false; // Flag para sincronización acústica del sístole ECG

// Instancia única del sintetizador de alarmas
const audioEngine = new ClinicalAudioEngine();

// Perfil activo por defecto de ciberseguridad
let activeProfile = "admin"; // admin | nurse

/**
 * Iniciar o reiniciar el bucle de refresco fisiológico (polling adaptativo)
 */
function restartPolling() {
    if (pollTimer) clearInterval(pollTimer);
    
    fetchPatientData();
    fetchVitalsData();
    
    pollTimer = setInterval(() => {
        fetchPatientData();
        fetchVitalsData();
    }, pollingIntervalSec * 1000);
}

/**
 * Inicializador automático de la Suite SCADA (Bootstrap)
 */
window.addEventListener('DOMContentLoaded', () => {
    if (typeof applyUILanguage === 'function') applyUILanguage();
    renderTelemetryCards();
    recreateCharts();
    renderClinicalButtons();
    
    // Cargar lista de pacientes desde base de datos PostgreSQL
    loadPatientsList();
    
    // Validar sesión clínica persistida en sessionStorage
    const user = sessionStorage.getItem("clinical_session_user");
    if (user) {
        document.getElementById("auth-portal").classList.add("opacity-0", "pointer-events-none");
        applyRBAC();
        if (typeof startPythonBackendWS === 'function') startPythonBackendWS();
    } else {
        document.getElementById("auth-portal").classList.remove("opacity-0", "pointer-events-none");
    }
    
    // Sincronizar el hardware con el estado del biosensor real en Python
    sendControlRequest(`device=${activeDevice}&state=${activeState}&interval=${pollingIntervalSec}`);
    
    // Si arranca en monitor vital básico, lanzar osciloscopio
    if (activeDevice === "welch-allyn") {
        document.getElementById("ecg-monitor-container").classList.remove("hidden");
        startEcgSimulation();
    }
    
    restartPolling();
});

// ESTADO DE RED
let networkMode = 'online';
function toggleNetworkMode() {
    networkMode = networkMode === 'offline' ? 'online' : 'offline';
    const btn = document.getElementById('network-mode-btn');
    if (networkMode === 'online') {
        btn.textContent = 'MODO LOCAL (WIFI)';
        btn.className = 'px-3 py-1 rounded-lg bg-medical-950/40 border border-medical-500/20 text-medical-400 font-bold text-[10px] uppercase tracking-wider transition';
        if (typeof startPythonBackendWS === 'function') startPythonBackendWS();
    } else {
        btn.textContent = 'MODO OFFLINE (JS)';
        btn.className = 'px-3 py-1 rounded-lg bg-slate-800 border border-slate-700 text-slate-400 font-bold text-[10px] uppercase tracking-wider transition';
        if (window.pythonWS) window.pythonWS.close();
    }
    logMessage(`Cambiado a modo ${networkMode}`, 'info');
}
