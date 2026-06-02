# 🔗 Elkarreragingarritasun Klinikoa (HL7 FHIR R4) eta Telemetria Asinkronoa

Telemedikuntza modernoaren erronka handiena ez da bioseinaleak neurtzea soilik, estandarizatzea baizik. BiosenseLink-ek erronka honi aurre egiten dio nazioarteko **HL7 FHIR R4** estandarra modu natiboan integratuz behaketa biomediko guztiak eta txosten diagnostikoak transmititu eta biltegiratzeko.

---

## 1. Zerbitzari Klinikoa: HAPI FHIR

Plataformak epe luzeko biltegiratzea eta balioztatze semantikoaren logika **HAPI FHIR** zerbitzari dedikatu baten esku uzten du (Javan oinarritua), zeina `8080` atakan Docker edukiontzian exekutatzen den.

**Arkitektura Abantailak:**
*   **Desakoplamendua:** BiosenseLink "Edge Gailu" gisa aritzen da, egoera iraunkorrik gabe; historia klinikoa HAPI FHIR-en esku uzten du.
*   **Agnostizismoa:** Edozein ospitale-sistemek (adibidez, Osabide Globalak) HAPI FHIR zerbitzariari galdera egin diezaioke Python, Java edo .NET erabiltzen duen kontuan izan gabe.

---

## 2. Telemetria Injekzio Asinkronoa (Background Tasks)

`run_simulation_lab.ps1` bezalako kanpoko scriptak behar izan beharrean, BiosenseLink-eko orkestratzaile nagusiak (`server.py`) Atzeko Zeregin Asinkrono bat (`asyncio.create_task`) muntatzen du FastAPI-ko `@app.on_event("startup")` apaintzailea erabiliz.

Zeregin honek etenik gabeko "deabru" (Daemon) gisa funtzionatzen du, biosentsoreen zikloetako transmisioak simulatuz (Adib. Welch Allyn Connex).

**Begizta Asinkronoaren Fluxua:**
1.  `N` segundo itxaroten du (egoera globalean definitutako telemetria maiztasuna).
2.  Zarata aleatorioa sortzen du egungo triage-aren konstante bizigarrien gainean (Adibidez, triage-a FA bada, bihotz-maiztasuna bortizki aldatuko da 110 eta 160 taupada minutuko artean).
3.  FHIR-en `Observation` eskemarekin bateragarria den JSON payload bat sortzen du.
4.  HTTP POST eskaera asinkrono bat (`httpx` edo `aiohttp` / `urllib`) egiten du `http://localhost:8080/fhir/Observation` endpoint-era.

---

## 3. Mapaketa Semantikoa (LOINC eta SNOMED CT)

Datuak balio mediko erreala izateko, ez da nahikoa zenbaki gordinak bidaltzea. Ezagutza biomedikoko ontologia kontrolatuen bidez etiketatu behar dira `fhir_exporter.py` scriptean.

### 3.1. LOINC Hiztegia (Logical Observation Identifiers Names and Codes)
Neurketak eta laborategiko emaitzak kodetzeko erabiltzen da.
*   **Bihotz Maiztasuna**: `8867-4`
*   **Oxigeno Saturazioa (SpO2)**: `2708-6`
*   **Presio Arterial Sistolikoa**: `8480-6`
*   **Presio Arterial Diastolikoa**: `8462-4`
*   **Gorputzeko Tenperatura**: `8310-5`

### 3.2. SNOMED CT Hiztegia (Systematized Nomenclature of Medicine)
CDSS agenteak (Ollama) erabiltzen du EKGaren analisi matematikoaren ondoren ateratako diagnostikoak kodetzeko.
*   **Erritmo Sinusal Normala**: `74864009`
*   **Fibrilazio Aurikularra**: `49436004`
*   **Takikardia Bentrikularra**: `253889003`
*   **Iskemia Akutua (STEMI)**: `401303003`
*   **Bihotz Geldialdia (Asistolia)**: `410429000`

---

## 4. FHIR Baliabideen Egitura (JSON)

BiosenseLink-ek bi baliabide primario mota sortzen ditu: `Observation` eta `DiagnosticReport`.

### `Observation` Baliabidearen Adibidea (Bihotz Maiztasuna):
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "8867-4",
      "display": "Heart rate"
    }]
  },
  "subject": {
    "reference": "Patient/biosenselink-001"
  },
  "valueQuantity": {
    "value": 75.0,
    "unit": "beats/minute",
    "system": "http://unitsofmeasure.org",
    "code": "/min"
  }
}
```

### `DiagnosticReport` Baliabidearen Adibidea (Iak Sortutako CDSS):
```json
{
  "resourceType": "DiagnosticReport",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11524-6",
      "display": "EKG Study"
    }]
  },
  "conclusion": "Pazienteak Fibrilazio Aurikularra aurkezten du erantzun bentrikular azkarrarekin. P uhinen ausentzia eta R-R irregularra.",
  "conclusionCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "49436004",
      "display": "Atrial Fibrillation"
    }]
  }]
}
```

---

## 5. Mahaigaineko Bezeroaren Esportazio Botoia ("HL7 FHIRra esportatu")

Mahaigaineko bezeroan (`main.py`) **"HL7 FHIRra esportatu"** botoiak elkarreragingarritasun kliniko estandarizatuko fluxu asinkrono bat abiarazten du klik bakoitzarekin.

### 5.1. Exekuzio-fluxu Teknikoa
Botoian sakatzean, `on_export_fhir(event)` atzera-dei (callback) funtzioak urrats hauek betetzen ditu:
1. **Datu Kuantitatibo eta Kualitatiboak Irakurtzea:** Aplikazioaren egoera globaletik (`state`) uneko EKG seinalearen parametro kalkulatuak (`ECGAnalysisReport`) eta CDSS moduluko diagnostiko diferentziala eskuratzen ditu.
2. **FHIR R4 Egituraketa:** `fhir_exporter.py` moduluko `export_to_fhir_bundle` funtzioari deitzen dio. Funtzio honek `fhir.resources` liburutegia erabiliz balioztatutako FHIR pakete kliniko bat eraikitzen du.
3. **JSON Iraunkortasuna:** Sortutako paketea (Bundle) `data/fhir_report.json` helbide lokalean idazten du UTF-8 kodeketan.
4. **Erabiltzailearekiko Interakzio Asinkronoa:** Botoiaren jatorrizko kolorea berdera (`#2ecc71`) aldatzen da eta etiketa **"Esportatuta!"** jartzen du. Hari asinkrono bat (`threading.Thread`) abiarazten da UI blokeatu gabe 1.5 segundo itxaroteko, eta ondoren botoia jatorrizko egoerara eta etiketara leheneratzen du.

### 5.2. Mapatutako Baliabide Klinikoak eta Egitura Semantikoa
Sortzen den `Bundle` (mota: `collection`) baliabideak egitura profesional honi jarraitzen dio:
*   **Pazientea (`Patient`):** UUID unibertsal batekin simulaturiko paziente profila.
*   **Behaketak (`Observation`):** EKG azterketaren parametro gakoak LOINC kode ofizialekin lotzen dira:
    *   *Bihotz-maiztasuna (Heart Rate):* LOINC `8867-4` (unitatea: `/min`)
    *   *PR tartea (PR Interval):* LOINC `46087-3` (unitatea: `ms`)
    *   *QRS iraupena (QRS Duration):* LOINC `46088-1` (unitatea: `ms`)
    *   *QTc tartea (QTc Interval):* LOINC `8636-4` (unitatea: `ms`)
*   **Diagnostiko-txostena (`DiagnosticReport`):** EKG azterketa osoa (LOINC `11524-6`) biltzen du, aurreko `Observation` baliabideak erreferentziatuz eta CDSS diagnostiko klinikoaren ondorioak gehituz (adibidez, *STEMI*, *Fibrilazio Aurikularra*, etab. **SNOMED CT** terminologiarekin).

### 5.3. IoMT Edge Pasabidearen Garrantzia
Funtzio honek BiosenseLink **Edge Pasabide** adimendun gisa finkatzen du. Seinale fisiko gordinak eta diagnostiko diferentzial konplexuak nazioarteko komunikazio mediko estandarretara bihurtzen ditu, edozein ospitaletako kudeaketa-sistemek (EHR) inolako adaptazio-geruzarik gabe interpretatu ditzaten.

---

## 6. Zergatik EKG Seinale Gordinak ez duten FHIR ID Independenterik (Arkitektura Klinikoa)

Arlo biomedikoan eta informatika medikoan ohikoa den galdera bat da zergatik gailu mugikorren neurketek (adib. bihotz-maiztasunak) FHIR ID espezifiko bat duten, eta EKG uhin gordinaren balio instantaneoek ez. Hau HL7 FHIR estandarraren egitura-diseinuari eta eraginkortasun klinikoari dagokio.

### 6.1. Datu-bolumena eta Sare-kolapsoa (DDoS Klinikoa)
EKG uhinak maiztasun altuko seinale jarraituak dira (gure kasuan, 500 Hz-koak, hots, 500 puntu segundoko 12 bide bakoitzeko).
* Segundoko jasotzen diren **6.000 lagin tenporal** horietako bakoitza FHIR zerbitzarira HTTP POST bidez `Observation` independente gisa igotzen saiatuko bagina, ospitaleko datu-basea eta sarea berehala kolapsatuko lirateke.

### 6.2. Nola kudeatzen ditu FHIR R4-k Seinale Jarraituak?
HL7 FHIR estandarrak bioseinaleak prozesatzeko egitura espezifikoak definitzen ditu, lagin gordinak isolatuta bidali beharrean:
* **`SampledData` Datu-Mota:** FHIR-ek `Observation` baliabidean `valueSampledData` eremua definitzen du. Honek seinale jarraitu oso bat espazio bidez banatutako kate bakar batean biltzen du (adibidez: `"0.470 -0.170 -0.307..."`), maiztasuna (500 Hz), eskala eta jatorri-puntuak adieraziz. Uhin guztiak **baliabide bakarrean** paketatzen dira.
* **`DiagnosticReport` Txostena (BiosenseLink Erabilera):** EKG azterketa oso bat ekintza kliniko bakar gisa ulertzen da. Horregatik:
  1. Bihotz-maiztasuna edo SpO2 bezalako konstanteak **balio diskretuak eta independenteak** dira, eta horregatik bakoitzak bere `Observation` eta bere **FHIR IDa** jasotzen du ziklo bakoitzean.
  2. Terminalaren beheko aldean ikusten diren voltajeen probeak telemetria pasabidearen funtzionamendu egokia monitorizatzeko tresna soil bat dira.
  3. 10 segundoko 12 bideko seinale osoa eta CDSSren ondorio adimendunak **txosten bakar batean (`DiagnosticReport`)** bidaltzen dira **"HL7 FHIRra esportatu"** botoia sakatzean. Une horretan, azterketa kardiologiko osoak bere FHIR ID propioa jasotzen du ospitaleko HKE zerbitzarian.


