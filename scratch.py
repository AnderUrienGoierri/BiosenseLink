import re

file_path = r'c:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink\frontend\www\index.html'

# Open with latin-1 or windows-1252 to avoid decode errors
with open(file_path, 'r', encoding='latin-1') as f:
    content = f.read()

replacements = {
    'Identificaci\u00f3n Profesional': '<span id="auth-title">Identificaci\u00f3n Profesional</span>',
    'Acceso restringido para el personal del Servicio Vasco de Salud': '<span id="auth-desc">Acceso restringido para el personal del Servicio Vasco de Salud</span>',
    'Seleccionar Profesional': '<span id="select-prof">Seleccionar Profesional</span>',
    'Ander PIN: 1234 | Amaia PIN: 5678': '<span id="pin-hint">Ander PIN: 1234 | Amaia PIN: 5678</span>',
    'Validar Credenciales': '<span id="login-btn">Validar Credenciales</span>',
    'Dispositivos PoC Activos': '<span id="active-devices-title">Dispositivos PoC Activos</span>',
    'Evaluaci\u00f3n de Signos Vitales B\u00e1sicos \u2022 Welch Allyn Connex': '<span id="header-device-subtitle">Evaluaci\u00f3n de Signos Vitales B\u00e1sicos \u2022 Welch Allyn Connex</span>',
    'Consola de Mando Fisiol\u00f3gico & Control REST': '<span id="console-title">Consola de Mando Fisiol\u00f3gico & Control REST</span>',
    'Controla la telemetr\u00eda, altera el comportamiento f\u00edsico e inyecta ruido de se\u00f1al en vivo.': '<span id="console-desc">Controla la telemetr\u00eda, altera el comportamiento f\u00edsico e inyecta ruido de se\u00f1al en vivo.</span>',
    'Activar Edge Gateway': '<span id="btn-global-start">Activar Edge Gateway</span>',
    'Parada de Emergencia': '<span id="btn-global-stop">Parada de Emergencia</span>',
    'Escenarios Cl\u00ednicos de Triage': '<span id="triage-title">Escenarios Cl\u00ednicos de Triage</span>',
    'Inyecta escenarios de ritmo y constantes sobre el servidor local HAPI FHIR para pruebas.': '<span id="triage-desc">Inyecta escenarios de ritmo y constantes sobre el servidor local HAPI FHIR para pruebas.</span>',
    'Ritmo Sinusal': '<span id="triage-normal">Ritmo Sinusal</span>',
    'Fibrilaci\u00f3n Auricular': '<span id="triage-afib">Fibrilaci\u00f3n Auricular</span>',
    'Taquicardia Ventricular': '<span id="triage-vtach">Taquicardia Ventricular</span>',
    'Asistolia / PCR': '<span id="triage-arrest">Asistolia / PCR</span>',
    'Isquemia STEMI': '<span id="triage-ischemia">Isquemia STEMI</span>',
    'Offline (I)': '<span id="btn-view-single">Offline (I)</span>',
    '12x1 Grid': '<span id="btn-view-grid">12x1 Grid</span>',
    '4x3+1': '<span id="btn-view-4x3">4x3+1</span>',
    'Historial de Peticiones y Conectividad REST/FHIR': '<span id="telemetry-history-title">Historial de Peticiones y Conectividad REST/FHIR</span>',
    'Soporte de Decisi\u00f3n CDSS': '<span id="cdss-btn">Soporte de Decisi\u00f3n CDSS</span>',
    'Lanzar Visualizador de Escritorio': '<span id="desktop-btn">Lanzar Visualizador de Escritorio</span>',
    'Creaci\u00f3n de Pacientes HL7 FHIR': '<span id="patient-creation-title">Creaci\u00f3n de Pacientes HL7 FHIR</span>',
    'Dar de Alta Nuevo Paciente': '<span id="patient-creation-btn">Dar de Alta Nuevo Paciente</span>',
    'Orquestador Cl\u00ednico Interoperable HL7 FHIR R4 \u2022 Osakidetza Simulation Environment v5.0 \u2022 Euskadi (DAM Goierri Eskola)': '<span id="footer-text">Orquestador Cl\u00ednico Interoperable HL7 FHIR R4 \u2022 Osakidetza Simulation Environment v5.0 \u2022 Euskadi (DAM Goierri Eskola)</span>',
    'MODO CONSULTA': '<span id="rbac-badge">MODO CONSULTA</span>',
    'Vital Signs Monitor': '<span id="header-device-title">Vital Signs Monitor</span>',
    'Gasometr\u00eda Arterial': '<span id="istat-name">Gasometr\u00eda Arterial</span>',
    'Gluc\u00f3metro Digital': '<span id="accu-name">Gluc\u00f3metro Digital</span>',
    'Hemograma PoC': '<span id="hemo-name">Hemograma PoC</span>',
    'Modo Local (WiFi)': '<span id="network-mode-btn">Modo Local (WiFi)</span>'
}

for text, rep in replacements.items():
    if rep not in content:
        content = content.replace(text, rep)

with open(file_path, 'w', encoding='latin-1') as f:
    f.write(content)
print('Done!')
