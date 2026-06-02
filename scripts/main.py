"""
==============================================================================
BiosenseLink - Interfaz de Visualizacion Interactiva de ECG 12 Derivaciones
==============================================================================
Orquestador principal del sistema BiosenseLink. Genera una interfaz grafica
interactiva mediante Matplotlib que permite al usuario:

  1. Seleccionar entre 6 escenarios clinicos de 12 derivaciones (STEMI, FA, etc.).
  2. Seleccionar Modos de Visualizacion (12x1 Apilado o 4x3+1 Clinico).
  3. Aplicar filtros en tiempo real.
  4. Consultar el informe clinico automatizado.
  5. Alternar de idioma en caliente entre Español y Euskara.

Autor: Ander Urien Telleria (BiosenseLink Project)
==============================================================================
"""

import sys
import os
import numpy as np
import pandas as pd
import matplotlib
from datetime import datetime
import threading
import time
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons, Button
import matplotlib.gridspec as gridspec

# Modulos locales
from ecg_simulator import SCENARIOS
from signal_processor import FILTERS, pipeline_clinical_standard
from pqrst_analyzer import analyze_ecg

# ---------------------------------------------------------------------------
# Configuracion global
# ---------------------------------------------------------------------------
SAMPLING_RATE = 500    # Hz
DURATION      = 10     # Segundos

# Diccionario de Internacionalización (i18n) para la UI nativa
TRANSLATIONS = {
    "es": {
        "view_lbl": "MODO VISUALIZACION",
        "scen_lbl": "ESCENARIO CLINICO",
        "filt_lbl": "FILTRO DIGITAL",
        "lang_lbl": "IDIOMA / HIZKUNTZA",
        "btn_fhir": "Exportar a HL7 FHIR",
        "btn_fhir_done": "¡Exportado!",
        "time_lbl": "Tiempo (s)",
        "rhythm_strip": "Tira de Ritmo",
        "report_title": "Hallazgos Clinicos CDSS (Topologia 12 Leads)",
        "report_empty": "No se detectaron anomalias en los parametros basicos.",
        "report_err": "Error en analisis CDSS: ",
        "title_stacked": "ECG 12 Derivaciones (Apilado) - ",
        "title_grid": "ECG 12 Derivaciones (4x3+1 Grid) - "
    },
    "eu": {
        "view_lbl": "IKUSTE MODOA",
        "scen_lbl": "ESZENATOKI KLINIKOA",
        "filt_lbl": "IRAGAZKI DIGITALA",
        "lang_lbl": "IDIOMA / HIZKUNTZA",
        "btn_fhir": "HL7 FHIRra esportatu",
        "btn_fhir_done": "Esportatuta!",
        "time_lbl": "Denbora (s)",
        "rhythm_strip": "Erritmo banda",
        "report_title": "CDSS Aurkikuntza Klinikoak (12 Bideko Topologia)",
        "report_empty": "Ez da anomalirik detektatu oinarrizko parametroetan.",
        "report_err": "Errorea CDSS analisian: ",
        "title_stacked": "EKG 12 Bide (Pilatua) - ",
        "title_grid": "EKG 12 Bide (4x3+1 Sarea) - "
    }
}


def main():
    print("=" * 60)
    print("  BiosenseLink - Gateway IoMT Inteligente (12-Lead)")
    print("=" * 60)

    # Estado de la app (incluye idioma)
    state = {
        "current_scenario": "normal",
        "current_filter": "clinical",
        "current_view": "4x3+1 Grid Clinico",
        "lang": "es",
        "time": None,
        "raw_ecg": None,      # DataFrame
        "filtered_ecg": None, # DataFrame
        "current_report": None
    }

    _update_signal(state)

    fig = plt.figure(figsize=(18, 11), facecolor="#0a0a1a", num="BiosenseLink - 12-Lead ECG Analyzer")
    fig.subplots_adjust(left=0.04, right=0.76, top=0.92, bottom=0.06, hspace=0.3)
    gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1.5], figure=fig)

    # --- Panel 1: Visualizacion ECG ---
    ax_ecg = fig.add_subplot(gs[0])
    ax_ecg.set_facecolor("#0d1117")
    ax_ecg.tick_params(colors="#888888")
    for spine in ax_ecg.spines.values():
        spine.set_color("#333333")

    # --- Panel 2: Informe clinico ---
    ax_report = fig.add_subplot(gs[1])
    ax_report.set_facecolor("#0d1117")
    ax_report.axis("off")
    
    # Titulo de reporte dinámico
    report_title = ax_report.set_title(TRANSLATIONS["es"]["report_title"], color="#e6e6e6", fontsize=11, fontweight="bold", pad=10)
    report_text = ax_report.text(0.02, 0.95, "", transform=ax_report.transAxes, fontsize=8.5, color="#e6e6e6", family="monospace", va="top")

    # ------------------------------------------------------------------
    # Panel lateral: Controles
    # ------------------------------------------------------------------
    # --- Vista ---
    ax_view_lbl = fig.add_axes([0.78, 0.88, 0.20, 0.03])
    ax_view_lbl.set_facecolor("#0a0a1a"); ax_view_lbl.axis("off")
    view_title_text = ax_view_lbl.text(0.5, 0.5, "MODO VISUALIZACION", transform=ax_view_lbl.transAxes, ha="center", va="center", color="#feca57", fontweight="bold")
    
    ax_view = fig.add_axes([0.78, 0.77, 0.20, 0.10])
    ax_view.set_facecolor("#1a1a2e")
    view_opts = ["4x3+1 Grid Clinico", "12x1 Apilado"]
    radio_view = RadioButtons(ax_view, view_opts, active=0, radio_props={"facecolor": ["#1a1a2e"]*2, "edgecolor": ["#feca57"]*2}, label_props={"color": ["#e6e6e6"]*2, "fontsize": [8.5]*2})

    # --- Escenario ---
    ax_scen_lbl = fig.add_axes([0.78, 0.72, 0.20, 0.03])
    ax_scen_lbl.set_facecolor("#0a0a1a"); ax_scen_lbl.axis("off")
    scen_title_text = ax_scen_lbl.text(0.5, 0.5, "ESCENARIO CLINICO", transform=ax_scen_lbl.transAxes, ha="center", va="center", color="#4ecdc4", fontweight="bold")
    
    ax_scen = fig.add_axes([0.78, 0.44, 0.20, 0.27])
    ax_scen.set_facecolor("#1a1a2e")
    scenario_labels = [SCENARIOS[k][0] for k in SCENARIOS]
    radio_scen = RadioButtons(ax_scen, scenario_labels, active=list(SCENARIOS.keys()).index("normal"), radio_props={"facecolor": ["#1a1a2e"]*len(SCENARIOS), "edgecolor": ["#4ecdc4"]*len(SCENARIOS)}, label_props={"fontsize": [8]*len(SCENARIOS), "color": ["#e6e6e6"]*len(SCENARIOS)})

    # --- Filtro ---
    ax_filt_lbl = fig.add_axes([0.78, 0.39, 0.20, 0.03])
    ax_filt_lbl.set_facecolor("#0a0a1a"); ax_filt_lbl.axis("off")
    filt_title_text = ax_filt_lbl.text(0.5, 0.5, "FILTRO DIGITAL", transform=ax_filt_lbl.transAxes, ha="center", va="center", color="#ff6b6b", fontweight="bold")
    
    ax_filt = fig.add_axes([0.78, 0.17, 0.20, 0.21])
    ax_filt.set_facecolor("#1a1a2e")
    filter_labels = [FILTERS[k][0] for k in FILTERS]
    radio_filt = RadioButtons(ax_filt, filter_labels, active=list(FILTERS.keys()).index("clinical"), radio_props={"facecolor": ["#1a1a2e"]*len(FILTERS), "edgecolor": ["#ff6b6b"]*len(FILTERS)}, label_props={"fontsize": [8]*len(FILTERS), "color": ["#e6e6e6"]*len(FILTERS)})

    # --- Idioma / Hizkuntza ---
    ax_lang_lbl = fig.add_axes([0.78, 0.13, 0.20, 0.03])
    ax_lang_lbl.set_facecolor("#0a0a1a"); ax_lang_lbl.axis("off")
    lang_title_text = ax_lang_lbl.text(0.5, 0.5, "IDIOMA / HIZKUNTZA", transform=ax_lang_lbl.transAxes, ha="center", va="center", color="#a855f7", fontweight="bold", fontsize=9)
    
    ax_lang = fig.add_axes([0.78, 0.07, 0.20, 0.05])
    ax_lang.set_facecolor("#1a1a2e")
    radio_lang = RadioButtons(ax_lang, ["Castellano", "Euskara"], active=0, radio_props={"facecolor": ["#1a1a2e"]*2, "edgecolor": ["#a855f7"]*2}, label_props={"color": ["#e6e6e6"]*2, "fontsize": [8.5]*2})

    # --- Boton de Exportacion FHIR ---
    ax_btn_fhir = fig.add_axes([0.78, 0.015, 0.20, 0.045])
    btn_fhir = Button(ax_btn_fhir, 'Exportar a HL7 FHIR', color="#1a1a2e", hovercolor="#2a2a4e")
    btn_fhir.label.set_color("#4ecdc4")
    btn_fhir.label.set_fontweight("bold")
    btn_fhir.label.set_fontsize(9)

    def update_plots():
        t = state["time"]
        df_raw = state["raw_ecg"]
        lang_key = state["lang"]
        tr = TRANSLATIONS[lang_key]
        
        # Filtro
        filter_key = state["current_filter"]
        filter_func = FILTERS[filter_key][1]
        df_filt = filter_func(df_raw, SAMPLING_RATE)
        state["filtered_ecg"] = df_filt

        ax_ecg.clear()
        ax_ecg.set_facecolor("#0d1117")
        ax_ecg.grid(True, alpha=0.15, color="#333333")
        
        view_mode = state["current_view"]
        
        if view_mode == "12x1 Apilado":
            _plot_12x1(ax_ecg, t, df_filt, lang_key)
            ax_ecg.set_title(f"{tr['title_stacked']}{SCENARIOS[state['current_scenario']][0]}", color="#e6e6e6", fontsize=12)
        else:
            _plot_4x3_grid(ax_ecg, t, df_filt, lang_key)
            ax_ecg.set_title(f"{tr['title_grid']}{SCENARIOS[state['current_scenario']][0]}", color="#e6e6e6", fontsize=12)

        # Analisis
        try:
            report = analyze_ecg(df_filt, sampling_rate=SAMPLING_RATE)
            state["current_report"] = report
            report_lines = _format_report(report, lang_key)
            report_text.set_text(report_lines)
        except Exception as e:
            report_text.set_text(f"{tr['report_err']}{str(e)}")

        fig.canvas.draw_idle()


    def on_view(lbl):
        state["current_view"] = lbl
        update_plots()

    def on_scen(lbl):
        for k, (n, _) in SCENARIOS.items():
            if n == lbl:
                state["current_scenario"] = k
                _update_signal(state)
                update_plots()
                break

    def on_filt(lbl):
        for k, (n, _) in FILTERS.items():
            if n == lbl:
                state["current_filter"] = k
                update_plots()
                break

    def on_lang(lbl):
        lang_key = "es" if lbl == "Castellano" else "eu"
        state["lang"] = lang_key
        tr = TRANSLATIONS[lang_key]
        
        # Traducir los headers y textos en caliente
        view_title_text.set_text(tr["view_lbl"])
        scen_title_text.set_text(tr["scen_lbl"])
        filt_title_text.set_text(tr["filt_lbl"])
        lang_title_text.set_text(tr["lang_lbl"])
        report_title.set_text(tr["report_title"])
        btn_fhir.label.set_text(tr["btn_fhir"])
        
        # Forzar repintado de gráficas con nuevos textos
        update_plots()

    def on_export_fhir(event):
        lang_key = state["lang"]
        tr = TRANSLATIONS[lang_key]
        try:
            from fhir_exporter import export_to_fhir_bundle
            
            report = state.get("current_report")
            if not report:
                print("No hay reporte para exportar.")
                return
                
            # Simulamos respuesta del CDSS basada en los hallazgos
            fake_cdss = {
                "differential_diagnosis": [{"condition": f.interpretation, "probability": "HIGH"} for f in report.findings if f.severity in ["CRITICO", "ALERTA"]],
                "reasoning_chain": "Analisis topografico automatizado basado en matrices ECG-12."
            }
            if not fake_cdss["differential_diagnosis"]:
                fake_cdss["differential_diagnosis"].append({"condition": "Normal Sinus Rhythm", "probability": "HIGH"})
                
            fhir_json = export_to_fhir_bundle(report, fake_cdss)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            out_path = os.path.join(data_dir, "fhir_report.json")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(fhir_json)
                
            print(f"[{datetime.now().strftime('%H:%M:%S')}] EXPORTACION EXITOSA: Bundle HL7 FHIR R4 guardado en {out_path}")
            
            # Cambiar color del boton temporalmente para feedback visual
            original_color = btn_fhir.color
            btn_fhir.color = "#2ecc71"
            btn_fhir.label.set_text(tr["btn_fhir_done"])
            fig.canvas.draw_idle()
            
            # Reset color
            def reset_btn():
                time.sleep(1.5)
                btn_fhir.color = original_color
                btn_fhir.label.set_text(tr["btn_fhir"])
                fig.canvas.draw_idle()
                
            import threading
            threading.Thread(target=reset_btn).start()
            
        except Exception as e:
            print(f"Error exportando FHIR: {e}")

    radio_view.on_clicked(on_view)
    radio_scen.on_clicked(on_scen)
    radio_filt.on_clicked(on_filt)
    radio_lang.on_clicked(on_lang)
    btn_fhir.on_clicked(on_export_fhir)
    
    update_plots()
    plt.show()


# ---------------------------------------------------------------------------
# Funciones Graficas 12 Leads
# ---------------------------------------------------------------------------

def _plot_12x1(ax, t, df, lang):
    """Apila las 12 derivaciones verticalmente."""
    tr = TRANSLATIONS[lang]
    leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    offset = 2.5 # mV offset entre graficas
    
    yticks = []
    yticklabels = []
    
    for i, lead in enumerate(leads):
        y_pos = -i * offset
        sig = df[lead].values
        ax.plot(t, sig + y_pos, color="#4ecdc4", linewidth=0.8)
        
        yticks.append(y_pos)
        yticklabels.append(lead)
        
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels, color="#feca57", fontweight="bold")
    ax.set_xlim(t[0], min(4.0, t[-1])) # Muestra solo 4 seg en apilado
    ax.set_ylim(-11 * offset - 1.5, 2.0)
    ax.set_xlabel(tr["time_lbl"], color="#e6e6e6")


def _plot_4x3_grid(ax, t, df, lang):
    """Dibuja el layout clinico estandar 4 columnas x 3 filas + Rhythm Strip."""
    tr = TRANSLATIONS[lang]
    # Layout matrix (Columna por tiempo: 0-2.5s, 2.5-5s, 5-7.5s, 7.5-10s)
    grid = [
        ['I',   'aVR', 'V1', 'V4'], # Fila 1 (y=0)
        ['II',  'aVL', 'V2', 'V5'], # Fila 2 (y=-offset)
        ['III', 'aVF', 'V3', 'V6'], # Fila 3 (y=-2*offset)
    ]
    
    fs = SAMPLING_RATE
    col_width_s = 2.5
    samples_per_col = int(col_width_s * fs)
    y_offset = 3.0 # mV
    
    for row_idx, row_leads in enumerate(grid):
        for col_idx, lead in enumerate(row_leads):
            start_idx = col_idx * samples_per_col
            end_idx   = start_idx + samples_per_col
            if end_idx > len(t): continue
            
            t_seg = t[start_idx:end_idx]
            sig = df[lead].values[start_idx:end_idx]
            
            y_pos = -row_idx * y_offset
            ax.plot(t_seg, sig + y_pos, color="#4ecdc4", linewidth=0.9)
            ax.text(t_seg[0] + 0.05, y_pos + 1.0, lead, color="#feca57", fontweight="bold", fontsize=10)

    # Rhythm Strip - Derivacion II, todo el ancho (10s)
    rhythm_y = -3 * y_offset - 1.0
    ax.plot(t, df['II'].values + rhythm_y, color="#ff6b6b", linewidth=1.0)
    ax.text(0.05, rhythm_y + 1.0, f"II ({tr['rhythm_strip']})", color="#feca57", fontweight="bold", fontsize=10)
    
    # Divisiones verticales de columnas (2.5s, 5.0s, 7.5s)
    for x_div in [2.5, 5.0, 7.5]:
        ax.axvline(x=x_div, color="#333333", linestyle="--", linewidth=1)

    ax.set_yticks([])
    ax.set_xlim(0, 10.0)
    ax.set_ylim(rhythm_y - 2.0, 2.0)
    ax.set_xlabel(tr["time_lbl"], color="#e6e6e6")


def _update_signal(state):
    key = state["current_scenario"]
    _, gen = SCENARIOS[key]
    t, df = gen(duration=DURATION, sampling_rate=SAMPLING_RATE)
    state["time"] = t
    state["raw_ecg"] = df


def _format_report(report, lang) -> str:
    tr = TRANSLATIONS[lang]
    lines = []
    
    # Traducir los parámetros clave en el reporte
    hr_term = "FC" if lang == "es" else "BM" # Frecuencia Cardíaca vs Bihotz-Maiztasuna
    lines.append(f"{hr_term}: {report.mean_heart_rate:.0f} lpm | PR: {report.mean_pr_interval_ms:.0f} ms | QRS: {report.mean_qrs_duration_ms:.0f} ms | QTc: {report.mean_qtc_ms:.0f} ms")
    lines.append("-" * 80)
    
    colors = {"NORMAL": "[OK]", "ATENCION": "[!]", "ALERTA": "[!!]", "CRITICO": "[!!!]"}
    
    if not report.findings:
        lines.append(tr["report_empty"])
        return "\n".join(lines)
        
    for f in report.findings:
        icon = colors.get(f.severity, "[?]")
        
        # Mapear interpretación si está en Euskara
        interpretation = f.interpretation
        if lang == "eu":
            # Traducciones simples de patologías comunes para el visor offline
            pathology_translations = {
                "Bradicardia sinusal": "Bradikardia sinusala",
                "Taquicardia sinusal": "Takikardia sinusala",
                "Bloqueo AV de 1er grado": "1. mailako AV blokeoa",
                "Bloqueo completo de rama": "Adar-blokeo osoa",
                "Elevacion del segmento ST (STEMI)": "ST segmentuaren igoera (STEMI)",
                "Asistolia / Paro Cardiaco": "Asistolia / Bihotz gelditzea",
                "Normal": "Normala"
            }
            interpretation = pathology_translations.get(f.parameter, f.interpretation)
            
        lines.append(f"{icon} {f.parameter}: {f.value} -> {interpretation[:90]}")
        
    return "\n".join(lines)


if __name__ == "__main__":
    main()
