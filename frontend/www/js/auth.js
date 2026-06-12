/**
 * SISTEMA DE AUTENTICACIÓN Y SEGURIDAD RBAC (auth.js)
 * Control de perfiles de ciberseguridad, validación de PINs y privilegios de UI.
 */

/**
 * Cambiar selección visual entre los perfiles clínicos en el Portal (4 perfiles)
 */
function selectAuthProfile(profileType) {
    activeProfile = profileType;
    
    const profiles = ['admin', 'tutoria', 'medicina', 'enfermeria'];
    const btnIds = {
        'admin': 'profile-btn-admin',
        'tutoria': 'profile-btn-tutor',
        'medicina': 'profile-btn-doctor',
        'enfermeria': 'profile-btn-nurse'
    };
    
    profiles.forEach(p => {
        const btn = document.getElementById(btnIds[p]);
        if (!btn) return;
        if (p === profileType) {
            btn.className = "p-3 rounded-xl border transition-all text-left flex flex-col justify-between h-24 bg-slate-950/40 border-medical-500/30 text-medical-400 ring-2 ring-medical-500/10";
        } else {
            btn.className = "p-3 rounded-xl border transition-all text-left flex flex-col justify-between h-24 bg-slate-950/20 border-slate-800 text-slate-500 hover:border-slate-750 hover:text-slate-450";
        }
    });
    
    document.getElementById("auth-pin").value = "";
    document.getElementById("auth-error-msg").classList.add("hidden");
}

/**
 * Evaluar el PIN introducido en pantalla contra la base de datos PostgreSQL
 */
async function attemptLogin() {
    const pin = document.getElementById("auth-pin").value;
    const errorMsg = document.getElementById("auth-error-msg");
    
    try {
        // Enviar POST a la API para validar (usando 127.0.0.1 para tunel ADB USB)
        const response = await fetch('http://localhost:8081/api/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin: pin })
        });
        
        const data = await response.json();
        
        if (data.status === "ok") {
            // Check if the returned role matches the selected activeProfile, unless it's an admin or tutor
            if ((activeProfile === "enfermeria" || activeProfile === "medicina") && (data.role === "admin" || data.role === "tutoria")) {
                // Allows an admin/tutor to log into a restricted console just fine, but we respect the selected view
            } else {
                activeProfile = data.role; // Assume the DB role
            }
            
            sessionStorage.setItem("clinical_session_user", data.display_name);
            sessionStorage.setItem("clinical_session_role", activeProfile);
            sessionStorage.setItem("clinical_session_title", data.title);
            
            // Activar el canal de audio del navegador
            if (typeof audioEngine !== 'undefined') {
                audioEngine.setMute(false);
                document.getElementById("audio-icon-muted").classList.add("hidden");
                document.getElementById("audio-icon-unmuted").classList.remove("hidden");
                
                // Tonos bip-bip de bienvenida exitosa
                audioEngine.playHeartbeat(800);
                setTimeout(() => audioEngine.playHeartbeat(1100), 80);
            }
            
            const portal = document.getElementById("auth-portal");
            portal.classList.add("opacity-0", "pointer-events-none");
            
            if (typeof startPythonBackendWS === 'function') {
                startPythonBackendWS();
            }
            applyRBAC();
        } else {
            // Zumbido grave indicando acceso denegado
            if (typeof audioEngine !== 'undefined') {
                audioEngine.setMute(false);
                audioEngine.playHeartbeat(150);
            }
            
            errorMsg.classList.remove("hidden");
            const card = document.querySelector("#auth-portal > div");
            card.classList.add("animate-bounce");
            setTimeout(() => card.classList.remove("animate-bounce"), 500);
        }
    } catch (err) {
        console.error("Error conectando con API de auth Postgres:", err);
        errorMsg.textContent = "Error de red conectando con el servidor";
        errorMsg.classList.remove("hidden");
    }
}

/**
 * Aplicar restricciones de Role-Based Access Control (RBAC) sobre el DOM en tiempo real
 */
function applyRBAC() {
    const user = sessionStorage.getItem("clinical_session_user");
    const role = sessionStorage.getItem("clinical_session_role");
    const title = sessionStorage.getItem("clinical_session_title");
    
    if (!user) {
        document.getElementById("auth-portal").classList.remove("opacity-0", "pointer-events-none");
        return;
    }
    
    document.getElementById("auth-portal").classList.add("opacity-0", "pointer-events-none");
    document.getElementById("user-display-name").textContent = user;
    document.getElementById("user-display-title").textContent = title;
    document.getElementById("user-avatar-initials").textContent = user.split(" ").map(n => n[0]).join("").substring(0,2);
    if (typeof applyUILanguage === "function") applyUILanguage();
    
    const badge = document.getElementById("rbac-badge");
    const triageLock = document.getElementById("triage-rbac-lock");
    const configLock = document.getElementById("configurator-rbac-lock");
    
    if (role === "nurse" || role === "enfermeria" || role === "medicina") {
        badge.className = "px-2 py-0.5 rounded bg-yellow-950 border border-yellow-500/20 text-yellow-400 font-mono text-[9px] font-bold uppercase tracking-wider";
        if (role === "medicina") {
            badge.textContent = (typeof currentLang !== "undefined" && currentLang === "eu") ? "KONSULTA MODOA (MEDIKUA)" : "MODO CONSULTA (MEDICINA)";
        } else {
            badge.textContent = (typeof currentLang !== "undefined" && currentLang === "eu") ? "KONSULTA MODOA (ERIZAIN)" : "MODO CONSULTA (ENFERMERÍA)";
        }
        if (triageLock) triageLock.classList.remove("hidden");
        if (configLock) configLock.classList.remove("hidden");
    } else {
        badge.className = "px-2 py-0.5 rounded bg-teal-950 border border-teal-500/20 text-teal-400 font-mono text-[9px] font-bold uppercase tracking-wider";
        if (role === "tutoria") {
            badge.textContent = (typeof currentLang !== "undefined" && currentLang === "eu") ? "KONTROL MODOA (TUTOREA)" : "MODO TUTOR (SIMULACIÓN)";
        } else {
            badge.textContent = (typeof currentLang !== "undefined" && currentLang === "eu") ? "KONTROL MODOA (ADMIN)" : "ACCESO TOTAL (JEFE DE SERVICIO)";
        }
        if (triageLock) triageLock.classList.add("hidden");
        if (configLock) configLock.classList.add("hidden");
    }
}

/**
 * Cerrar sesión, borrar llaves y silenciar alarmas acústicas de forma segura
 */
function logout() {
    sessionStorage.clear();
    audioEngine.setMute(true);
    
    const mutedIcon = document.getElementById("audio-icon-muted");
    const unmutedIcon = document.getElementById("audio-icon-unmuted");
    mutedIcon.classList.remove("hidden");
    unmutedIcon.classList.add("hidden");
    
    document.getElementById("auth-pin").value = "";
    document.getElementById("auth-portal").classList.remove("opacity-0", "pointer-events-none");
    document.getElementById("auth-error-msg").classList.add("hidden");
}

/**
 * Mostrar / Ocultar el panel de control de base de datos en pantalla de Login
 */
function toggleDbPanel(e) {
    if (e) e.stopPropagation();
    const panel = document.getElementById("db-control-panel");
    if (!panel) return;
    if (panel.classList.contains("hidden")) {
        panel.classList.remove("hidden");
        verifyDbConnection();
    } else {
        panel.classList.add("hidden");
    }
}

/**
 * Verificar el estado de la conexión a la base de datos PostgreSQL desde la API
 */
async function verifyDbConnection() {
    const statusText = document.getElementById("db-status-text");
    const statusDot = document.getElementById("db-status-dot");
    const detailsText = document.getElementById("db-details-text");
    
    if (!statusText || !statusDot || !detailsText) return;
    
    statusText.textContent = "Verificando...";
    statusDot.className = "w-2.5 h-2.5 rounded-full bg-yellow-500 animate-pulse";
    
    try {
        const response = await fetch('http://localhost:8081/api/db/status');
        const data = await response.json();
        
        if (data.db_available && data.db_connection_allowed) {
            statusText.textContent = "CONECTADO (ONLINE)";
            statusText.className = "text-xs font-bold text-emerald-400";
            statusDot.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
        } else if (!data.db_connection_allowed) {
            statusText.textContent = "DESCONECTADO (FORZADO)";
            statusText.className = "text-xs font-bold text-red-400";
            statusDot.className = "w-2.5 h-2.5 rounded-full bg-red-500";
        } else {
            statusText.textContent = "ERROR DE CONEXIÓN";
            statusText.className = "text-xs font-bold text-amber-500";
            statusDot.className = "w-2.5 h-2.5 rounded-full bg-amber-500";
        }
        
        detailsText.innerHTML = `Host: localhost:5432<br>DB: medical_platform<br>Allowed: ${data.db_connection_allowed}<br>Available: ${data.db_available}<br>Details: ${data.details || 'OK'}`;
    } catch (err) {
        statusText.textContent = "ERROR DE SERVIDOR API";
        statusText.className = "text-xs font-bold text-red-500";
        statusDot.className = "w-2.5 h-2.5 rounded-full bg-red-600";
        detailsText.textContent = "No se pudo conectar con el servidor backend FastAPI en el puerto 8081. Asegúrese de que server.py esté iniciado.";
    }
}

/**
 * Conectar o desconectar la base de datos PostgreSQL mediante una petición a la API
 */
async function controlDbConnection(action) {
    const endpoint = action === 'connect' ? 'connect' : 'disconnect';
    try {
        await fetch(`http://localhost:8081/api/db/${endpoint}`, { method: 'POST' });
        verifyDbConnection();
    } catch (err) {
        console.error("Error al controlar conexión de base de datos:", err);
    }
}
