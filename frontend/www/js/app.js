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

// Web Worker para evitar la suspensión al minimizar la ventana
let pollingWorker = null;

function initPollingWorker() {
    if (typeof Worker !== 'undefined') {
        const workerCode = `
            let timer = null;
            let heartbeatTimer = null;
            let hr = 72;
            let isPaused = false;
            
            self.onmessage = function(e) {
                if (e.data.action === 'start') {
                    isPaused = false;
                    if (timer) clearInterval(timer);
                    timer = setInterval(() => {
                        self.postMessage('tick');
                    }, e.data.intervalMs);
                    
                    startHeartbeat();
                } else if (e.data.action === 'stop') {
                    isPaused = true;
                    if (timer) clearInterval(timer);
                    timer = null;
                    if (heartbeatTimer) clearInterval(heartbeatTimer);
                    heartbeatTimer = null;
                } else if (e.data.action === 'set_hr') {
                    hr = e.data.hr;
                    if (!isPaused) {
                        startHeartbeat();
                    }
                }
            };
            
            function startHeartbeat() {
                if (heartbeatTimer) clearInterval(heartbeatTimer);
                if (hr < 5.0 || isPaused) return;
                
                const intervalMs = 60000.0 / hr;
                heartbeatTimer = setInterval(() => {
                    self.postMessage('heartbeat_tick');
                }, intervalMs);
            }
        `;
        const blob = new Blob([workerCode], {type: 'application/javascript'});
        pollingWorker = new Worker(URL.createObjectURL(blob));
        pollingWorker.onmessage = function(e) {
            if (e.data === 'tick') {
                fetchPatientData();
                fetchVitalsData();
            } else if (e.data === 'heartbeat_tick') {
                // Solo reproducir el pitido acústico de fondo si la pestaña está minimizada/oculta
                // (Si está visible, el propio bucle animateECG ya reproduce el sonido sincronizado con el pico visual)
                if (document.hidden) {
                    const hrDisp = document.getElementById("display-val-8867-4");
                    let currentHr = 72;
                    if (hrDisp && hrDisp.textContent !== "--") currentHr = parseFloat(hrDisp.textContent);
                    if (typeof audioEngine !== 'undefined') {
                        audioEngine.playHeartbeat(currentHr > 120 ? 620 : 550);
                    }
                }
            }
        };
    }
}

/**
 * Iniciar o reiniciar el bucle de refresco fisiológico (polling adaptativo)
 */
function restartPolling() {
    fetchPatientData();
    fetchVitalsData();
    
    if (pollingWorker) {
        pollingWorker.postMessage({
            action: 'start',
            intervalMs: pollingIntervalSec * 1000
        });
    } else {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(() => {
            fetchPatientData();
            fetchVitalsData();
        }, pollingIntervalSec * 1000);
    }
}

/**
 * Detener el bucle de polling
 */
function stopPolling() {
    if (pollingWorker) {
        pollingWorker.postMessage({ action: 'stop' });
    }
    if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
    }
}

/**
 * Inicializador automático de la Suite SCADA (Bootstrap)
 */
window.addEventListener('DOMContentLoaded', () => {
    initPollingWorker();
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
