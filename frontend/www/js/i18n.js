const translations = {
    es: {
        // IDs
        "auth-title": "Identificación Profesional",
        "auth-desc": "Acceso restringido para el personal del Servicio Vasco de Salud",
        "select-prof": "Seleccionar Profesional",
        "pin-hint": "TI: 9999 | KA: 4321 | AO: 1234 | AR: 5678",
        "login-btn": "Validar Credenciales",
        "active-devices-title": "Dispositivos PoC Activos",
        "welch-name": "Vital Signs Monitor",
        "istat-name": "Gasometría Arterial",
        "accu-name": "Glucómetro Digital",
        "hemo-name": "Hemograma PoC",
        "header-device-title": "Vital Signs Monitor",
        "rbac-badge": "MODO CONSULTA",
        "header-device-subtitle": "Evaluación de Signos Vitales Básicos • Welch Allyn Connex",
        "network-mode-btn": "Modo Local (WiFi)",
        "console-title": "Consola de Mando Fisiológico & Control REST",
        "console-desc": "Controla la telemetría, altera el comportamiento físico e inyecta ruido de señal en vivo.",
        "btn-global-start": "Activar Edge Gateway",
        "btn-global-stop": "Parada de Emergencia",
        "triage-title": "Escenarios Clínicos de Triage",
        "triage-desc": "Inyecta escenarios de ritmo y constantes sobre el servidor local HAPI FHIR para pruebas.",
        "triage-normal": "Ritmo Sinusal",
        "triage-afib": "Fibrilación Auricular",
        "triage-vtach": "Taquicardia Ventricular",
        "triage-arrest": "Asistolia / PCR",
        "triage-ischemia": "Isquemia STEMI",
        "btn-view-single": "Offline (I)",
        "btn-view-grid": "12x1 Grid",
        "btn-view-4x3": "4x3+1",
        "telemetry-history-title": "Historial de Peticiones y Conectividad REST/FHIR",
        "cdss-btn": "Soporte de Decisión CDSS",
        "desktop-btn": "Lanzar Visualizador de Escritorio",
        "patient-creation-title": "Creación de Pacientes HL7 FHIR",
        "patient-creation-btn": "Dar de Alta Nuevo Paciente",
        "footer-text": "Orquestador Clínico Interoperable HL7 FHIR R4 • Osakidetza Simulation Environment v5.0 • Euskadi (DAM Goierri Eskola)"
    },
    eu: {
        // IDs
        "auth-title": "Identifikazio Profesionala",
        "auth-desc": "Euskal Osasun Zerbitzuko langileentzat sarbide mugatua",
        "select-prof": "Profesionala Hautatu",
        "pin-hint": "TI: 9999 | KA: 4321 | AO: 1234 | AR: 5678",
        "login-btn": "Kredentzialak Egiaztatu",
        "active-devices-title": "PoC Gailu Aktiboak",
        "welch-name": "Bizi-seinaleen Monitorea",
        "istat-name": "Gasometria Arteriala",
        "accu-name": "Glukometro Digitala",
        "hemo-name": "Hemograma PoC",
        "header-device-title": "Bizi-seinaleen Monitorea",
        "rbac-badge": "KONTSULTA MODUA",
        "header-device-subtitle": "Oinarrizko Bizi-seinaleen Ebaluazioa • Welch Allyn Connex",
        "network-mode-btn": "Modu Lokala (WiFi)",
        "console-title": "Aginte-Kontsola Fisiologikoa & REST Kontrola",
        "console-desc": "Telemetria kontrolatu, portaera fisikoa aldatu eta seinale zarata injektatu zuzenean.",
        "btn-global-start": "Edge Gateway Aktibatu",
        "btn-global-stop": "Larrialdiko Geldialdia",
        "triage-title": "Triage Eszenatoki Klinikoak",
        "triage-desc": "Erritmo eta konstante eszenatokiak injektatu tokiko HAPI FHIR zerbitzarian probetarako.",
        "triage-normal": "Erritmo Sinusala",
        "triage-afib": "Fibrilazio Aurikularra",
        "triage-vtach": "Takikardia Bentrikularra",
        "triage-arrest": "Asistolia / PCR",
        "triage-ischemia": "Iskemia STEMI",
        "btn-view-single": "Offline (I)",
        "btn-view-grid": "12x1 Sareta",
        "btn-view-4x3": "4x3+1",
        "telemetry-history-title": "Eskaeren Historia eta REST/FHIR Konektibitatea",
        "cdss-btn": "Erabakiak Hartzeko Laguntza CDSS",
        "desktop-btn": "Mahaigaineko Ikusgailua Abiarazi",
        "patient-creation-title": "HL7 FHIR Pazienteen Sorkuntza",
        "patient-creation-btn": "Paziente Berria Alta Eman",
        "footer-text": "Orkestratzaile Kliniko Elkarreragilea HL7 FHIR R4 • Osakidetza Simulation Environment v5.0 • Euskadi (DAM Goierri Eskola)"
    }
};

let currentLang = 'es';

function changeLanguage(lang) {
    if (!translations[lang]) return;
    currentLang = lang;
    
    const esBtn = document.getElementById('lang-btn-es');
    const euBtn = document.getElementById('lang-btn-eu');
    
    if (esBtn && euBtn) {
        if (lang === 'es') {
            esBtn.classList.add('bg-medical-500', 'text-white');
            esBtn.classList.remove('bg-slate-950', 'text-slate-400');
            euBtn.classList.remove('bg-medical-500', 'text-white');
            euBtn.classList.add('bg-slate-950', 'text-slate-400');
        } else {
            euBtn.classList.add('bg-medical-500', 'text-white');
            euBtn.classList.remove('bg-slate-950', 'text-slate-400');
            esBtn.classList.remove('bg-medical-500', 'text-white');
            esBtn.classList.add('bg-slate-950', 'text-slate-400');
        }
    }

    // Apply translations directly by ID (this avoids modifying the massive HTML file directly)
    for (const [id, text] of Object.entries(translations[lang])) {
        const el = document.getElementById(id);
        if (el) {
            // Check if element has child elements, if it does, we only want to replace the text node
            // But for our case, most of these IDs just contain text or we can just replace innerHTML.
            // Let's use innerHTML or textContent carefully.
            
            // Special handling for elements that might contain SVGs like headers
            if (id === "console-title" || id === "telemetry-history-title" || id === "triage-title" || id === "patient-creation-title" || id === "header-device-title" || id === "desktop-btn") {
               // We find the last span or text node to replace, to preserve icons
               const span = el.querySelector('span:last-child');
               if (span) {
                   span.textContent = text;
               } else {
                   // Fallback
                   el.innerHTML = text; // MIGHT overwrite SVG if not careful, but we assume we assigned IDs to spans
               }
            } else {
               el.textContent = text;
            }
        }
    }

    // Also target elements with data-i18n if they exist
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang][key]) {
            el.innerHTML = translations[lang][key];
        }
    });

    localStorage.setItem('biosenselink_lang', lang);
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang: lang } }));
}

// Ensure the language change button actually works and is attached if not loaded inline
document.addEventListener('DOMContentLoaded', () => {
    // Some IDs in index.html might need tweaking to match the JS above.
    // I will write a script to inject these IDs into index.html where necessary.
    const savedLang = localStorage.getItem('biosenselink_lang') || 'es';
    changeLanguage(savedLang);
});
