/**
 * MOTOR DE INTEROPERABILIDAD Y CONEXIÓN REST/FHIR (api.js)
 * Manejo de llamadas fetch de red y persistencia relacional en Postgres.
 */

/**
 * Enviar Peticiones REST de control al servidor HTTP local en 8081
 */
async function sendControlRequest(params) {
    try {
        const response = await fetch(`${CONTROL_URL}?${params}`);
        if (!response.ok) throw new Error();
        const data = await response.json();
        
        document.getElementById("interval-display").textContent = `${data.interval.toFixed(1)} seg`;
        document.getElementById("slider-interval").value = data.interval;
        
        const noiseText = data.noise === 0 ? "Sin Ruido" : `Ruido: ${data.noise.toFixed(0)}0%`;
        document.getElementById("noise-display").textContent = noiseText;
        document.getElementById("slider-noise").value = data.noise;
        
        if (data.is_paused) {
            document.getElementById("btn-power-on").className = "px-3 py-1.5 rounded-lg bg-slate-800 text-slate-400 border border-slate-700 text-xs font-bold transition hover:bg-slate-700 flex items-center gap-1.5";
            document.getElementById("btn-power-on").innerHTML = "🔴 FUERA DE LÍNEA";
        } else {
            document.getElementById("btn-power-on").className = "px-3 py-1.5 rounded-lg bg-emerald-950/40 text-emerald-400 border border-emerald-500/20 text-xs font-bold transition hover:bg-emerald-900/30 flex items-center gap-1.5";
            document.getElementById("btn-power-on").innerHTML = `<span class="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping"></span> TRANSMITIENDO`;
        }

        document.getElementById("ping-indicator").className = "w-2 h-2 rounded-full bg-emerald-500 animate-ping";
        document.getElementById("connection-status").textContent = "Control Activo (Puerto 8081)";
        document.getElementById("connection-status").className = "text-emerald-500 font-mono text-[10px]";
        
        return data;
    } catch (err) {
        document.getElementById("ping-indicator").className = "w-2 h-2 rounded-full bg-red-500 animate-pulse";
        document.getElementById("connection-status").textContent = "Offline (Puerto 8081 Desconectado)";
        document.getElementById("connection-status").className = "text-red-500 font-mono text-[10px]";
        return null;
    }
}

/**
 * Enviar comando de acción directa al emulador (pausar/reanudar)
 */
async function sendControlAction(action) {
    logMessage(`POST /api/control?action=${action} ...`, "info");
    await sendControlRequest(`action=${action}`);
}

/**
 * Cambiar el intervalo de muestreo en caliente
 */
async function updateInterval(val) {
    document.getElementById("interval-display").textContent = `${parseFloat(val).toFixed(1)} seg`;
    pollingIntervalSec = parseInt(val);
    restartPolling();
    await sendControlRequest(`interval=${val}`);
}

/**
 * Cambiar el nivel de ruido fisiológico inyectado
 */
async function updateNoise(val) {
    const label = val === "0" ? "Sin Ruido" : `Ruido: ${val}0%`;
    document.getElementById("noise-display").textContent = label;
    await sendControlRequest(`noise=${val}`);
}

/**
 * Sintonizar el simulador de biosensores hacia un escenario de Triage específico
 */
async function setClinicalState(stateCode) {
    activeState = stateCode;
    logMessage(`POST /api/config/triage { triage: "${stateCode}" } ...`, "warning");
    
    try {
        const response = await fetch(`http://localhost:8081/api/config/triage`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ triage: stateCode })
        });
        
        if (!response.ok) throw new Error();
        
        logMessage(`[OK] Triage inyectado con éxito: ${stateCode.toUpperCase()}`, "success");
        
        renderClinicalButtons();
        fetchVitalsData();
        
    } catch (err) {
        logMessage(`Fallo al inyectar escenario de Triage en el biosensor`, "error");
    }
}

/**
 * Registrar un nuevo Paciente en caliente vía HL7 FHIR (Persistencia en PostgreSQL)
 */
async function registerFhirPatient() {
    const name = document.getElementById("cfg-name").value.trim();
    const lastname = document.getElementById("cfg-lastname").value.trim();
    const age = parseInt(document.getElementById("cfg-age").value);
    const weight = parseFloat(document.getElementById("cfg-weight").value);
    const height = parseFloat(document.getElementById("cfg-height").value);
    const gender = document.getElementById("cfg-gender").value;
    const pathology = document.getElementById("cfg-pathology").value;
    
    if (!name || !lastname || isNaN(age) || isNaN(weight) || isNaN(height)) {
        logMessage("Error de formulario: Por favor rellenar todos los campos del expediente.", "error");
        audioEngine.playHeartbeat(150); // zumbido grave de error
        return;
    }
    
    const newPatientId = `${name.toLowerCase()}-${lastname.toLowerCase()}`.replace(/\s+/g, '-');
    
    // Payload estructurado HL7 FHIR R4
    const patientPayload = {
        resourceType: "Patient",
        id: newPatientId,
        active: true,
        name: [{
            use: "official",
            text: `${name} ${lastname}`,
            family: lastname,
            given: [name]
        }],
        gender: gender,
        birthDate: new Date(new Date().getFullYear() - age, 4, 15).toISOString().split('T')[0],
        telecom: [{ system: "email", value: `${name.toLowerCase()}@osakidetza.eus` }],
        managingOrganization: { display: "Red de Salud Vasca - Osakidetza (Simulación Ph.D.)" },
        extension: [
            { url: "http://hl7.org/fhir/StructureDefinition/patient-weight", valueDecimal: weight },
            { url: "http://hl7.org/fhir/StructureDefinition/patient-height", valueDecimal: height },
            { url: "http://hl7.org/fhir/StructureDefinition/patient-pathology", valueString: pathology }
        ]
    };
    
    logMessage(`PUT /fhir/Patient/${newPatientId} (Persistiendo en Postgres)...`, "info");
    
    try {
        // 1. Persistencia en la Base de Datos a través de HAPI FHIR
        const fhirResponse = await fetch(`${FHIR_URL}/Patient/${newPatientId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/fhir+json; charset=utf-8",
                "Accept": "application/fhir+json"
            },
            body: JSON.stringify(patientPayload)
        });
        
        if (!fhirResponse.ok) throw new Error("Fallo al guardar recurso Patient en HAPI FHIR");
        
        logMessage(`[OK] Paciente persistido en PostgreSQL. ID: Patient/${newPatientId}`, "success");
        
        // 2. Transmitir los nuevos targets fisiológicos al emulador Edge
        const biosensorResponse = await fetch(`http://localhost:8081/api/config/patient`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id: newPatientId,
                name: `${name} ${lastname}`,
                gender: gender,
                age: age,
                weight: weight,
                height: height,
                pathology: pathology
            })
        });
        
        if (!biosensorResponse.ok) throw new Error("Fallo al sincronizar targets con biosensores");
        logMessage(`[OK] Sincronización Edge completada. Biosensores en caliente sintonizados.`, "success");
        
        // 3. Reconfigurar variables globales y limpiar UI
        PATIENT_ID = newPatientId;
        
        // Sonidos agudos sístole de éxito
        audioEngine.playHeartbeat(880);
        setTimeout(() => audioEngine.playHeartbeat(1200), 80);
        
        document.getElementById("cfg-name").value = "";
        document.getElementById("cfg-lastname").value = "";
        document.getElementById("cfg-age").value = "";
        document.getElementById("cfg-weight").value = "";
        document.getElementById("cfg-height").value = "";
        
        // Recargar lista del selector para incluir al nuevo paciente
        await loadPatientsList();
        
        fetchPatientData();
        fetchVitalsData();
        
    } catch (err) {
        logMessage(`Error en registro: ${err.message}`, "error");
        audioEngine.playHeartbeat(150);
    }
}

/**
 * Cargar lista completa de pacientes desde PostgreSQL (a través de HAPI FHIR)
 */
async function loadPatientsList() {
    try {
        const response = await fetch(`${FHIR_URL}/Patient?_count=100`);
        if (!response.ok) throw new Error();
        const bundle = await response.json();
        
        const selectElement = document.getElementById("select-active-patient");
        if (!selectElement) return;
        
        selectElement.innerHTML = "";
        
        if (bundle.entry && bundle.entry.length > 0) {
            bundle.entry.forEach(entry => {
                const patient = entry.resource;
                const firstName = patient.name[0].given.join(" ");
                const lastName = patient.name[0].family;
                const id = patient.id;
                
                const option = document.createElement("option");
                option.value = id;
                option.textContent = `${firstName} ${lastName}`;
                selectElement.appendChild(option);
            });
            
            // Sincronizar selección visual con el paciente activo
            selectElement.value = PATIENT_ID;
        } else {
            const option = document.createElement("option");
            option.value = "ander-patient";
            option.textContent = "Dr. Ander Otxoa (Por Defecto)";
            selectElement.appendChild(option);
        }
    } catch (err) {
        logMessage("No se pudo cargar la lista de pacientes registrados desde PostgreSQL", "warning");
        const selectElement = document.getElementById("select-active-patient");
        if (selectElement) {
            selectElement.innerHTML = `<option value="ander-patient">Dr. Ander Otxoa (Por Defecto)</option>`;
        }
    }
}

/**
 * Cambiar el paciente activo sincronizando el biosensor Edge
 */
async function changeActivePatient(newPatientId) {
    if (!newPatientId) return;
    logMessage(`Sintonizando monitor clínico para Patient/${newPatientId}...`, "info");
    
    try {
        // 1. Obtener la información del paciente desde HAPI FHIR
        const response = await fetch(`${FHIR_URL}/Patient/${newPatientId}`);
        if (!response.ok) throw new Error("No se pudo descargar el recurso del paciente");
        const patient = await response.json();
        
        const firstName = patient.name[0].given.join(" ");
        const lastName = patient.name[0].family;
        const gender = patient.gender;
        const age = new Date().getFullYear() - new Date(patient.birthDate).getFullYear();
        
        // Buscar extensiones fisiológicas (peso, altura, patología)
        let weight = 70.0;
        let height = 175.0;
        let pathology = "none";
        
        if (patient.extension) {
            patient.extension.forEach(ext => {
                if (ext.url.endsWith("patient-weight")) weight = ext.valueDecimal;
                if (ext.url.endsWith("patient-height")) height = ext.valueDecimal;
                if (ext.url.endsWith("patient-pathology")) pathology = ext.valueString;
            });
        }
        
        // 2. Sincronizar el emulador Edge (Python) en puerto 8081
        const biosensorResponse = await fetch(`http://localhost:8081/api/config/patient`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                id: newPatientId,
                name: `${firstName} ${lastName}`,
                gender: gender,
                age: age,
                weight: weight,
                height: height,
                pathology: pathology
            })
        });
        
        if (!biosensorResponse.ok) throw new Error("Fallo al sincronizar targets con emulador");
        logMessage(`[OK] Biosensor sincronizado en caliente con ${firstName} ${lastName}.`, "success");
        
        // 3. Actualizar variable global y refrescar pantalla
        PATIENT_ID = newPatientId;
        
        const selectElement = document.getElementById("select-active-patient");
        if (selectElement) selectElement.value = newPatientId;
        
        // Sonido sístole confirmación
        audioEngine.playHeartbeat(1000);
        
        // Recargar telemetría
        fetchPatientData();
        fetchVitalsData();
        
    } catch (err) {
        logMessage(`Error al cambiar paciente: ${err.message}`, "error");
    }
}

/**
 * Cargar metadatos del paciente activo desde HAPI FHIR y sintonizar en pantalla
 */
async function fetchPatientData() {
    try {
        const response = await fetch(`${FHIR_URL}/Patient/${PATIENT_ID}`);
        if (!response.ok) throw new Error();
        const patient = await response.json();
        
        const firstName = patient.name[0].given.join(" ");
        const lastName = patient.name[0].family;
        const genderText = patient.gender === "male" ? "Varón" : "Mujer";
        const age = new Date().getFullYear() - new Date(patient.birthDate).getFullYear();
        
        document.getElementById("pat-name").textContent = `${firstName} ${lastName}`;
        document.getElementById("pat-gender-age").textContent = `${genderText}, ${age} años (Nacido el: ${patient.birthDate})`;
        document.getElementById("pat-email").textContent = patient.telecom[0].value;
        document.getElementById("pat-org").textContent = patient.managingOrganization.display;
        document.getElementById("pat-id").textContent = `Patient/${patient.id}`;
        
        // Iniciales dinámicas del avatar
        const initials = `${firstName[0] || ""}${lastName[0] || ""}`.toUpperCase();
        const avatar = document.getElementById("pat-avatar");
        if (avatar) avatar.textContent = initials;
        
        // Sincronizar valor seleccionado del dropdown
        const selectElement = document.getElementById("select-active-patient");
        if (selectElement) selectElement.value = PATIENT_ID;
    } catch (err) {
        document.getElementById("pat-name").textContent = "HAPI FHIR Offline";
        document.getElementById("pat-gender-age").textContent = "Docker Compose apagado o en reinicio";
        document.getElementById("pat-email").textContent = "Inicia el servidor Docker...";
    }
}

/**
 * Cargar observaciones recientes del paciente desde HAPI FHIR y redibujar displays/gráficos
 */
async function fetchVitalsData() {
    try {
        const response = await fetch(`${FHIR_URL}/Observation?subject=Patient/${PATIENT_ID}&_count=500&_sort=-date`);
        if (!response.ok) throw new Error();
        const bundle = await response.json();

        if (!bundle.entry || bundle.entry.length === 0) {
            logMessage("Servidor FHIR vacío. Enciende el biosensor para comenzar a inyectar.", "warning");
            return;
        }

        const observations = bundle.entry.map(e => e.resource);
        observations.sort((a, b) => new Date(a.effectiveDateTime) - new Date(b.effectiveDateTime));

        if (observations.length > 0) {
            const latestObs = observations[observations.length - 1];
            const latestTime = latestObs.effectiveDateTime;
            if (latestTime !== lastLoggedTime) {
                logMessage(`GET /fhir/Observation?subject=Patient/${PATIENT_ID} - Recibidas ${observations.length} mediciones R4`, "success");
                lastLoggedTime = latestTime;
            }
        }

        const dev = DEVICES_DATABASE[activeDevice];
        const activeLoincs = dev.metrics.map(m => m.code);
        const filteredObs = observations.filter(o => activeLoincs.includes(o.code.coding[0].code));

        const currentVals = {};
        filteredObs.forEach(obs => {
            const code = obs.code.coding[0].code;
            currentVals[code] = obs.valueQuantity.value;
        });

        activeLoincs.forEach(code => {
            const val = currentVals[code];
            const disp = document.getElementById(`display-val-${code}`);
            if (disp) {
                disp.textContent = val !== undefined ? val.toFixed(2) : "--";
            }
        });

        const maxDataLimit = 15;
        
        Object.entries(charts).forEach(([chartId, chartInstance]) => {
            chartInstance.data.datasets.forEach(dataset => {
                const code = dataset.loincCode;
                
                const metricObs = filteredObs.filter(o => o.code.coding[0].code === code);
                const vals = metricObs.map(o => o.valueQuantity.value).slice(-maxDataLimit);
                const times = metricObs.map(o => new Date(o.effectiveDateTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })).slice(-maxDataLimit);
                
                dataset.data = vals;
                chartInstance.data.labels = times;
            });
            
            chartInstance.update('none');
        });

        evaluarCDSS(currentVals);

    } catch (err) {
        console.error("Error consultando HAPI FHIR", err);
    }
}

// BACKEND PYTHON WEBSOCKET
window.pythonWS = null;
window.lastEcgPayload = null;
function startPythonBackendWS() {
    const ip = document.getElementById('server-ip-input').value || 'localhost';
    const wsUrl = `ws://${ip}:8081/ws/ecg`;
    window.pythonWS = new WebSocket(wsUrl);
    window.pythonWS.onopen = () => { logMessage('Conectado al motor Python 12-Lead', 'success'); };
    window.pythonWS.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if(data.type === 'ecg_stream') {
            window.lastEcgPayload = data;
        }
    };
    window.pythonWS.onerror = (e) => { logMessage('Error WS. Comprueba que server.py está corriendo.', 'error'); };
    window.pythonWS.onclose = () => { logMessage('Desconectado del servidor Python.', 'warning'); };
}

/**
 * Lanzar visualizador de escritorio main.py desde la aplicación web
 */
async function runDesktopVisualizer() {
    logMessage("Enviando orden de lanzamiento para el Visualizador Clínico Desktop...", "info");
    try {
        const response = await fetch("http://localhost:8081/api/run-desktop-visualizer", {
            method: "POST"
        });
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (data.status === "ok") {
            logMessage("¡Visualizador Clínico Desktop lanzado con éxito!", "success");
            if (typeof audioEngine !== 'undefined') {
                audioEngine.playHeartbeat(880);
            }
        } else {
            throw new Error(data.message);
        }
    } catch (err) {
        logMessage(`Fallo al lanzar el Visualizador Clínico: ${err.message || 'servidor desconectado'}`, "error");
        if (typeof audioEngine !== 'undefined') {
            audioEngine.playHeartbeat(150);
        }
    }
}
