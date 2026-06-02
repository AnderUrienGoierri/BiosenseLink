# 💻 Frontend Kontsola eta Telemetria Web UI

BiosenseLink-ek bezero astun (Fat Clients) tradizionalen erabilera saihesten du telemedikuntzan, web arkitektura arin baten alde eginez. Nabigatzailearen teknologia estandarrak (HTML5, JavaScript ES6) erabiltzen ditu grafiko mediko konplexuak 60 FPS-tan renderizatzeko, gailuaren CPUa gainkargatu gabe.

---

## 1. Osziloskopio Medikoa (HTML5 Canvas)

Monitore elektrokardiografikoa ez da DOM liburutegi motelak erabiliz renderizatzen (ohiko Chart.js edo D3.js purua, adibidez), datuen dentsitatea oso handia baita (500 lagin segundoko). Horren ordez, **HTML5 Canvas** API gordina erabiltzen da, `ui.js` bidez kudeatuta.

### 1.1. Buffer Bikoitza eta Sareta Medikoa
*   **Hondo Estatikoa (CSS Pattern):** EKG paperaren sareta milimetratu klasikoa (5mm-ko lauki handiak, 1mm-ko txikiak) CSS eredu natibo baten bidez marrazten da (`bg-ecg-grid`). Honek JS motorrak fotograma bakoitzean lineak berriro marraztu behar izatea ekiditen du.
*   **Oihal Dinamikoa (Canvas):** JavaScript-ek Float32 array-ak jasotzen ditu WebSocket bidez eta `ctx.lineTo()` eta `ctx.stroke()` erabiltzen ditu lerro isoelektriko berdea (kolorea: `#4ecdc4`) trazatzeko, izpi katodikoen hodi (CRT) baten fosforo efektuekin (*Glow*).

### 1.2. Ekortze Marrazketa Algoritmoa (Sweep)
Mugimendu-grafikoek (scroll) ez bezala, benetako monitore medikoek ekortze bat erabiltzen dute, ezkerretik eskuinera berrabiarazten dena, seinale zaharra apurka-apurka ezabatuz ("fade" efektua edo barra beltz mugikorra). Frontend-ak logika hau inplementatzen du egungo marrazketa-indizea (`x`) jarraituz eta orratz birtualaren aurretik dagoen bloke bat (`[x, x + Δx]`) ezabatuz.

---

## 2. Telemetria Motorra (WebSocket eta REST)

Arkitekturak maiztasun handiko streaming-a eta dei transakzionalak desakoplatzen ditu.

*   **WebSocket Fluxua (`api.js`)**: Full-Duplex konexio irekia `ws://localhost:8081/ws/ecg` helbidean. Tentsio-tentsorea eta denbora-markagailua soilik transferitzen ditu. Oso arina da.
*   **REST Polling (Aukerakoa)**: Aplikazioak `GET /api/vitals` deiak egiten ditu, zeregin asinkronoak datuak WS bidez bultzatzen ez baditu, akatsen tolerantzia bermatuz.
*   **Kontrol Gertaerak**: Triage botoiek (Fibrilazio Aurikularra, Takikardia Bentrikularra) komandoak bidaltzen dituzte `POST /api/control/set_scenario` bidez, Gateway-ak berehala prozesatzen dituelarik.

---

## 3. Lokalizazio Dinamikoa Zuzenean (i18n)

Osasun ingurune elebidunetan (Osakidetza) erabilgarritasuna bermatzeko, interfazeak nazioartekotze motor bat (`i18n.js`) du, kontsola *zuzenean* itzultzen duena orria kargatu beharrik gabe.

### 3.1. i18n Arkitektura
*   **Hiztegiak Memorian**: `i18n.js` fitxategiak `es` (Espainiera) eta `eu` (Euskara) JSON objektuak gordetzen ditu.
*   **ID Bidezko Injekzioa**: Goiburuan hizkuntza aldatzean, O(n) begizta batek DOMeko IDak zeharkatzen ditu (`auth-title`, `triage-afib`, etab.), dagokion balioa injektatuz ondoan dauden SVG nodoak hautsi gabe, `changeLanguage()` funtzioari esker.
*   **Iraupena**: Erabiltzailearen hobespena `localStorage`-n gordetzen da `biosenselink_lang` gakoaren azpian.

---

## 4. Mahaigaineko Ikusgailua (Matplotlib)

Lineaz kanpoko analisi zehatza egiteko, *Mahaigaineko Ikusgailua Abiarazi* botoiak `main.py` deitzen du.

*   **Matplotlib GridSpec**: Interfaze natiboa paneletan banatzen du (Grafikoak, CDSS, Kontrolak).
*   **Multi-Lead Layout-ak**: **4x3+1 Grid** estandar amerikarra renderizatzen du (2.5 segundoko 4 denbora-zutabe, II. bidea behealdean 10 segundoko etengabeko *Rhythm Strip* gisa edukiz).
*   **Tokiko RadioButtons**: `es`/`eu` hizkuntza-aldaketa inplementatzen du, ardatzak eta txosten patologikoen itzulpenak Web interfazearen abiadura berean birmarraztuz.
