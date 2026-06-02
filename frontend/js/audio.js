/**
 * CLINICAL AUDIO ENGINE (IEC 60601-1-8 Compliance)
 * Sintetizador acústico de alarmas médicas y tonos de monitorización fisiológica.
 * Desarrollado con Web Audio API pura de alto rendimiento sin archivos wav/mp3 de apoyo.
 */
class ClinicalAudioEngine {
    constructor() {
        this.ctx = null;
        this.muted = true; // Por defecto silenciado por restricciones de navegador
        this.flatlineOsc = null;
        this.flatlineGain = null;
        this.criticalInterval = null;
    }

    init() {
        if (!this.ctx) {
            this.ctx = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    setMute(state) {
        this.muted = state;
        if (state) {
            this.stopFlatline();
            this.stopCritical();
        }
    }

    playHeartbeat(frequency = 550) {
        if (this.muted) return;
        this.init();
        
        try {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            
            osc.frequency.setValueAtTime(frequency, this.ctx.currentTime);
            
            // Envolvente de volumen tipo pulso clínico
            gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.08);
            
            osc.start();
            osc.stop(this.ctx.currentTime + 0.09);
        } catch (e) {}
    }

    startFlatline() {
        if (this.muted) return;
        this.init();
        if (this.flatlineOsc) return;

        try {
            this.flatlineOsc = this.ctx.createOscillator();
            this.flatlineGain = this.ctx.createGain();
            
            this.flatlineOsc.connect(this.flatlineGain);
            this.flatlineGain.connect(this.ctx.destination);
            
            this.flatlineOsc.frequency.setValueAtTime(1000, this.ctx.currentTime);
            this.flatlineGain.gain.setValueAtTime(0.06, this.ctx.currentTime);
            
            this.flatlineOsc.start();
        } catch (e) {}
    }

    stopFlatline() {
        if (this.flatlineOsc) {
            try {
                this.flatlineOsc.stop();
            } catch (e) {}
            this.flatlineOsc = null;
            this.flatlineGain = null;
        }
    }

    startCriticalAlarm() {
        if (this.muted) return;
        this.init();
        if (this.criticalInterval) return;

        // Estándar IEC 60601-1-8 alta prioridad: 5 pulsos en ráfaga rápida
        this.criticalInterval = setInterval(() => {
            if (this.muted) {
                this.stopCritical();
                return;
            }
            const times = [0, 0.15, 0.30, 0.55, 0.70];
            times.forEach(t => {
                setTimeout(() => {
                    if (this.muted || !this.criticalInterval) return;
                    try {
                        const osc = this.ctx.createOscillator();
                        const gain = this.ctx.createGain();
                        osc.connect(gain);
                        gain.connect(this.ctx.destination);
                        osc.frequency.setValueAtTime(980, this.ctx.currentTime);
                        gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.1);
                        osc.start();
                        osc.stop(this.ctx.currentTime + 0.12);
                    } catch (e) {}
                }, t * 1000);
            });
        }, 2500);
    }

    stopCritical() {
        if (this.criticalInterval) {
            clearInterval(this.criticalInterval);
            this.criticalInterval = null;
        }
    }
}
