# ⚙️ Hedapen eta Instalazio Gida (Setup Guide)

Eskuliburu honek **BiosenseLink** ekosistema garapen-ingurune batean edo simulazio kliniko batean (Windows/Linux/Mac) abiarazteko urratsez urratseko jarraibideak ematen ditu.

---

## 1. Sistemaren Aldez Aurreko Baldintzak

Plataforma hasi aurretik, ziurtatu osagai hauek instalatuta dituzula:

1.  **Docker Desktop / Docker Engine**: PostgreSQL eta HAPI FHIR zerbitzariak birtualizatzeko beharrezkoa da. Ziurtatu Docker daemona martxan dagoela.
2.  **Python 3.10 edo berriagoa**: FastAPI Gateway-a eta DSP motorrak (SciPy/NeuroKit2) exekutatzeko beharrezkoa da.
3.  **Ollama**: Tokian instalatuta, Adimen Artifizialeko Air-Gapped inferentziarako.
4.  **PowerShell (Windows) edo Bash (Linux)**: Orkestratzailea exekutatzeko.

---

## 2. IA Motorraren Prestaketa (Ollama)

BiosenseLink-ek **DeepSeek-R1 (8B)** erabiltzen du CDSS motorrerako, pazienteen datuak ospitaleko intranetetik ez direla ateratzen bermatuz (HIPAA/GDPR araudia betetzea).

1. Ireki terminala.
2. Deskargatu oinarrizko eredua:
   ```bash
   ollama pull deepseek-r1:8b
   ```
3. Egiaztatu Ollama zerbitzaria ataka lehenetsian eskuragarri dagoela (`http://localhost:11434`).

---

## 3. Backend Dependentziak Instalatzea (Python)

Edge zerbitzariak eta algoritmo biomedikoek liburutegi matematiko espezifikoak behar dituzte.

Ireki kontsola BiosenseLink-en erroko karpetan (`C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink`) eta instalatu liburutegiak:

```bash
pip install fastapi uvicorn websockets psycopg2-binary numpy pandas scipy neurokit2 matplotlib httpx
```

---

## 4. Erabateko Hedapena (Orkestratzaile Automatikoa)

Martxan jartzea errazteko, ez dago edukiontziak edo backend-a eskuz abiarazi beharrik. Biltegiak orkestratzaile maisu bat dakar PowerShell-en.

### Windows-en (PowerShell):
Exekutatu script-a proiektuaren erroan:
```powershell
.\Lanzar_BiosenseLink.ps1
```

**Zer egiten du script honek?**
1. `HAPI FHIR` altxatzen du `8080` atakan Docker bidez.
2. `PostgreSQL` altxatzen du `5432` atakan.
3. Datu-basearen eskema eta erabiltzaileak (Dr. Ander, Enfermera Amaia) injektatzen ditu.
4. `FastAPI` (Gateway) zerbitzaria altxatzen du `8081` atakan.
5. Frontend-a (HTML5 Canvas) nabigatzailera zuzenean zerbitzatzen du.

---

## 5. Arazo Ohikoen Konponbidea (Troubleshooting)

### Arazoa: "Ez da konektatzen PostgreSQL datu-basera"
*   **Arrazoia**: Docker ez dago martxan edo `docs/postgre_pass.txt` fitxategiko pasahitzak aldatu dira eta ez datoz bat aldez aurretik instantziatutako edukiontziarekin.
*   **Bidea**: Ireki Docker Desktop, ezabatu `clinical-db` edukiontzia eta `postgres_data` bolumena, eta berrabiarazi `Lanzar_BiosenseLink.ps1` script-a fabrikako pasahitzekin birsortu dadin.

### Arazoa: "CDSS-ak gehiegi irauten du edo Timeout ematen du"
*   **Arrazoia**: Tokiko hardwarea (GPU/CPU) LLM eredua memorian mantentzeko arazoak ditu, edo Ollama ez dago abiarazita.
*   **Bidea**: Ziurtatu gutxienez 8GB RAM libre dituzula. Egiaztatu nabigatzaile batean `http://localhost:11434` atariak "Ollama is running" erantzuten duela.

### Arazoa: "Osziloskopioaren grafikoa motel edo saltoka ikusten da"
*   **Arrazoia**: Zure nabigatzaileak hardware azelerazioa desgaituta dauka HTML5 Canvas-erako.
*   **Bidea**: Joan Chrome/Edge-ren ezarpenetara (`chrome://settings/system`) eta ziurtatu "Erabili hardware azelerazioa eskuragarri dagoenean" aktibatuta dagoela.
