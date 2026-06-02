# 🫀 Simulazio Biomedikoa eta Seinaleen Prozesamendu Digitala (DSP)

Dokumentu honek BiosenseLink-ek maila klinikoko Point-of-Care (PoC) monitore bat simulatzeko denbora errealean exekutatzen duen elektrofisiologia-motorraren eta iragazki digitalaren oinarri matematikoak eta ingeniaritza aurkezten ditu.

---

## 1. EKG Simulazio Dinamikoa (McSharry Eredua)

Aurrez grabatutako fitxategi estatikoak erreproduzitzeko muga gainditzeko, BiosenseLink-ek bihotzeko jarduera elektrikoa modu dinamikoan sortzen du ("zuzenean"), McSharry et al. egileek proposatutako eredu matematiko aurreratua erabiliz (IEEE Transactions on Biomedical Engineering, 2003).

### 1.1. Bektoreen Sorkuntza Begizta (Bektorekardiograma 3D)

`ecg_simulator.py` script-ak hiru ekuazio diferentzial arruntez (ODE) osatutako sistema akoplatu bat erabiltzen du, bihotzaren bektore dipolo elektrikoaren (VCG: $x, y, z$) hiru dimentsioko ibilbidea simulatzeko.

EKGren morfologia (P, Q, R, S, T uhinak) atraktorea 3D egoera-espazio batean muga-ziklo baterantz bultzatuz modelatzen da, non uhin bakoitza parametrizatutako funtzio Gaussiartarren bidez matematikoki definitzen den:
*   $\theta_i$: Uhinaren angelua.
*   $a_i$: Uhinaren anplitudea.
*   $b_i$: Uhinaren zabalera.

**Oinarrizko Ekuazioak:**
$$ \dot{x} = \alpha x - \omega y $$
$$ \dot{y} = \alpha y + \omega x $$
$$ \dot{z} = -\sum a_i \cdot \Delta \theta_i \cdot e^{-\frac{\Delta \theta_i^2}{2b_i^2}} - (z - z_0) $$

### 1.2. 12 Bideetarako Proiekzio Espaziala (Dower Matrizea)

Lortutako hiru dimentsioko dipoloa (VCG) giza enborraren azalean proiektatzen da **Dower-en Transformatu Alderantzikatuaren** bidez. Horri esker, kardiologoek erabiltzen dituzten **12 bide estandarrak** (I, II, III, aVR, aVL, aVF, V1-V6) lor daitezke, matematikoki sortutako hiru bektore ortogonal soiletatik abiatuta.

---

## 2. Artefaktuak eta Triage Akats-Moduak Injektatzea

Simulagailuak ez ditu seinale perfektuak sortzen, errealistak baizik. Berez, script-ean bi artefaktu kliniko injektatzen dira:

1.  **Baseline Noraeza (Baseline Wander)**: Pazientearen arnasketak eragindako kaxa torazikoaren mugimendua simulatzen duen maiztasun baxuko modulazioa ($0.15 - 0.30$ Hz).
2.  **Zarata Mioelektrikoa eta Sareko Interferentziak (EMG / 50Hz)**: Maiztasun handiko zarata Gaussiarra eta sinusoidala, muskulu-uzkurdura txikiak eta sare elektriko lokaleko akoplamendu elektromagnetikoa simulatuz.

### 2.1 Eszenatoki Klinikoak (Parametroen Aldaketa)

Simulagailuak ODE-en atraktoreak berehala aldatzeko aukera ematen du, patologiak induzitzeko:
*   **Takikardia Bentrikularra (TV)**: QRS-aren anplitudea masiboki aldatuz eta taupada arteko denbora kolapsatuz.
*   **Iskemia Miokardikoa (STEMI)**: ST segmentuaren (birkargatze goiztiarraren fasea) tentsio asimetrikoa handituz bide prekordialetan.
*   **Fibrilazio Aurikularra (FA)**: Bihotz-maiztasuna zorizkatuz (banaketa bimodala) eta P uhinaren anplitudea kenduz.

---

## 3. Seinaleen Prozesamendu Digitala (DSP) - `signal_processor.py`

IA-k eta frontend-ak seinale gordina zaratarekin nahastuta jasotzen dutenez, Gateway-ak seinalea egokitu behar du `scipy.signal` erabiliz.

### 3.1. Fase Zeroko Butterworth Iragazkia
Fase-distortsioa ekiditeko (PR edo QT tarteen irakurketa klinikoki alda baitezake), aurrera eta atzeranzko iragazketa metodoa erabiltzen da (`scipy.signal.filtfilt`).

**Iragazketa Klinikoaren Pipelinea:**
1.  **Goi-Paseko Iragazkia (High-pass) 0.5 Hz-etan:** Arnasketaren baseline noraeza kentzen du, ST segmentua osorik mantenduz.
2.  **Behe-Paseko Iragazkia (Low-pass) 40 Hz-etan:** Zarata electromiografikoa mozten du. (Ohiko jarraipen klinikorako AHAren araudiaren arabera).
3.  **Notch Iragazkia (Banda Errefusatzea) 50 Hz-etan:** Europako sare elektrikoaren interferentzia harmonikoa ezabatzen du. (Kalitate Faktorea $Q = 30$).

```python
from scipy.signal import butter, filtfilt, iirnotch

def pipeline_clinical_standard(signal, fs=500):
    # 1. Banda-Paseko Iragazkia (0.5 - 40 Hz)
    nyq = 0.5 * fs
    b, a = butter(4, [0.5 / nyq, 40.0 / nyq], btype='band')
    sig_band = filtfilt(b, a, signal)
    
    # 2. Notch Iragazkia (50 Hz)
    b_n, a_n = iirnotch(50.0, 30.0, fs)
    sig_clean = filtfilt(b_n, a_n, sig_band)
    
    return sig_clean
```

### 3.2. Ezaugarrien Erauzketa (Delineazioa)
Seinalea garbitu ondoren, `pqrst_analyzer.py` script-ak Wavelet Jarraituak (CWT) eta **Pan-Tompkins algoritmo aldatua** erabiltzen ditu `NeuroKit2`-ren bidez uhin bakoitzaren hasiera- eta amaiera-puntu metrikoak markatzeko. Honek CDSS-ari milisegundotan kronometratutako tarteak ematen dizkio fidagarritasun geometriko handiz.
