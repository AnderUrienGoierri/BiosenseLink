/**
 * BiosenseLink - Sistema de Internacionalización Dinámico (i18n)
 * Soporta cambio en caliente de idioma entre Español (ES) y Euskara (EU).
 */

const TRANSLATIONS = {
    es: {
        "portal-title": "Autenticación Médica PoC",
        "portal-desc": "Acceso de seguridad local mediante sincronización PostgreSQL",
        "pin-placeholder": "Ingrese PIN Clínico (ej. 1234)",
        "login-btn": "Iniciar Sesión",
        "login-error": "PIN inválido o error en PostgreSQL. Intente 9999 (sysadmin), 4321 (Tutor_1), 1234 (Medikua_1) o 5678 (Erizaina_1).",
        
        "rbac-badge-admin": "MODO CONTROL (ADMIN)",
        "rbac-badge-nurse": "MODO CONSULTA (ERIZAIN)",
        
        "menu-device": "DISPOSITIVO ACTIVO",
        "menu-scenarios": "ESCENARIOS CLÍNICOS (TRIAGE)",
        "menu-patient": "PACIENTE ACTIVO",
        "menu-cdss": "ASISTENTE DIAGNÓSTICO CON IA",
        
        "scen-normal": "Estado Normal (Fisiológico)",
        "scen-pcr": "Parada Cardiorrespiratoria (PCR)",
        "scen-shock": "Shock Séptico (Hipotensión)",
        "scen-crisis": "Crisis Hipertensiva",
        "scen-epoc": "Crisis EPOC (Hipoxia severa)",
        "scen-sepsis": "Sepsis Generalizada",
        
        "card-hr": "FRECUENCIA CARDÍACA",
        "card-spo2": "SATURACIÓN OXÍGENO",
        "card-temp": "TEMPERATURA CORPORAL",
        "card-bp": "PRESIÓN ARTERIAL (PA)",
        
        "lbl-paciente": "Paciente:",
        "lbl-genero": "Género:",
        "lbl-edad": "Edad:",
        "lbl-peso": "Peso:",
        "lbl-altura": "Altura:",
        "lbl-patologia": "Patología:",
        
        "btn-interpret": "GENERAR ANÁLISIS CON IA (OLLAMA CDSS)",
        "btn-desktop": "Visualizador de Escritorio",
        "btn-logout": "Cerrar Sesión",
        
        "log-header": "CONSOLA DE TELEMETRÍA IOMT & AUDITORÍA CLÍNICA",
        "log-conn-ok": "Conectado al stream de ECG en puerto 8081",
        "log-conn-err": "Desconectado. Intentando reconectar...",
        
        "welch-title": "Vital Signs Monitor",
        "welch-subtitle": "Evaluación de Signos Vitales Básicos • Welch Allyn Connex",
        
        "philips-title": "IntelliVue Patient Monitor",
        "philips-subtitle": "Monitoreo Multiparamétrico Crítico • Philips Medical",
        
        "net-local": "MODO LOCAL (WIFI)",
        "net-offline": "MODO OFFLINE (JS)",
        
        "patient-list-lbl": "SELECCIONAR PACIENTE DE BBDD",
        "patient-new-btn": "CREAR PACIENTE NUEVO",
        
        "modal-new-title": "Registrar Nuevo Paciente en PostgreSQL",
        "modal-new-id": "ID Clínico:",
        "modal-new-name": "Nombre Completo:",
        "modal-new-age": "Edad:",
        "modal-new-weight": "Peso (kg):",
        "modal-new-height": "Altura (cm):",
        "modal-new-gender": "Género:",
        "modal-new-pathology": "Patología Preexistente:",
        "modal-new-save": "Guardar en PostgreSQL",
        "modal-new-cancel": "Cancelar"
    },
    eu: {
        "portal-title": "PoC Autentifikazio Medikoa",
        "portal-desc": "Tokiko segurtasun-sarbidea PostgreSQL sinkronizazio bidez",
        "pin-placeholder": "Sartu PIN klinikoa (adib. 1234)",
        "login-btn": "Saioa Hasi",
        "login-error": "PIN baliogabea edo errorea PostgreSQL-n. Saiatu 9999 (sysadmin), 4321 (Tutor_1), 1234 (Medikua_1) edo 5678 (Erizaina_1).",
        
        "rbac-badge-admin": "KONTROL MODOA (ADMIN)",
        "rbac-badge-nurse": "KONSULTA MODOA (ERIZAIN)",
        
        "menu-device": "GAILU AKTIBOA",
        "menu-scenarios": "ESZENATOKI KLINIKOAK (TRIAGE)",
        "menu-patient": "PAZIENTE AKTIBOA",
        "menu-cdss": "DIAGNOSTIKO ASISTENTEA AA BIDEZ",
        
        "scen-normal": "Egoera Normala (Fisiologikoa)",
        "scen-pcr": "Bihotz-Biriketako Gelditzea (PCR)",
        "scen-shock": "Shock Septikoa (Hipotentsioa)",
        "scen-crisis": "Krisialdi Hipertentsiboa",
        "scen-epoc": "EPOC Krisia (Hipoxia larria)",
        "scen-sepsis": "Sepsis Orokorra",
        
        "card-hr": "BIHOTZ-MAIZTASUNA",
        "card-spo2": "OXIGENO SATURAZIOA",
        "card-temp": "GORPUTZ TENPERATURA",
        "card-bp": "PRESIO ARTERIALA (PA)",
        
        "lbl-paciente": "Pazientea:",
        "lbl-genero": "Generoa:",
        "lbl-edad": "Adina:",
        "lbl-peso": "Pisua:",
        "lbl-altura": "Altuera:",
        "lbl-patologia": "Aurretiko Patologia:",
        
        "btn-interpret": "DIAGNOSTIKOA SORTU AA BIDEZ (OLLAMA CDSS)",
        "btn-desktop": "Mahaigaineko Ikustailea",
        "btn-logout": "Saioa Itxi",
        
        "log-header": "IOMT TELEMETRIA KONSOLA ETA AUDITORIA KLINIKOA",
        "log-conn-ok": "EKG konexioa ireki da 8081 atakan",
        "log-conn-err": "Deskonektatuta. Berriro konektatzen saiatzen...",
        
        "welch-title": "Signo Bizigarrien Monitorea",
        "welch-subtitle": "Oinarrizko Signo Bizigarrien Ebaluazioa • Welch Allyn Connex",
        
        "philips-title": "IntelliVue Paziente Monitorea",
        "philips-subtitle": "Parametro Anitzeko Monitorizazio Kritikoa • Philips Medical",
        
        "net-local": "TOKO MODOA (WIFI)",
        "net-offline": "OFFLINE MODOA (JS)",
        
        "patient-list-lbl": "HAUTATU PAZIENTEA DATU-BASETIK",
        "patient-new-btn": "PAZIENTE BERRIA SORTU",
        
        "modal-new-title": "Paziente Berria Erregistratu PostgreSQL-n",
        "modal-new-id": "ID Klinikoa:",
        "modal-new-name": "Izen-Abizenak:",
        "modal-new-age": "Adina:",
        "modal-new-weight": "Pisua (kg):",
        "modal-new-height": "Altuera (cm):",
        "modal-new-gender": "Generoa:",
        "modal-new-pathology": "Aurretiko Patologia:",
        "modal-new-save": "Gorde PostgreSQL-n",
        "modal-new-cancel": "Utzi"
    }
};

let currentLang = localStorage.getItem("biosenselink_lang") || "es";

function changeLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("biosenselink_lang", lang);
    applyUILanguage();
    
    // Loguear el cambio
    const msg = lang === "es" ? "Idioma cambiado a Español" : "Hizkuntza Euskarara aldatu da";
    logMessage(msg, "info");
}

function applyUILanguage() {
    const dict = TRANSLATIONS[currentLang];
    if (!dict) return;
    
    // 1. Textos data-i18n
    const elements = document.querySelectorAll("[data-i18n]");
    elements.forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (dict[key]) {
            el.innerText = dict[key];
        }
    });
    
    // 2. Placeholders data-i18n-placeholder
    const placeholders = document.querySelectorAll("[data-i18n-placeholder]");
    placeholders.forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (dict[key]) {
            el.setAttribute("placeholder", dict[key]);
        }
    });
    
    // 3. Titles data-i18n-title
    const titles = document.querySelectorAll("[data-i18n-title]");
    titles.forEach(el => {
        const key = el.getAttribute("data-i18n-title");
        if (dict[key]) {
            el.setAttribute("title", dict[key]);
        }
    });
    
    // 4. Cambiar clases de los botones selectores del header
    const btnEs = document.getElementById("lang-btn-es");
    const btnEu = document.getElementById("lang-btn-eu");
    if (btnEs && btnEu) {
        if (currentLang === "es") {
            btnEs.className = "px-2.5 py-1 rounded-lg bg-medical-500 text-white font-bold text-[10px] transition cursor-pointer";
            btnEu.className = "px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 font-bold text-[10px] hover:text-white transition cursor-pointer";
        } else {
            btnEu.className = "px-2.5 py-1 rounded-lg bg-medical-500 text-white font-bold text-[10px] transition cursor-pointer";
            btnEs.className = "px-2.5 py-1 rounded-lg bg-slate-950 border border-slate-800 text-slate-400 font-bold text-[10px] hover:text-white transition cursor-pointer";
        }
    }
    
    // 5. Actualizar dinámicamente etiquetas variables de cabecera
    if (typeof activeDevice !== "undefined") {
        updateHeaderLabels();
    }
    
    // 6. Actualizar textos de logs de consola si existen
    const logHeader = document.querySelector("#scada-logs-section h3");
    if (logHeader) {
        logHeader.innerText = dict["log-header"];
    }
}

function updateHeaderLabels() {
    const dict = TRANSLATIONS[currentLang];
    const headerTitle = document.getElementById("header-device-title");
    const headerSubtitle = document.getElementById("header-device-subtitle");
    
    if (headerTitle && headerSubtitle) {
        if (activeDevice === "welch-allyn") {
            headerTitle.innerText = dict["welch-title"];
            headerSubtitle.innerText = dict["welch-subtitle"];
        } else if (activeDevice === "philips-intellivue") {
            headerTitle.innerText = dict["philips-title"];
            headerSubtitle.innerText = dict["philips-subtitle"];
        }
    }
}
