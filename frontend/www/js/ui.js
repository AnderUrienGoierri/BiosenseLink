/**
 * CAPA DE INTERFAZ DE USUARIO Y RENDERIZADO SCADA (ui.js)
 * Manejo de gráficos, displays dinámicos, logs y osciloscopio cardíaco interactivo.
 */

// Base de Datos de Dispositivos Digitalizados en la Suite Simulation Lab
const DEVICES_DATABASE = {
    "welch-allyn": {
        name: "Vital Signs Monitor",
        model: "Welch Allyn Connex",
        desc: "Monitor de signos vitales básicos a pie de cama. Registra pulso, SpO₂ con onda de volumen, temperatura y presión arterial hemodinámica.",
        metrics: [
            { code: "8867-4", name: "Frecuencia Cardíaca", unit: "lpm", color: "text-red-500", border: "rgba(239, 68, 68, 1)", bg: "rgba(239, 68, 68, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H7l2-5 3 10 2-7 1.5 4h3.28"/></svg>` },
            { code: "2708-6", name: "Saturación SpO₂", unit: "%", color: "text-sky-400", border: "rgba(56, 189, 248, 1)", bg: "rgba(56, 189, 248, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22a7 7 0 0 0 7-7c0-4.3-7-13-7-13S5 10.7 5 15a7 7 0 0 0 7 7z"/></svg>` },
            { code: "8310-5", name: "Temperatura", unit: "°C", color: "text-amber-500", border: "rgba(245, 158, 11, 1)", bg: "rgba(245, 158, 11, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg>` },
            { code: "8480-6", name: "Presión Sistólica", unit: "mmHg", color: "text-pink-500", border: "rgba(236, 72, 153, 1)", bg: "rgba(236, 72, 153, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14 4-4M3.34 19a10 10 0 1 1 17.32 0"/></svg>` },
            { code: "8462-4", name: "Presión Diastólica", unit: "mmHg", color: "text-fuchsia-500", border: "rgba(217, 70, 239, 1)", bg: "rgba(217, 70, 239, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 14-4-4M3.34 19a10 10 0 1 1 17.32 0"/></svg>` }
        ],
        states: [
            { code: "normal", label: "Estable (Basal)", color: "bg-slate-800 text-slate-300 border-slate-700", icon: `<svg class="w-3.5 h-3.5 text-emerald-400 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>` },
            { code: "pcr", label: "Paro Cardíaco (Asistolia)", color: "bg-red-950/60 text-red-400 border-red-500/40 font-bold", icon: `<svg class="w-3.5 h-3.5 text-red-500 inline-block animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" /></svg>` },
            { code: "shock", label: "Shock Hipovolémico", color: "bg-orange-950/50 text-orange-400 border-orange-500/30", icon: `<svg class="w-3.5 h-3.5 text-orange-400 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 13.5 12 21m0 0-7.5-7.5M12 21V3" /></svg>` },
            { code: "crisis", label: "Crisis Hipertensiva", color: "bg-purple-950/50 text-purple-400 border-purple-500/30", icon: `<svg class="w-3.5 h-3.5 text-purple-400 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 10.5 12 3m0 0 7.5 7.5M12 3v18" /></svg>` },
            { code: "epoc", label: "EPOC Reagudizado", color: "bg-cyan-950/50 text-cyan-400 border-cyan-500/30", icon: `<svg class="w-3.5 h-3.5 text-cyan-400 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3v18M3 12h18" /></svg>` },
            { code: "sepsis", label: "Sepsis Térmica", color: "bg-amber-950/50 text-amber-400 border-amber-500/30", icon: `<svg class="w-3.5 h-3.5 text-amber-400 inline-block" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>` }
        ]
    },
    "istat-gas": {
        name: "Gasometría Arterial",
        model: "Abbott i-STAT Alinity",
        desc: "Analizador Point-of-Care de gases sanguíneos, electrólitos y metabolitos. Evalúa equilibrio ácido-base.",
        metrics: [
            { code: "11557-6", name: "pH Arterial", unit: "pH", color: "text-emerald-400", border: "rgba(16, 185, 129, 1)", bg: "rgba(16, 185, 129, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v4M14 2v4M8.5 2h7M3 22h18M3 22l6.5-13.5M21 22l-6.5-13.5M5.6 16h12.8"/></svg>` },
            { code: "2019-8", name: "Presión pCO₂", unit: "mmHg", color: "text-violet-400", border: "rgba(167, 139, 250, 1)", bg: "rgba(167, 139, 250, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>` },
            { code: "2703-7", name: "Presión pO₂", unit: "mmHg", color: "text-blue-400", border: "rgba(96, 165, 250, 1)", bg: "rgba(96, 165, 250, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>` },
            { code: "2524-7", name: "Lactato", unit: "mmol/L", color: "text-rose-400", border: "rgba(251, 113, 133, 1)", bg: "rgba(251, 113, 133, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m8 3 4 8 5-5M4 14l8-8 4 4M14 21l-4-8-5 5M20 10l-8 8-4-4"/></svg>` }
        ],
        states: [
            { code: "normal", label: "Normal (Basal)", color: "bg-slate-800 text-slate-300 border-slate-700" },
            { code: "acidosis", label: "Inducir Acidosis Metabólica", color: "bg-rose-950/40 text-rose-400 border-rose-500/20" },
            { code: "alkalosis", label: "Inducir Alcalosis Respiratoria", color: "bg-violet-950/40 text-violet-400 border-violet-500/20" }
        ]
    },
    "accu-chek": {
        name: "Glucómetro e Hitos",
        model: "Roche Accu-Chek Inform II",
        desc: "Dispositivo metabólico PoC para control de glucosa y niveles de cetonas en sangre a pie de cama del paciente.",
        metrics: [
            { code: "2339-0", name: "Glucosa Sanguínea", unit: "mg/dL", color: "text-fuchsia-400", border: "rgba(232, 121, 249, 1)", bg: "rgba(232, 121, 249, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m10.5 20.5 10-10a4.95 4.95 0 1 0-7-7l-10 10a4.95 4.95 0 1 0 7 7Z"/><path d="m8.5 8.5 7 7"/></svg>` },
            { code: "3167-4", name: "Cetonas", unit: "mg/dL", color: "text-indigo-400", border: "rgba(129, 140, 248, 1)", bg: "rgba(129, 140, 248, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2v17.5a2.5 2.5 0 0 1-5 0V2M8.5 2h7M9 8h5M9 12h5"/></svg>` }
        ],
        states: [
            { code: "normal", label: "Normal (Basal)", color: "bg-slate-800 text-slate-300 border-slate-700" },
            { code: "diabetic-keto", label: "Cetoacidosis Diabética (CAD)", color: "bg-fuchsia-950/40 text-fuchsia-400 border-fuchsia-500/20" },
            { code: "hypoglycemia", label: "Inducir Hipoglucemia", color: "bg-indigo-950/40 text-indigo-400 border-indigo-500/20" }
        ]
    },
    "coaguchek": {
        name: "Coagulómetro PoC",
        model: "Roche CoaguChek Pro II",
        desc: "Analizador de coagulación portátil. Mide el Tiempo de Protrombina (PT) y el Ratio de Rango Internacional (INR).",
        metrics: [
            { code: "46418-2", name: "Tiempo Protrombina (PT)", unit: "s", color: "text-yellow-400", border: "rgba(250, 204, 21, 1)", bg: "rgba(250, 204, 21, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>` },
            { code: "34714-6", name: "Índice INR", unit: "ratio", color: "text-orange-400", border: "rgba(251, 146, 60, 1)", bg: "rgba(251, 146, 60, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="2" y1="14" x2="6" y2="14"/><line x1="10" y1="8" x2="14" y2="8"/><line x1="18" y1="16" x2="22" y2="16"/></svg>` }
        ],
        states: [
            { code: "normal", label: "Normal (Basal)", color: "bg-slate-800 text-slate-300 border-slate-700" },
            { code: "warfarin-overdose", label: "Sobredosis de Warfarina (INR Crítico)", color: "bg-orange-950/40 text-orange-400 border-orange-500/20" }
        ]
    },
    "alere-triage": {
        name: "Inmunología Cardíaca",
        model: "Alere Triage MeterPro",
        desc: "Analizador de inmunofluorescencia PoC para diagnóstico de infartos e insuficiencia cardíaca congestiva.",
        metrics: [
            { code: "10839-9", name: "Troponina I", unit: "ng/mL", color: "text-red-500", border: "rgba(239, 68, 68, 1)", bg: "rgba(239, 68, 68, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>` },
            { code: "30934-4", name: "Péptido BNP", unit: "pg/mL", color: "text-cyan-400", border: "rgba(34, 211, 238, 1)", bg: "rgba(34, 211, 238, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M3.22 12H7l2-5 3 10 2-7 1.5 4h3.28"/></svg>` }
        ],
        states: [
            { code: "normal", label: "Normal (Basal)", color: "bg-slate-800 text-slate-300 border-slate-700" },
            { code: "ami-infarct", label: "Crisis de Infarto Agudo (IAM)", color: "bg-red-950/40 text-red-400 border-red-500/20" }
        ]
    },
    "hiv-monitor": {
        name: "Seguimiento Inmunológico VIH",
        model: "Abbott m-PIMA & Cepheid GeneXpert PoC",
        desc: "Sistema digital molecular descentralizado para control y optimización de adherencia al tratamiento de VIH. Monitorea la replicación virológica y respuesta celular.",
        metrics: [
            { code: "70241-5", name: "Carga Viral VIH-1", unit: "copias/mL", color: "text-indigo-400", border: "rgba(129, 140, 248, 1)", bg: "rgba(129, 140, 248, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M10.85 12A3 3 0 1 1 15 9.5m-3 5.35a3 3 0 1 1-4.15-2.5m4.15-2.85a3 3 0 1 1 0 5.7M12 22v-3M3 12h3M21 12h-3M12 2v3"/></svg>` },
            { code: "24467-3", name: "Recuento CD4+", unit: "cél/µL", color: "text-emerald-400", border: "rgba(16, 185, 129, 1)", bg: "rgba(16, 185, 129, 0.15)", icon: `<svg class="w-full h-full" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v8M8 12h8"/></svg>` }
        ],
        states: [
            { code: "normal", label: "Normal (Adherencia)", color: "bg-slate-800 text-slate-300 border-slate-700" },
            { code: "therapeutic-failure", label: "Inducir Fallo de Adherencia", color: "bg-amber-950/40 text-amber-400 border-amber-500/20" },
            { code: "aids-crisis", label: "Crisis de Inmunodeficiencia (SIDA)", color: "bg-red-950/40 text-red-400 border-red-500/20" }
        ]
    }
};

/**
 * Registrar logs de depuración estructurados en la consola web en pantalla
 */
function logMessage(text, type = "info") {
    const logBox = document.getElementById("api-log");
    if (!logBox) return;
    const timeStr = new Date().toLocaleTimeString();
    let color = "text-slate-400";
    if (type === "success") color = "text-emerald-400";
    if (type === "warning") color = "text-amber-400";
    if (type === "error") color = "text-red-400 font-bold";

    const div = document.createElement("div");
    div.className = `${color} py-0.5 border-b border-slate-900/30`;
    div.innerHTML = `<span class="text-slate-600 font-semibold">[${timeStr}]</span> ${text}`;
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
}

/**
 * Activar o desactivar las alarmas acústicas mediante control de UI
 */
function toggleAudio() {
    const isMuted = !audioEngine.muted;
    audioEngine.setMute(isMuted);
    
    const mutedIcon = document.getElementById("audio-icon-muted");
    const unmutedIcon = document.getElementById("audio-icon-unmuted");
    
    if (isMuted) {
        if (mutedIcon) mutedIcon.classList.remove("hidden");
        if (unmutedIcon) unmutedIcon.classList.add("hidden");
        logMessage("Alarmas sonoras silenciadas por el operador.", "info");
    } else {
        if (mutedIcon) mutedIcon.classList.add("hidden");
        if (unmutedIcon) unmutedIcon.classList.remove("hidden");
        logMessage("Alarmas sonoras activas. Cumplimiento IEC 60601-1-8.", "warning");
        audioEngine.playHeartbeat(800);
    }
    
    // Actualizar el estado visual del botón de mute en el panel flotante
    const panelMuteBtn = document.getElementById("panel-mute-btn");
    if (panelMuteBtn) {
        if (isMuted) {
            panelMuteBtn.textContent = "Activar Sonido";
            panelMuteBtn.className = "w-full py-1.5 rounded-lg bg-emerald-950/40 text-emerald-400 border border-emerald-500/20 text-xs font-bold transition hover:bg-emerald-900/30";
        } else {
            panelMuteBtn.textContent = "Silenciar Todo";
            panelMuteBtn.className = "w-full py-1.5 rounded-lg bg-red-950/40 text-red-400 border border-red-500/20 text-xs font-bold transition hover:bg-red-900/30";
        }
    }
}

/**
 * Mostrar u ocultar el panel flotante de control de volumen
 */
function toggleVolumePanel(event) {
    if (event) event.stopPropagation();
    const panel = document.getElementById("volume-panel");
    if (panel) {
        panel.classList.toggle("hidden");
    }
}

/**
 * Cambiar el volumen de un tipo específico de sonido (ECG heartbeat, Flatline, Alarm)
 */
function changeSoundVolume(soundType, val) {
    const percentageText = document.getElementById(`vol-${soundType}-txt`);
    if (percentageText) {
        percentageText.textContent = `${val}%`;
    }
    
    let scaledVal = 0;
    if (soundType === 'heartbeat') {
        scaledVal = (val / 100) * 0.2; // Rango de ganancia: 0 a 0.2
    } else if (soundType === 'flatline') {
        scaledVal = (val / 100) * 0.15; // Rango de ganancia: 0 a 0.15
    } else if (soundType === 'alarm') {
        scaledVal = (val / 100) * 0.2; // Rango de ganancia: 0 a 0.2
    }
    
    if (typeof audioEngine !== 'undefined') {
        audioEngine.setVolume(soundType, scaledVal);
    }
}

// Cerrar el panel flotante si el usuario hace clic en cualquier parte fuera de él
document.addEventListener("click", (e) => {
    const panel = document.getElementById("volume-panel");
    const container = document.getElementById("audio-control-container");
    if (panel && container && !container.contains(e.target)) {
        panel.classList.add("hidden");
    }
});

/**
 * Dibujar botones del controlador de simulación según el dispositivo médico activo
 */
function renderClinicalButtons() {
    const container = document.getElementById("clinical-state-controls");
    if (!container) return;
    container.innerHTML = "";
    const device = DEVICES_DATABASE[activeDevice];
    
    device.states.forEach(st => {
        const btn = document.createElement("button");
        btn.onclick = () => setClinicalState(st.code);
        
        let activeClass = "bg-slate-900 border-slate-800 text-slate-400 hover:bg-slate-800 hover:text-slate-200";
        if (st.code === activeState) {
            activeClass = st.color + " ring-2 ring-medical-500/20 font-bold";
        }
        
        btn.className = `px-3 py-1.5 rounded-lg border text-xs transition duration-200 flex items-center justify-center gap-1.5 ${activeClass}`;
        btn.innerHTML = `${st.icon || ''}<span>${st.label}</span>`;
        container.appendChild(btn);
    });
}

/**
 * Cambiar el dispositivo activo en el Sidebar y Reconfigurar la interfaz (SCADA)
 */
async function selectDevice(deviceKey) {
    if (deviceKey === activeDevice) return;
    
    activeDevice = deviceKey;
    activeState = "normal";
    logMessage(`Cambiando dispositivo a: [${deviceKey.toUpperCase()}] ...`, "info");
    
    const navButtons = document.querySelectorAll("#device-nav button");
    navButtons.forEach(btn => {
        btn.className = "w-full text-left px-4 py-3 rounded-xl transition-all duration-200 flex items-center gap-3 bg-slate-900/30 text-slate-400 border border-transparent hover:bg-slate-900/60 hover:text-slate-200";
        const iconDiv = btn.querySelector("div");
        if (iconDiv) {
            iconDiv.className = "w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center flex-shrink-0";
        }
        const svg = btn.querySelector("svg");
        if (svg) {
            svg.className = "w-5 h-5";
        }
    });
    const dots = document.querySelectorAll("#device-nav span");
    dots.forEach(dt => { if (dt) dt.className = "w-2 h-2 rounded-full bg-emerald-500"; });
    
    const activeBtn = document.getElementById(`nav-${deviceKey.split("-")[0]}`);
    if (activeBtn) {
        activeBtn.className = "w-full text-left px-4 py-3 rounded-xl transition-all duration-200 flex items-center gap-3 bg-medical-950/20 text-medical-400 border border-medical-500/30 shadow-md";
        const iconDiv = activeBtn.querySelector("div");
        if (iconDiv) {
            iconDiv.className = "w-8 h-8 rounded-lg bg-medical-500/10 flex items-center justify-center flex-shrink-0";
        }
        const svg = activeBtn.querySelector("svg");
        if (svg) {
            svg.className = "w-5 h-5 text-medical-400";
        }
    }
    const activeDot = document.getElementById(`dot-${deviceKey.split("-")[0]}`);
    if (activeDot) {
        activeDot.className = "w-2 h-2 rounded-full bg-emerald-400 animate-pulse";
    }

    const dev = DEVICES_DATABASE[deviceKey];
    document.getElementById("header-device-title").textContent = dev.name;
    document.getElementById("header-device-subtitle").textContent = `${dev.desc} • ${dev.model}`;

    await sendControlRequest(`device=${deviceKey}`);
    renderTelemetryCards();
    recreateCharts();
    renderClinicalButtons();
    
    fetchPatientData();
    fetchVitalsData();

    const ecgMonitor = document.getElementById("ecg-monitor-container");
    if (deviceKey === "welch-allyn") {
        if (ecgMonitor) ecgMonitor.classList.remove("hidden");
        startEcgSimulation();
    } else {
        if (ecgMonitor) ecgMonitor.classList.add("hidden");
        stopEcgSimulation();
    }
}

/**
 * Crear las tarjetas numéricas en el Dashboard
 */
function renderTelemetryCards() {
    const container = document.getElementById("telemetry-cards-container");
    if (!container) return;
    container.innerHTML = "";
    const dev = DEVICES_DATABASE[activeDevice];

    dev.metrics.forEach(met => {
        const card = document.createElement("div");
        card.className = "bg-slate-900/40 rounded-xl p-5 border border-slate-900 flex justify-between items-center relative overflow-hidden";
        card.innerHTML = `
            <div class="absolute -right-4 -bottom-4 w-24 h-24 text-slate-800/10 select-none pointer-events-none">${met.icon}</div>
            <div class="z-10">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">${met.name}</span>
                <div class="flex items-baseline gap-1 mt-2">
                    <span id="display-val-${met.code}" class="text-4xl font-black ${met.color}">--</span>
                    <span class="text-xs text-slate-400 font-medium">${met.unit}</span>
                </div>
                <span class="text-[8px] text-slate-500 font-mono mt-2 block">LOINC: ${met.code}</span>
            </div>
        `;
        container.appendChild(card);
    });
}

/**
 * Destruir e inicializar gráficos de Chart.js
 */
function recreateCharts() {
    Object.values(charts).forEach(ch => { if (ch) ch.destroy(); });
    charts = {};

    const container = document.getElementById("charts-grid-container");
    if (!container) return;
    container.innerHTML = "";
    const dev = DEVICES_DATABASE[activeDevice];

    let chartConfigs = [];
    if (activeDevice === "welch-allyn") {
        chartConfigs = [
            {
                id: `chart-canvas-g1`,
                title: `Monitoreo Cardiopulmonar (FC & SpO₂)`,
                metrics: [dev.metrics[0], dev.metrics[1]]
            },
            {
                id: `chart-canvas-g2`,
                title: `Monitoreo Térmico (Temperatura)`,
                metrics: [dev.metrics[2]]
            },
            {
                id: `chart-canvas-g3`,
                title: `Monitoreo Hemodinámico (Presión Arterial)`,
                metrics: [dev.metrics[3], dev.metrics[4]]
            }
        ];
    } else if (dev.metrics.length <= 2) {
        chartConfigs = dev.metrics.map(m => ({
            id: `chart-canvas-${m.code}`,
            title: `Historial de ${m.name}`,
            metrics: [m]
        }));
    } else {
        chartConfigs = [
            {
                id: `chart-canvas-g1`,
                title: `Historial Fisiológico Principal`,
                metrics: [dev.metrics[0], dev.metrics[1]]
            },
            {
                id: `chart-canvas-g2`,
                title: `Historial Fisiológico Secundario`,
                metrics: dev.metrics.slice(2)
            }
        ];
    }

    container.className = `grid grid-cols-1 ${chartConfigs.length > 1 ? 'lg:grid-cols-2' : ''} gap-6`;

    chartConfigs.forEach(conf => {
        const box = document.createElement("div");
        box.className = "bg-slate-900/40 rounded-xl p-5 border border-slate-900 flex flex-col h-[280px]";
        
        const bulletHtml = conf.metrics.map(m => `<span class="inline-flex items-center gap-1 text-[10px] text-slate-400 font-semibold"><span class="w-2.5 h-2.5 rounded-full" style="background-color: ${m.border}"></span> ${m.name}</span>`).join(" • ");
        box.innerHTML = `
            <div class="flex justify-between items-center mb-3">
                <h3 class="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full bg-medical-500 animate-pulse"></span> ${conf.title}
                </h3>
                <div class="flex items-center gap-2">${bulletHtml}</div>
            </div>
            <div class="flex-1 min-h-0 relative">
                <canvas id="${conf.id}"></canvas>
            </div>
        `;
        container.appendChild(box);

        const ctx = document.getElementById(conf.id).getContext('2d');
        const datasets = conf.metrics.map(m => ({
            label: m.name,
            data: [],
            borderColor: m.border,
            backgroundColor: m.bg,
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.3,
            fill: false,
            loincCode: m.code
        }));

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#475569', font: { size: 8, family: 'monospace' } }
                },
                y: {
                    grid: { color: 'rgba(30, 41, 59, 0.3)' },
                    ticks: { color: '#475569', font: { size: 8, family: 'monospace' } }
                }
            }
        };

        charts[conf.id] = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: datasets },
            options: chartOptions
        });
    });
}

// ==========================================
// SISTEMA DE OSCILOSCOPIO ELECTROCARDIOGRÁFICO (ECG/EKG)
// ==========================================
let ecgCanvas = null;
let ecgCtx = null;
let ecgAnimationId = null;
let ecgX = 0;
let ecgY = 70;
let lastEcgTime = 0;
let ecgPhase = 0;

// View Modes: 'offline_single' | 'online_grid' | 'online_4x3'
window.ecgViewMode = 'offline_single';

function setEcgViewMode(mode) {
    window.ecgViewMode = mode;
    const btns = ['btn-view-single', 'btn-view-grid', 'btn-view-4x3'];
    btns.forEach(id => {
        document.getElementById(id).className = "px-2 py-0.5 rounded border border-slate-700 bg-slate-800 text-slate-400 transition hover:bg-slate-700";
    });
    let activeBtn = "";
    if(mode === 'offline_single') activeBtn = 'btn-view-single';
    if(mode === 'online_grid')    activeBtn = 'btn-view-grid';
    if(mode === 'online_4x3')     activeBtn = 'btn-view-4x3';
    document.getElementById(activeBtn).className = "px-2 py-0.5 rounded border border-medical-500/50 bg-medical-950/40 text-medical-400 font-bold transition hover:bg-medical-900/40";

    // Trigger grid repaint when switching modes
    if (ecgCanvas && ecgCtx) {
        _ecgNeedGridRedraw = true;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// RING BUFFER — accumulates real-time 12-lead samples from WebSocket
// ─────────────────────────────────────────────────────────────────────────────
const ECG_LEADS       = ['I','II','III','aVR','aVL','aVF','V1','V2','V3','V4','V5','V6'];
const ECG_BUF_SIZE    = 2000;   // ~4 seconds at 500 Hz — plenty of headroom
let _ecgRingBuf       = {};     // leadName → Float32Array
let _ecgRingWrite     = 0;
let _ecgRingRead      = 0;

// State for per-lead sweep cursors (online modes)
let _ecgCursorX    = new Array(12).fill(0); // current X per lead (12x1 mode)
let _ecgCursorY    = new Array(12).fill(null); // last Y per lead
let _ecg4CursorX   = new Array(13).fill(0); // col-local X per cell (4x3 + rhythm)
let _ecg4CursorY   = new Array(13).fill(null);
let _ecgNeedGridRedraw = true;
let _ecgSamplingRate   = 500;  // Hz — synced from WS payload

// Expose push function so api.js can call it
window.pushEcgSamples = function(payload) {
    if (!payload || !payload.leads || !payload.time) return;
    if (payload.sampling_rate) _ecgSamplingRate = payload.sampling_rate;
    const nSamples = payload.time.length;
    
    // Si el lector se ha quedado muy atrás respecto a la escritura (más de 1000 muestras, ~2 segundos),
    // significa que la pestaña estuvo minimizada o suspendida. Vaciamos el buffer para sincronizar en tiempo real.
    const lag = _ecgRingWrite - _ecgRingRead;
    if (lag > 1000) {
        _ecgRingRead = _ecgRingWrite;
    }

    for (let s = 0; s < nSamples; s++) {
        ECG_LEADS.forEach(lead => {
            if (!_ecgRingBuf[lead]) {
                _ecgRingBuf[lead] = new Float32Array(ECG_BUF_SIZE);
            }
            const v = payload.leads[lead] ? payload.leads[lead][s] : 0;
            _ecgRingBuf[lead][_ecgRingWrite % ECG_BUF_SIZE] = v;
        });
        _ecgRingWrite++;
    }
};

function _ecgRingAvailable() {
    return _ecgRingWrite - _ecgRingRead;
}

function _ecgRingPeek(lead, offset) {
    if (!_ecgRingBuf[lead]) return 0;
    return _ecgRingBuf[lead][(_ecgRingRead + offset) % ECG_BUF_SIZE];
}

function _ecgRingConsume(n) {
    _ecgRingRead = Math.min(_ecgRingRead + n, _ecgRingWrite);
}

// ─────────────────────────────────────────────────────────────────────────────
// GRID DRAWING (shared, called once or on resize/mode-change)
// ─────────────────────────────────────────────────────────────────────────────
function _drawEcgMmGrid(ctx, w, h, mode) {
    ctx.fillStyle = "#090d16";
    ctx.fillRect(0, 0, w, h);

    // 1 mm minor grid
    ctx.strokeStyle = "rgba(20,184,166,0.05)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let x = 0; x < w; x += 5) { ctx.moveTo(x, 0); ctx.lineTo(x, h); }
    for (let y = 0; y < h; y += 5) { ctx.moveTo(0, y); ctx.lineTo(w, y); }
    ctx.stroke();

    // 5 mm major grid
    ctx.strokeStyle = "rgba(20,184,166,0.14)";
    ctx.lineWidth = 1.0;
    ctx.beginPath();
    for (let x = 0; x < w; x += 25) { ctx.moveTo(x, 0); ctx.lineTo(x, h); }
    for (let y = 0; y < h; y += 25) { ctx.moveTo(0, y); ctx.lineTo(w, y); }
    ctx.stroke();

    if (mode === 'online_4x3') {
        const colW = w / 4;
        const rowH = (h * 0.75) / 3;
        // Column dividers (top 3 rows only)
        ctx.strokeStyle = "rgba(20,184,166,0.30)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        for (let c = 1; c < 4; c++) {
            ctx.moveTo(c * colW, 0);
            ctx.lineTo(c * colW, h * 0.75);
        }
        // Row dividers
        for (let r = 1; r < 3; r++) {
            ctx.moveTo(0, r * rowH);
            ctx.lineTo(w, r * rowH);
        }
        // Rhythm strip divider
        ctx.moveTo(0, h * 0.75);
        ctx.lineTo(w, h * 0.75);
        ctx.stroke();
    } else if (mode === 'online_grid') {
        const rowH = h / 12;
        ctx.strokeStyle = "rgba(20,184,166,0.20)";
        ctx.lineWidth = 1.0;
        ctx.beginPath();
        for (let r = 1; r < 12; r++) {
            ctx.moveTo(0, r * rowH);
            ctx.lineTo(w, r * rowH);
        }
        ctx.stroke();
    }
}

// Draw persistent lead labels (called after grid draw)
function _drawLeadLabels12x1(ctx, w, h) {
    const rowH = h / 12;
    ECG_LEADS.forEach((lead, i) => {
        const lx = 4, ly = i * rowH + 13;
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(lx - 2, ly - 11, lead.length * 7 + 4, 14);
        ctx.fillStyle = "rgba(255,255,255,0.92)";
        ctx.font = "bold 10px 'Inter', monospace";
        ctx.fillText(lead, lx, ly);
    });
}

function _drawLeadLabels4x3(ctx, w, h) {
    const colW = w / 4;
    const rowH = (h * 0.75) / 3;
    const gridLeads = [
        {name:'I',   col:0,row:0},{name:'II',  col:0,row:1},{name:'III', col:0,row:2},
        {name:'aVR', col:1,row:0},{name:'aVL', col:1,row:1},{name:'aVF', col:1,row:2},
        {name:'V1',  col:2,row:0},{name:'V2',  col:2,row:1},{name:'V3',  col:2,row:2},
        {name:'V4',  col:3,row:0},{name:'V5',  col:3,row:1},{name:'V6',  col:3,row:2}
    ];
    ctx.font = "bold 10px 'Inter', monospace";
    gridLeads.forEach(gl => {
        const lx = gl.col * colW + 4;
        const ly = gl.row * rowH + 13;
        ctx.fillStyle = "rgba(0,0,0,0.55)";
        ctx.fillRect(lx - 2, ly - 11, gl.name.length * 7 + 4, 14);
        ctx.fillStyle = "#ffb03b";
        ctx.fillText(gl.name, lx, ly);
    });
    // Rhythm strip label
    const ry = h * 0.75 + 13;
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(2, ry - 11, 78, 14);
    ctx.fillStyle = "#f43f5e";
    ctx.fillText("II Rhythm", 4, ry);
}

// ─────────────────────────────────────────────────────────────────────────────
// CLEAR-AHEAD strip (repairs grid after erasing)
// ─────────────────────────────────────────────────────────────────────────────
function _clearAheadStrip(ctx, x, y0, height, stripW, majorGrid, rowMin, rowMax) {
    // Erase the strip
    ctx.fillStyle = "#090d16";
    ctx.fillRect(x, rowMin, stripW, rowMax - rowMin);
    // Redraw 1mm minor lines in strip
    ctx.strokeStyle = "rgba(20,184,166,0.05)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    for (let gx = Math.floor(x / 5) * 5; gx < x + stripW; gx += 5) {
        ctx.moveTo(gx, rowMin); ctx.lineTo(gx, rowMax);
    }
    for (let gy = Math.floor(rowMin / 5) * 5; gy <= rowMax; gy += 5) {
        ctx.moveTo(x, gy); ctx.lineTo(x + stripW, gy);
    }
    ctx.stroke();
    // Redraw 5mm major lines in strip
    ctx.strokeStyle = "rgba(20,184,166,0.14)";
    ctx.lineWidth = 1.0;
    ctx.beginPath();
    for (let gx = Math.floor(x / 25) * 25; gx < x + stripW; gx += 25) {
        ctx.moveTo(gx, rowMin); ctx.lineTo(gx, rowMax);
    }
    for (let gy = Math.floor(rowMin / 25) * 25; gy <= rowMax; gy += 25) {
        ctx.moveTo(x, gy); ctx.lineTo(x + stripW, gy);
    }
    ctx.stroke();
}

// ─────────────────────────────────────────────────────────────────────────────
// ONLINE 12×1 — sweeping oscilloscope, all 12 leads stacked
// ─────────────────────────────────────────────────────────────────────────────
function _sweepOnline12x1(values) {
    // values: Float32Array or Array of 12 lead samples (one sample, all leads)
    const w = ecgCanvas.width;
    const h = ecgCanvas.height;
    const rowH = h / 12;
    const STRIP_W = 18;   // erase-ahead width (px)
    // Scale: 25mm/s standard. At 500Hz, one sample = 1/500 s.
    // Pixels per sample = pixPerSec / Fs = (w / windowSec) / Fs
    // windowSec for 12x1: we show the whole width as one sweep (chosen sweep time)
    const sweepSec   = w / 75; // 75 px/s ≈ comfortable clinical sweep
    const pxPerSamp  = 75 / _ecgSamplingRate;

    ECG_LEADS.forEach((lead, i) => {
        const v = values[i];
        const rowTop = i * rowH;
        const rowBot = rowTop + rowH;
        const yBase  = rowTop + rowH * 0.5;
        const scale  = rowH * 0.42;
        const x      = _ecgCursorX[i];
        const newY   = yBase - (v * scale);

        // Clear ahead strip
        _clearAheadStrip(ecgCtx, x, rowTop, rowH, STRIP_W, 25, rowTop, rowBot);

        // Draw row divider at lane boundaries (keep visible)
        ecgCtx.strokeStyle = "rgba(20,184,166,0.20)";
        ecgCtx.lineWidth = 1.0;
        if (i > 0) {
            ecgCtx.beginPath();
            ecgCtx.moveTo(x, rowTop);
            ecgCtx.lineTo(Math.min(x + STRIP_W, w), rowTop);
            ecgCtx.stroke();
        }

        // Draw signal segment
        if (_ecgCursorY[i] !== null) {
            ecgCtx.shadowBlur   = 6;
            ecgCtx.shadowColor  = "#10b981";
            ecgCtx.strokeStyle  = "#10b981";
            ecgCtx.lineWidth    = 2.0;
            ecgCtx.lineCap      = "round";
            ecgCtx.beginPath();
            ecgCtx.moveTo(x, _ecgCursorY[i]);
            ecgCtx.lineTo(x + pxPerSamp, newY);
            ecgCtx.stroke();
            ecgCtx.shadowBlur = 0;
        }

        _ecgCursorY[i] = newY;
        _ecgCursorX[i] = x + pxPerSamp;
        // Wrap
        if (_ecgCursorX[i] >= w) {
            _ecgCursorX[i] = 0;
            _ecgCursorY[i] = null;
        }
    });

    // Repaint lead labels (so they stay on top of the signal)
    _drawLeadLabels12x1(ecgCtx, w, h);
}

// ─────────────────────────────────────────────────────────────────────────────
// ONLINE 4×3+1 — standard clinical diagnostic layout
// ─────────────────────────────────────────────────────────────────────────────
const _4x3_LEADS = [
    {lead:'I',   col:0,row:0, idx:0},
    {lead:'II',  col:0,row:1, idx:1},
    {lead:'III', col:0,row:2, idx:2},
    {lead:'aVR', col:1,row:0, idx:3},
    {lead:'aVL', col:1,row:1, idx:4},
    {lead:'aVF', col:1,row:2, idx:5},
    {lead:'V1',  col:2,row:0, idx:6},
    {lead:'V2',  col:2,row:1, idx:7},
    {lead:'V3',  col:2,row:2, idx:8},
    {lead:'V4',  col:3,row:0, idx:9},
    {lead:'V5',  col:3,row:1, idx:10},
    {lead:'V6',  col:3,row:2, idx:11}
];

function _sweepOnline4x3(values) {
    const w    = ecgCanvas.width;
    const h    = ecgCanvas.height;
    const colW = w / 4;
    const topH = h * 0.75;          // top 3 rows = 75% height
    const rowH = topH / 3;
    const rStripTop = h * 0.75;     // rhythm strip top
    const rStripH   = h * 0.25;
    const STRIP_W   = 18;
    const pxPerSamp = 75 / _ecgSamplingRate;  // same sweep speed as 12x1

    _4x3_LEADS.forEach(gl => {
        const { lead, col, row, idx } = gl;
        const li = ECG_LEADS.indexOf(lead);
        const v  = values[li];

        const cellLeft = col * colW;
        const cellTop  = row * rowH;
        const cellBot  = cellTop + rowH;
        const yBase    = cellTop + rowH * 0.5;
        const scale    = rowH * 0.42;
        const x        = cellLeft + _ecg4CursorX[idx];
        const newY     = yBase - (v * scale);
        const localX   = _ecg4CursorX[idx];

        // Only draw within the cell's column
        if (x < cellLeft || x > cellLeft + colW) return;

        // Clear-ahead within cell bounds
        const eraseLeft  = Math.min(x, cellLeft + colW - STRIP_W - 1);
        const eraseRight = Math.min(eraseLeft + STRIP_W, cellLeft + colW);
        _clearAheadStrip(ecgCtx, eraseLeft, cellTop, rowH, eraseRight - eraseLeft, 25, cellTop, cellBot);

        // Column and row dividers maintenance
        ecgCtx.strokeStyle = "rgba(20,184,166,0.30)";
        ecgCtx.lineWidth = 1.5;
        if (col > 0) {
            ecgCtx.beginPath();
            ecgCtx.moveTo(cellLeft, cellTop);
            ecgCtx.lineTo(cellLeft, cellBot);
            ecgCtx.stroke();
        }
        if (row > 0) {
            ecgCtx.beginPath();
            ecgCtx.moveTo(cellLeft, cellTop);
            ecgCtx.lineTo(Math.min(x + STRIP_W, cellLeft + colW), cellTop);
            ecgCtx.stroke();
        }

        // Draw signal
        if (_ecg4CursorY[idx] !== null) {
            ecgCtx.shadowBlur   = 6;
            ecgCtx.shadowColor  = "#14b8a6";
            ecgCtx.strokeStyle  = "#2dd4bf";
            ecgCtx.lineWidth    = 2.0;
            ecgCtx.lineCap      = "round";
            ecgCtx.beginPath();
            ecgCtx.moveTo(x, _ecg4CursorY[idx]);
            ecgCtx.lineTo(x + pxPerSamp, newY);
            ecgCtx.stroke();
            ecgCtx.shadowBlur = 0;
        }

        _ecg4CursorY[idx] = newY;
        _ecg4CursorX[idx] = localX + pxPerSamp;

        // Wrap within column
        if (_ecg4CursorX[idx] >= colW) {
            _ecg4CursorX[idx] = 0;
            _ecg4CursorY[idx] = null;
        }
    });

    // Rhythm strip — Lead II (full width)
    {
        const li  = ECG_LEADS.indexOf('II');
        const v   = values[li];
        const idx = 12; // rhythm strip cursor index
        const x   = _ecg4CursorX[idx];
        const yBase = rStripTop + rStripH * 0.5;
        const scale = rStripH * 0.42;
        const newY  = yBase - (v * scale);

        _clearAheadStrip(ecgCtx, x, rStripTop, rStripH, STRIP_W, 25, rStripTop, h);

        // Rhythm strip top divider maintenance
        ecgCtx.strokeStyle = "rgba(20,184,166,0.30)";
        ecgCtx.lineWidth = 1.5;
        ecgCtx.beginPath();
        ecgCtx.moveTo(x, rStripTop);
        ecgCtx.lineTo(Math.min(x + STRIP_W, w), rStripTop);
        ecgCtx.stroke();

        if (_ecg4CursorY[idx] !== null) {
            ecgCtx.shadowBlur   = 7;
            ecgCtx.shadowColor  = "#f43f5e";
            ecgCtx.strokeStyle  = "#f43f5e";
            ecgCtx.lineWidth    = 2.2;
            ecgCtx.lineCap      = "round";
            ecgCtx.beginPath();
            ecgCtx.moveTo(x, _ecg4CursorY[idx]);
            ecgCtx.lineTo(x + pxPerSamp, newY);
            ecgCtx.stroke();
            ecgCtx.shadowBlur = 0;
        }

        _ecg4CursorY[idx] = newY;
        _ecg4CursorX[idx] = x + pxPerSamp;
        if (_ecg4CursorX[idx] >= w) {
            _ecg4CursorX[idx] = 0;
            _ecg4CursorY[idx] = null;
        }
    }

    // Repaint labels on top
    _drawLeadLabels4x3(ecgCtx, w, h);
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN ENTRY — startEcgSimulation
// ─────────────────────────────────────────────────────────────────────────────
let ecgXArr = new Array(12).fill(0);

function startEcgSimulation() {
    if (ecgAnimationId) return;
    ecgCanvas = document.getElementById("ecg-canvas");
    if (!ecgCanvas) return;

    const rect = ecgCanvas.getBoundingClientRect();
    ecgCanvas.width  = rect.width;
    ecgCanvas.height = rect.height;

    ecgCtx = ecgCanvas.getContext("2d");
    ecgX   = 0;
    ecgXArr = new Array(12).fill(0);
    lastEcgTime = performance.now();
    ecgPhase    = 0;

    // Reset online cursors
    _ecgCursorX.fill(0);
    _ecgCursorY.fill(null);
    _ecg4CursorX.fill(0);
    _ecg4CursorY.fill(null);
    _ecgNeedGridRedraw = true;

    // Draw initial grid for current mode
    _drawEcgMmGrid(ecgCtx, ecgCanvas.width, ecgCanvas.height, window.ecgViewMode);

    function animateECG(timestamp) {
        if (!ecgCanvas || !ecgCtx) return;
        const dt = (timestamp - lastEcgTime) / 1000.0;
        lastEcgTime = timestamp;

        const isPausedSim = document.getElementById("btn-power-on")?.textContent.includes("FUERA DE LÍNEA") || false;

        // ── ONLINE MODES ──────────────────────────────────────────────────────
        if (window.ecgViewMode !== 'offline_single' && !isPausedSim) {
            // Redraw grid if mode just changed or canvas resized
            if (_ecgNeedGridRedraw) {
                _drawEcgMmGrid(ecgCtx, ecgCanvas.width, ecgCanvas.height, window.ecgViewMode);
                if (window.ecgViewMode === 'online_grid') _drawLeadLabels12x1(ecgCtx, ecgCanvas.width, ecgCanvas.height);
                else                                      _drawLeadLabels4x3(ecgCtx, ecgCanvas.width, ecgCanvas.height);
                _ecgCursorX.fill(0); _ecgCursorY.fill(null);
                _ecg4CursorX.fill(0); _ecg4CursorY.fill(null);
                _ecgNeedGridRedraw = false;
            }

            // Consume samples from ring buffer — consume as many as have arrived
            // to maintain real-time sync (usually ~5-10 per 60fps frame at 500Hz)
            const available = _ecgRingAvailable();
            const toConsume = Math.min(available, 8);  // cap at 8 to avoid burst

            for (let s = 0; s < toConsume; s++) {
                // Read one sample from each lead
                const vals = ECG_LEADS.map((_l, li) =>
                    _ecgRingBuf[ECG_LEADS[li]] ? _ecgRingBuf[ECG_LEADS[li]][(_ecgRingRead) % ECG_BUF_SIZE] : 0
                );
                _ecgRingConsume(1);

                if (window.ecgViewMode === 'online_grid') _sweepOnline12x1(vals);
                else                                      _sweepOnline4x3(vals);
            }

            // If no WS data yet, show waiting message
            if (_ecgRingWrite === 0) {
                ecgCtx.fillStyle = "rgba(20,184,166,0.5)";
                ecgCtx.font = "bold 13px Inter, sans-serif";
                ecgCtx.textAlign = "center";
                ecgCtx.fillText("Esperando datos WebSocket...", ecgCanvas.width / 2, ecgCanvas.height / 2);
                ecgCtx.textAlign = "left";
            }

            ecgAnimationId = requestAnimationFrame(animateECG);
            return;
        }

        // ── OFFLINE MODE (Lead II Fallback, single-lead sweeping trace) ───────
        const hrDisp = document.getElementById("display-val-8867-4");
        let hr = 72;
        if (hrDisp && hrDisp.textContent !== "--") hr = parseFloat(hrDisp.textContent);
        const beatDuration = 60.0 / hr;

        if (!isPausedSim && hr >= 5.0) {
            ecgPhase += dt / beatDuration;
            if (ecgPhase >= 1.0) ecgPhase = ecgPhase % 1.0;
        }

        let ecgVal = 0;
        if (!isPausedSim && hr >= 5.0) {
            const p = ecgPhase;
            if      (p >= 0.0  && p < 0.08) ecgVal = 0.14 * Math.sin((p/0.08) * Math.PI);
            else if (p >= 0.12 && p < 0.14) ecgVal = -0.08 * ((p - 0.12) / 0.02);
            else if (p >= 0.14 && p < 0.17) {
                const phase = (p - 0.14) / 0.03;
                if (phase < 0.5) ecgVal = -0.08 + (1.18 * (phase / 0.5));
                else             ecgVal = 1.1 - (1.3 * ((phase - 0.5) / 0.5));
            } else if (p >= 0.17 && p < 0.19) ecgVal = -0.2 + (0.2 * ((p - 0.17) / 0.02));
            else if (p >= 0.23 && p < 0.35)   ecgVal = 0.22 * Math.sin(((p - 0.23) / 0.12) * Math.PI);
        }

        if (isPausedSim) {
            audioEngine.stopFlatline();
            audioEngine.stopCritical();
        } else if (hr < 5.0) {
            audioEngine.stopCritical();
            audioEngine.startFlatline();
        } else {
            audioEngine.stopFlatline();
            if (activeState === "shock" || activeState === "epoc" || activeState === "sepsis" || activeState === "crisis") audioEngine.startCriticalAlarm();
            else audioEngine.stopCritical();
        }

        if (!isPausedSim && hr >= 5.0) {
            if (ecgPhase >= 0.14 && ecgPhase < 0.17) {
                if (!hasBeeped) {
                    audioEngine.playHeartbeat(hr > 120 ? 620 : 550);
                    hasBeeped = true;
                }
            } else hasBeeped = false;
        }

        const height = ecgCanvas.height;
        const scale  = height * 0.35;
        const noiseVal = parseFloat(document.getElementById("slider-noise").value);
        const noise    = (Math.random() - 0.5) * (noiseVal / 10.0) * 0.25;

        const finalY = (height / 2) - ((ecgVal + noise) * scale);
        const speed  = 150;
        const dx     = speed * dt;
        const nextX  = ecgX + dx;

        ecgCtx.lineWidth    = 2.5;
        ecgCtx.lineCap      = "round";
        ecgCtx.strokeStyle  = "#10b981";
        ecgCtx.shadowBlur   = 8;
        ecgCtx.shadowColor  = "#10b981";

        ecgCtx.clearRect(ecgX, 0, Math.max(25, dx + 5), height);
        ecgCtx.beginPath();
        ecgCtx.moveTo(ecgX, ecgY);
        ecgCtx.lineTo(nextX, finalY);
        ecgCtx.stroke();
        ecgCtx.shadowBlur = 0;

        ecgX = nextX;
        ecgY = finalY;

        if (ecgX >= ecgCanvas.width) {
            ecgX = 0;
            ecgCtx.clearRect(0, 0, 30, height);
        }

        updateEcgDiagnostics(hr, isPausedSim);
        ecgAnimationId = requestAnimationFrame(animateECG);
    }

    ecgAnimationId = requestAnimationFrame(animateECG);
}


/**
 * Detener y apagar la simulación de ECG y alarmas asociadas
 */
function stopEcgSimulation() {
    if (ecgAnimationId) {
        cancelAnimationFrame(ecgAnimationId);
        ecgAnimationId = null;
    }
    audioEngine.stopFlatline();
    audioEngine.stopCritical();
}

/**
 * Calcular y renderizar en pantalla los intervalos diagnósticos cardíacos (PR, QRS, QTc)
 */
function updateEcgDiagnostics(hr, isPausedSim) {
    const prDisp = document.getElementById("ecg-pr-val");
    const qrsDisp = document.getElementById("ecg-qrs-val");
    const qtDisp = document.getElementById("ecg-qt-val");
    const axisDisp = document.getElementById("ecg-axis-val");
    const diagDisp = document.getElementById("ecg-diagnostic-val");
    
    if (!prDisp) return;
    
    if (isPausedSim) {
        prDisp.textContent = "--";
        qrsDisp.textContent = "--";
        qtDisp.textContent = "--";
        axisDisp.textContent = "Sin Actividad";
        axisDisp.className = "text-slate-500 font-bold";
        diagDisp.innerHTML = "Consola de telemetría detenida. Esperando activación...";
        return;
    }
    
    if (hr < 5.0) {
        prDisp.textContent = "--";
        qrsDisp.textContent = "--";
        qtDisp.textContent = "--";
        axisDisp.textContent = "AUSENTE (0°)";
        axisDisp.className = "text-red-500 font-bold animate-pulse";
        diagDisp.innerHTML = "<span class='text-red-500 font-bold animate-pulse flex items-center gap-1.5 inline-flex'><svg class='w-4 h-4 text-red-500 inline-block animate-bounce flex-shrink-0' fill='none' viewBox='0 0 24 24' stroke='currentColor' stroke-width='2.5'><path stroke-linecap='round' stroke-linejoin='round' d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' /></svg> ASISTOLIA / PARO CARDÍACO DETECTADO.</span> Iniciar RCP de urgencia e inyectar adrenalina.";
        return;
    }
    
    const pr = Math.max(0.12, Math.min(0.20, 0.20 - ((hr - 60) * 0.001)));
    const qrs = 0.08;
    const rr = 60.0 / hr;
    const qt = 0.41 * Math.sqrt(rr); // Ecuación de Bazett
    
    prDisp.textContent = `${pr.toFixed(2)} s`;
    qrsDisp.textContent = `${qrs.toFixed(2)} s`;
    qtDisp.textContent = `${qt.toFixed(2)} s`;
    
    const spo2Disp = document.getElementById("display-val-2708-6");
    const tempDisp = document.getElementById("display-val-8310-5");
    const spo2 = spo2Disp && spo2Disp.textContent !== "--" ? parseFloat(spo2Disp.textContent) : 98;
    const temp = tempDisp && tempDisp.textContent !== "--" ? parseFloat(tempDisp.textContent) : 36.6;
    
    if (hr > 120.0) {
        axisDisp.textContent = "Normal (+68°)";
        axisDisp.className = "text-yellow-500 font-bold";
        diagDisp.innerHTML = "<span class='text-yellow-400 font-bold'>Taquicardia Sinusal.</span> Descartar shock, sepsis, deshidratación o fiebre activa.";
    } else if (spo2 < 90.0) {
        axisDisp.textContent = "Desviación Izquierda (-12°)";
        axisDisp.className = "text-red-500 font-bold";
        diagDisp.innerHTML = "<span class='text-red-500 font-bold'>Hipoxia Severa Detectada.</span> Sufrimiento cardíaco agudo por hipoxia. Peligro de acidosis.";
    } else if (temp >= 38.5) {
        axisDisp.textContent = "Normal (+54°)";
        axisDisp.className = "text-yellow-500 font-bold";
        diagDisp.innerHTML = "<span class='text-yellow-400 font-bold'>Hipertermia / Fiebre.</span> El pulso se eleva por demanda metabólica refleja celular.";
    } else {
        axisDisp.textContent = "Normal (+58°)";
        axisDisp.className = "text-emerald-400 font-bold";
        diagDisp.innerHTML = "<span class='text-emerald-400 font-bold'>Ritmo Sinusal Regular.</span> Intervalos PR y QTc normales. Conducción auriculoventricular íntegra.";
    }
}
