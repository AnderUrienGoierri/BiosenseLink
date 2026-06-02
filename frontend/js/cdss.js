/**
 * CEREBRO CLINICAL DECISION SUPPORT SYSTEM - CDSS (cdss.js)
 * Algoritmos clínicos para el diagnóstico, alertas de Triage e inyección IEC 60601-1-8.
 */

/**
 * Evaluar constantes vitales multivariable y actualizar el panel de Triage / Alarmas
 * @param {Object} vals Diccionario indexado por códigos LOINC conteniendo los valores fisiológicos actuales
 */
function evaluarCDSS(vals) {
    const card = document.getElementById("triage-card");
    const tag = document.getElementById("triage-status-tag");
    const title = document.getElementById("triage-title");
    const desc = document.getElementById("triage-desc");
    const action = document.getElementById("triage-action");
    const icon = document.getElementById("triage-icon");

    if (!card) return;

    // Reset de clases de brillo neon
    card.className = "bg-slate-900/40 rounded-xl p-5 border flex flex-col justify-between transition-all duration-300 xl:col-span-2 ";
    
    let status = "NORMAL";
    let severity = "low";
    let titleText = "Dispositivo Estable";
    let descText = "La telemetría del biosensor Point-of-Care reporta parámetros estables y constantes.";
    let metrologicalText = "Acción Metrológica sugerida: Ninguna. El transductor y las sondas reportan excelente impedancia de contacto.";

    // ==========================================
    // 1. MONITOR CARDIOVASCULAR (Welch Allyn)
    // ==========================================
    if (activeDevice === "welch-allyn") {
        const hr = vals["8867-4"];
        const spo2 = vals["2708-6"];
        const temp = vals["8310-5"];
        const sys = vals["8480-6"];
        const dia = vals["8462-4"];

        if (hr !== undefined && spo2 !== undefined && temp !== undefined && sys !== undefined && dia !== undefined) {
            if (hr < 5.0) {
                severity = "critical";
                status = "ASISTOLIA / PARADA CARDÍACA";
                titleText = "Paro Cardiorrespiratorio Inminente";
                descText = "LÍNEA PLANA DE ECG DETECTADA. El paciente se encuentra clínicamente muerto o el cable de Lead II se ha desconectado.";
                metrologicalText = "PROTOCOLO DE ACCIÓN: Iniciar maniobras de RCP, solicitar carro de paradas desfibrilador y comprobar electrodos en el tórax.";
            } else if (spo2 < 93.0 || hr > 120.0 || temp >= 38.5 || sys > 145.0 || sys < 90.0 || dia > 95.0 || dia < 55.0) {
                severity = "critical";
                status = "EMERGENCIA FISIOLÓGICA";
                titleText = "Inestabilidad Clínica Crítica";
                descText = `Alerta de Triage: Se detecta ${spo2 < 93.0 ? 'Hipoxia Crítica (SpO₂: ' + spo2.toFixed(1) + '%). ' : ''}${hr > 120.0 ? 'Taquicardia Aguda (' + hr.toFixed(0) + ' lpm). ' : ''}${temp >= 38.5 ? 'Crisis de Hipertermia (' + temp.toFixed(1) + ' °C). ' : ''}${sys > 145.0 || dia > 95.0 ? 'Crisis Hipertensiva (' + sys.toFixed(0) + '/' + dia.toFixed(0) + ' mmHg). ' : ''}${sys < 90.0 || dia < 55.0 ? 'Hipotensión Severa/Shock (' + sys.toFixed(0) + '/' + dia.toFixed(0) + ' mmHg). ' : ''}`;
                metrologicalText = "PROTOCOLO: Comprobar pinza del pulsioxímetro y estanqueidad del manguito de tensión. Descartar artefactos mecánicos.";
            } else if (spo2 < 95.0 || hr > 100.0 || temp >= 37.5 || sys > 130.0 || dia > 85.0 || sys < 100.0 || dia < 60.0) {
                severity = "warning";
                status = "ADVERTENCIA MODERADA";
                titleText = "Deriva Fisiológica Leve";
                descText = `Descompensación hemodinámica leve: Presión en ${sys.toFixed(0)}/${dia.toFixed(0)} mmHg con pulso de ${hr.toFixed(0)} lpm. Las constantes vitales rozan límites clínicos.`;
                metrologicalText = "Sugerencia: Monitorizar al paciente de forma activa en cama. Evitar esfuerzos musculares reactivos.";
            }
        }
    }
    
    // ==========================================
    // 2. GASOMETRÍA ARTERIAL (i-STAT Alinity)
    // ==========================================
    else if (activeDevice === "istat-gas") {
        const ph = vals["11557-6"];
        const pco2 = vals["2019-8"];
        const po2 = vals["2703-7"];
        const lac = vals["2524-7"];

        if (ph !== undefined && lac !== undefined) {
            if (ph < 7.25 || lac >= 4.0) {
                severity = "critical";
                status = "ACIDOSIS SEVERA / CRÍTICA";
                titleText = "Acidosis Láctica Aguda";
                descText = `Desequilibrio Ácido-Base Crítico: pH arterial en ${ph.toFixed(2)} con Lactato elevado en ${lac.toFixed(1)} mmol/L. Sospecha de shock séptico o hipoperfusión tisular.`;
                metrologicalText = "PROTOCOLO: Verificar calibración de dos puntos del cartucho i-STAT. Descartar burbujas de aire en la jeringa arterial.";
            } else if (ph > 7.55 || pco2 < 28.0) {
                severity = "critical";
                status = "ALCALOSIS CRÍTICA";
                titleText = "Alcalosis Respiratoria Descompensada";
                descText = `Deriva de Gases: pH elevado en ${ph.toFixed(2)} por hiperventilación pulmonar severa (pCO₂: ${pco2.toFixed(1)} mmHg).`;
                metrologicalText = "Sugerencia: Repetir muestra de gases en 15 minutos utilizando un nuevo cartucho desechable de calibración húmeda.";
            } else if (ph < 7.35 || lac >= 2.0) {
                severity = "warning";
                status = "ADVERTENCIA METABÓLICA";
                titleText = "Acidemia Compensada Leve";
                descText = `Desviación basal: pH en ${ph.toFixed(2)} con acumulación metabólica de Lactato (${lac.toFixed(1)} mmol/L).`;
                metrologicalText = "Sugerencia: Mantener control e inspeccionar posibles fugas térmicas en el analizador de gases.";
            }
        }
    }

    // ==========================================
    // 3. GLUCÓMETRO METABÓLICO (Accu-Chek)
    // ==========================================
    else if (activeDevice === "accu-chek") {
        const glu = vals["2339-0"];
        const ket = vals["3167-4"];

        if (glu !== undefined && ket !== undefined) {
            if (glu >= 250.0 && ket >= 1.5) {
                severity = "critical";
                status = "CRISIS DIABÉTICA (CAD)";
                titleText = "Cetoacidosis Diabética Crítica";
                descText = `Emergencia Metabólica: Glucosa extremadamente alta en ${glu.toFixed(0)} mg/dL acoplada a Cetonas elevadas en ${ket.toFixed(1)} mg/dL. Riesgo inminente de coma diabético.`;
                metrologicalText = "PROTOCOLO: Realizar inmediatamente control de calidad líquida en el glucómetro PoC. Confirmar calibración de tiras mediante chip RFID.";
            } else if (glu < 55.0) {
                severity = "critical";
                status = "SHOCK HIPOGLUCÉMICO";
                titleText = "Hipoglucemia Severa Aguda";
                descText = `Emergencia Clínica: Glucosa por debajo de límites biológicos viables (${glu.toFixed(0)} mg/dL). Pérdida de conciencia inminente.`;
                metrologicalText = "Sugerencia: Administrar glucagón/suero glucosado intravenoso. Calibrar glucómetro contra analizador central de laboratorio.";
            } else if (glu > 180.0 || ket >= 0.5) {
                severity = "warning";
                status = "ADVERTENCIA GLUCÉMICA";
                titleText = "Hiperglucemia en Progreso";
                descText = `Desviación metabólica: Glucosa elevada en ${glu.toFixed(0)} mg/dL con ligera elevación de cuerpos cetónicos.`;
                metrologicalText = "Sugerencia: Reevaluar bolo de insulina rápida. Comprobar que la tira reactiva no haya expirado o sufrido degradación por humedad.";
            }
        }
    }

    // ==========================================
    // 4. COAGULÓMETRO CARDIOVASCULAR (CoaguChek)
    // ==========================================
    else if (activeDevice === "coaguchek") {
        const pt = vals["46418-2"];
        const inr = vals["34714-6"];

        if (inr !== undefined) {
            if (inr >= 3.0) {
                severity = "critical";
                status = "HEMORRAGIA CRÍTICA";
                titleText = "Riesgo Hemorrágico Severo";
                descText = `Alerta de Coagulación: Índice INR en rango crítico (${inr.toFixed(2)}). Tiempo de protrombina prolongado a ${pt.toFixed(1)}s por sobredosis de anticoagulantes.`;
                metrologicalText = "PROTOCOLO: Administrar Vitamina K / plasma fresco congelado de urgencia. Verificar que el firmware del CoaguChek esté sintonizado.";
            } else if (inr >= 1.5) {
                severity = "warning";
                status = "ADVERTENCIA HEMOSTÁTICA";
                titleText = "Anticoagulación Moderada";
                descText = `Nivel terapéutico alterado: INR elevado en ${inr.toFixed(2)}. Vigilancia de hematomas espontáneos.`;
                metrologicalText = "Sugerencia: Sintonizar dosis de Warfarin/Sintrom. Limpiar la ranura del sensor óptico del coagulómetro.";
            }
        }
    }

    // ==========================================
    // 5. INMUNOLOGÍA DE URGENCIAS (Alere Triage)
    // ==========================================
    else if (activeDevice === "alere-triage") {
        const trop = vals["10839-9"];
        const bnp = vals["30934-4"];

        if (trop !== undefined && bnp !== undefined) {
            if (trop >= 0.5 || bnp >= 300.0) {
                severity = "critical";
                status = "INFARTO / FALLO CARDÍACO";
                titleText = "Sospecha de Síndrome Coronario Agudo (IAM)";
                descText = `Emergencia Cardiovascular: Troponina I cardíaca elevada en ${trop.toFixed(2)} ng/mL con Péptido Natriurético BNP en ${bnp.toFixed(0)} pg/mL. Necrosis miocárdica activa.`;
                metrologicalText = "PROTOCOLO: Realizar ECG de 12 derivaciones de inmediato. Preparar sala de hemodinámica. Calibrar láser del lector inmunológico Triage.";
            } else if (trop >= 0.05 || bnp >= 100.0) {
                severity = "warning";
                status = "ADVERTENCIA CARDÍACA";
                titleText = "Insuficiencia Cardíaca Congestiva";
                descText = `Desviación metabólica: Elevación moderada de BNP (${bnp.toFixed(0)} pg/mL) y Troponina limítrofe, sugiriendo sobrecarga de presión ventricular.`;
                metrologicalText = "Sugerencia: Monitorizar balance hídrico y administrar diuréticos. Limpiar lente de lectura del cartucho.";
            }
        }
    }
    
    // ==========================================
    // 6. CONTROL VIH INMUNOLÓGICO (Abbott m-PIMA)
    // ==========================================
    else if (activeDevice === "hiv-monitor") {
        const vl = vals["70241-5"];
        const cd4 = vals["24467-3"];

        if (vl !== undefined && cd4 !== undefined) {
            if (cd4 < 200.0) {
                severity = "critical";
                status = "INMUNODEFICIENCIA AGUDA (Fase SIDA)";
                titleText = "Crisis de Inmunodeficiencia Crítica";
                descText = `Alerta Inmune CDSS: Recuento de CD4 críticamente bajo en ${cd4.toFixed(0)} cél/µL con Carga Viral elevada a ${vl.toFixed(0)} copias/mL. Alto riesgo de infecciones oportunistas graves.`;
                metrologicalText = "PROTOCOLO DE URGENCIA: Iniciar profilaxis para PCP (Cotrimoxazol) y micosis. Solicitar genotipado de resistencia del virus en FHIR. Repetir conteo.";
            } else if (vl >= 20.0) {
                severity = "warning";
                status = "REBOTE DE CARGA VIRAL";
                titleText = "Fallo de Adherencia Terapéutica";
                descText = `Alerta Virológica: Replicación viral activa detectada. Carga Viral en ${vl.toFixed(0)} copias/mL. CD4 estable en ${cd4.toFixed(0)} cél/µL.`;
                metrologicalText = "Sugerencia: Entrevistar al paciente sobre apego al TAR (antirretrovirales). Programar carga viral de control en 4 semanas.";
            } else {
                severity = "low";
                status = "INDETECTABLE = INTRANSMISIBLE (I=I)";
                titleText = "Control Virológico Exitoso";
                descText = `Adherencia Excelente: Carga viral indetectable (< 20 copias/mL) y CD4 robusto en ${cd4.toFixed(0)} cél/µL. La transmisión sexual del virus es biológicamente imposible (U=U).`;
                metrologicalText = "Acción sugerida: Continuar pauta antirretroviral estándar. Excelente respuesta del Servicio Vasco de Salud.";
            }
        }
    }

    // ==========================================
    // APLICACIÓN VISUAL DE ALARMAS DE TRIAGE
    // ==========================================
    if (severity === "critical") {
        card.classList.add("glow-red");
        tag.textContent = status;
        tag.className = "text-xs font-mono px-2 py-0.5 rounded bg-red-950 text-red-400 font-bold border border-red-500/30 animate-pulse";
        
        title.className = "text-md font-bold text-red-500 font-title";
        title.textContent = titleText;
        
        desc.textContent = descText;
        
        icon.innerHTML = `
            <svg class="w-8 h-8 text-red-500 animate-bounce" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
        `;
        
        action.className = "mt-4 p-3 bg-red-950/30 border border-red-500/20 rounded-xl text-[10px] text-red-300 font-semibold flex items-center gap-2";
        action.innerHTML = `<svg class="w-3.5 h-3.5 text-red-400 flex-shrink-0 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/></svg> <span>${metrologicalText}</span>`;
    } else if (severity === "warning") {
        card.classList.add("glow-yellow");
        tag.textContent = status;
        tag.className = "text-xs font-mono px-2 py-0.5 rounded bg-yellow-950 text-yellow-400 font-semibold border border-yellow-500/30";
        
        title.className = "text-md font-bold text-yellow-500 font-title";
        title.textContent = titleText;
        
        desc.textContent = descText;
        
        icon.innerHTML = `
            <svg class="w-8 h-8 text-yellow-400 animate-pulse" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
        `;
        
        action.className = "mt-4 p-3 bg-yellow-950/30 border border-yellow-500/20 rounded-xl text-[10px] text-yellow-300 font-medium flex items-center gap-2";
        action.innerHTML = `<svg class="w-3.5 h-3.5 text-yellow-400 flex-shrink-0 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> <span>${metrologicalText}</span>`;
    } else {
        card.classList.add("glow-green");
        tag.textContent = status;
        tag.className = "text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 font-medium border border-emerald-500/30";
        
        title.className = "text-md font-bold text-emerald-400 font-title";
        title.textContent = titleText;
        
        desc.textContent = descText;
        
        icon.innerHTML = `
            <svg class="w-8 h-8 text-emerald-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        `;
        
        action.className = "mt-4 p-3 bg-emerald-950/20 border border-emerald-500/10 rounded-xl text-[10px] text-emerald-400/80 flex items-center gap-2";
        action.innerHTML = `<svg class="w-3.5 h-3.5 text-emerald-400 flex-shrink-0 inline" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v8M8 12h8"/></svg> <span>${metrologicalText}</span>`;
    }
}
