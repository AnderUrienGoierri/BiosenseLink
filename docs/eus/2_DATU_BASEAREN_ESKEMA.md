# 🗄️ Datu-basearen Eskema eta Segurtasun Klinikoa (RBAC)

Dokumentu honek **BiosenseLink** ekosisteman hedatutako PostgreSQL datu-base erlazionalaren topologia zehazten du, ingurune mediko simulatu batean sarbide-kontrolean, trazabilitatean eta segurtasun teknikoan oinarrituz.

---

## 1. Tokiko Biltegiratze Arkitektura

Etengabeko telemetria eta diagnostiko egituratuak **HAPI FHIR R4** zerbitzarian (`8080` ataka) dinamikoki injektatzen diren bitartean, plataformak latentzia txikiko eta gogor tipifikatutako sistema sendo bat behar du Profesionalen Identitatea eta Sarbidea kudeatzeko (IAM/RBAC). Horretarako, tokiko Docker edukiontzi batean martxan dagoen **PostgreSQL 15** erabiltzen da.

| Zerbitzua / Parametroa | Konfigurazio Teknikoa |
| :--- | :--- |
| **Datu-base Motorra** | PostgreSQL 15 (Docker: `postgres:15-alpine`) |
| **Erakutsitako Ataka** | `5432` |
| **Bolumen Iraunkorra** | `postgres_data` (Disko fisikoan mapatua datuak ez galtzeko) |
| **Administrazio Kontsola** | `pgAdmin 4` (`5050` ataka) |
| **Kredentzial Orokorrak** | `postgre_pass.txt` (`docs/` karpetaren erroan) |

---

## 2. "Edge Gateway" Paradigma: Erantzukizunen Banaketa

Eskema hau berrikustean ohiko galdera tekniko bat izaten da: **Non daude pazienteen (`patients`) eta konstante bizigarrien (`vital_signs`) taulak?**

Erantzuna BiosenseLink-en diseinu aurreratuan datza, **Edge Gailu (Edge Device) IoMT Gateway** gisa jarduten baitu. Ospitale-ekosistema moderno batean, ohe ondoko monitore kliniko batek ez luke inoiz modu lokalean eta iraunkorrean Historia Kliniko Elektronikoa (HCE) gorde behar ohiko SQL eskemak erabiliz, segurtasun (HIPAA/GDPR) eta datuen sinkronizazio arrazoi zorrotzengatik.

Hori dela eta, biltegiratzea bi silo kontzeptualetan banatzen da:

1.  **PostgreSQL (Funtzionamendu Lokala eta RBAC):** Tokiko gailua gobernatzeko soilik eta esklusiboki erabiltzen da. Bere taula bakarra `clinical_users` da, osasun-langileen sarrera-saiakerari berehala erantzuteko; horrela, latentzia baxuko autentifikazioa ahalbidetzen da, nahiz eta ospitaleak interneteko konexioa galdu.
2.  **HAPI FHIR Zerbitzaria (Datu Klinikoen Biltegia - CDR):** Sortutako datuak (500Hz-ko konstanteak, IA-ren diagnostikoak) ez dira SQL zutabetan egituratzen. Gateway-ak aurkikuntzak hegan paketatzen ditu JSON baliabide estandar internazionaletan (`Observation` eta `DiagnosticReport` bezala) eta zuzenean ospitaleko **HAPI FHIR** zerbitzari zentralera injektatzen ditu. Honek berehalako elkarreragingarritasun klinikoa bermatzen du Osabide Global edo Epic bezalako plataformekin.

*(Pazienteen datuak nola gordetzen diren buruzko informazio gehiago lortzeko, kontsultatu `4_FHIR_INTEGRAZIOA.md` dokumentua)*.

---

## 3. Eskema Erlazionala (DDL)

Hasierako inplementazio script-ak (`db_setup.py`) DDL (Data Definition Language) sententziak exekutatzen ditu modu asinkronoan PostgreSQL-ren gainean `psycopg2` liburutegia erabiliz. Taulen egitura optimizatuta dago autentifikazio prozesuan irakurketa azkarra egiteko.

### Taula: `clinical_users`

Gateway sistemarako sarbidea duen lantalde klinikoa gordetzen du.

```sql
CREATE TABLE IF NOT EXISTS clinical_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    pin VARCHAR(4) NOT NULL,
    role VARCHAR(20) NOT NULL,
    display_name VARCHAR(100) NOT NULL
);
```

**Osotasun Murrizketak:**
*   `username`: Zeharo bakarra izan behar du saio-talkak ekiditeko.
*   `pin`: Egituraz 4 luzerakoa izan behar da. *Ekoizpen ingurune zorrotz batean (HIPAA/GDPR), eremu hau bcrypt/Argon2 algoritmoen bidez hasheatuko litzateke. PoC honetan, testu lauan erabiltzen da, baina sarean zifratuta.*
*   `role`: Zenbaketa logikoa (`admin`, `nurse`). Kontsolan sarbide-maila definitzen du.

---

## 3. Roletan Oinarritutako Sarbide Kontrola (RBAC)

Sarbide Kontrola API mailan (`server.py`) ebazten da, autentifikazio momentuan PostgreSQL datu-baseari galdera eginez.

Berez hedatzen diren bi rol nagusi daude:

1. **Kardiologia Burua / Administratzailea (`admin`)**
   *   **Identitatea:** Dr. Ander Otxoa
   *   **PIN:** `1234`
   *   **Baimenak:** Supererabiltzaile pribilegioak. Sarbide osoa du DSP motorra aldatzeko, artefaktu fisiologikoak zuzenean injektatzeko, telemetria maiztasuna aldatzeko eta FHIR APIa erabiltzeko.

2. **Guardiko Erizaina / Eragilea (`nurse`)**
   *   **Identitatea:** Enf. Amaia Ruiz
   *   **PIN:** `5678`
   *   **Baimenak:** Konstante bizigarrien monitorearen, EKG osziloskopioaren (WebSockets) eta CDSS txostenaren Bistaratzea (Irakurketa Soilik). Ezin ditu simulazioaren parametro fisikoak REST komandoen bidez aldatu.

---

## 4. Auditoria eta Trazabilitatea

Arlo biomedikoan, monitore baten gaineko ekintza klinikoen trazabilitatea nahitaezkoa da (Adibidez: FDA 21 CFR Part 11 araudiak).

*   **Intrusioa eta Blokeoa**: BiosenseLink-eko frontend-ak sarrera huts-egiteak erregistratzen ditu. Erabiltzaile-PIN parekatzearen PostgreSQLren erantzunak `NULL` itzultzen duenean, APIak `HTTP 401 Unauthorized` bidez erantzuten du.
*   **Logging Backend-ean**: FastApi backend-ak saio-hasierako gertaerak modu iraunkorrean idazten ditu Python-en `logging` modulu estandarraren bidez, Kontsola Klinikoarekin izandako interakzioen berreraikitze forentsea ahalbidetuz.

---

## 5. Hasieraketa Automatikoaren Script-a

`scripts/db_setup.py` script-ak hazi idempotente (*seed*) gisa jokatzen du:

1. Behin-behineko kredentzialak erabiliz konektatzen saiatzen da.
2. `clinical_db` datu-basea dagoen egiaztatzen du. Ez badago, sortu egiten du.
3. `clinical_db`-ra konektatzen da.
4. `clinical_users` taula sortzen du ez badago.
5. Hasierako rolak ("Ander" eta "Amaia") injektatzen ditu `INSERT ... ON CONFLICT DO NOTHING` erabiliz.

Honek ingurune medikoa berehala martxan egotea bermatzen du `Lanzar_BiosenseLink.ps1` orkestrazio script-eko "Play" botoia sakatzean.
