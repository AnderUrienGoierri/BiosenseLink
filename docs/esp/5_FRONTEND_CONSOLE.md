# 💻 Consola Frontend y Telemetría Web UI

BiosenseLink evita el uso de clientes pesados (Fat Clients) tradicionales en la telemedicina en favor de una arquitectura web ágil, utilizando tecnologías estándar del navegador (HTML5, JavaScript ES6) para renderizar gráficos médicos complejos a 60 FPS sin sobrecargar la CPU del dispositivo.

---

## 1. Osciloscopio Médico (HTML5 Canvas)

El monitor electrocardiográfico no se renderiza usando librerías DOM lentas (como Chart.js convencional o D3.js puro) debido a la altísima densidad de datos (500 muestras por segundo). En su lugar, se emplea el API **HTML5 Canvas** crudo, gestionado por `ui.js`.

### 1.1. Doble Búfer y Cuadrícula Médica
*   **Fondo Estático (CSS Pattern):** La clásica cuadrícula milimetrada del papel de ECG (cuadros grandes de 5mm, pequeños de 1mm) se dibuja mediante un patrón CSS nativo (`bg-ecg-grid`). Esto evita que el motor JS tenga que redibujar las líneas en cada *frame*.
*   **Lienzo Dinámico (Canvas):** JavaScript recibe arrays Float32 por el WebSocket y utiliza `ctx.lineTo()` y `ctx.stroke()` para trazar la línea isoelectrolítica verde (color: `#4ecdc4`) con efectos de *Glow* tipo fósforo de tubo de rayos catódicos (CRT).

### 1.2. Algoritmo de Trazado de Barrido (Sweep)
A diferencia de los gráficos de desplazamiento (scroll), los monitores médicos reales usan un barrido que se reinicia de izquierda a derecha borrando gradualmente la señal antigua (efecto "fade" o barra negra desplazante). El frontend implementa esta lógica rastreando el índice de dibujo actual `x` y borrando un bloque `[x, x + Δx]` por delante de la aguja virtual.

---

## 2. Motor de Telemetría (WebSocket y REST)

La arquitectura desacopla el streaming de alta frecuencia de las llamadas transaccionales.

*   **Flujo WebSocket (`api.js`)**: Conexión Full-Duplex abierta en `ws://localhost:8081/ws/ecg`. Solo transfiere el tensor de voltajes y el marcador de tiempo. Es extremadamente ligero.
*   **Polling REST (Opcional)**: La aplicación realiza llamadas a `GET /api/vitals` si la tarea asíncrona no empuja los datos vía WS, garantizando tolerancia a fallos.
*   **Eventos de Control**: Los botones de Triage (Fibrilación Auricular, Taquicardia Ventricular) envían comandos mediante `POST /api/control/set_scenario` que el Gateway procesa instantáneamente.

---

## 3. Localización Dinámica In-Vivo (i18n)

Para garantizar la usabilidad en entornos sanitarios bilingües (Osakidetza), la interfaz cuenta con un motor de internacionalización (`i18n.js`) que traduce la consola *en caliente* sin recargar la página.

### 3.1. Arquitectura del i18n
*   **Diccionarios en Memoria**: El archivo `i18n.js` alberga los objetos JSON para `es` (Español) y `eu` (Euskara).
*   **Inyección por ID**: Al cambiar de idioma en el header, un bucle en O(n) recorre los IDs del DOM (`auth-title`, `triage-afib`, etc.) inyectando el valor correspondiente sin destruir los nodos SVG colindantes gracias a la función `changeLanguage()`.
*   **Persistencia**: La preferencia del usuario se guarda en `localStorage` bajo la clave `biosenselink_lang`.

---

## 4. Visualizador de Escritorio (Matplotlib)

Para el análisis detallado offline, el botón *Lanzar Visualizador de Escritorio* invoca `main.py`.

*   **Matplotlib GridSpec**: Divide la interfaz nativa en paneles (Gráficas, CDSS, Controles).
*   **Multi-Lead Layouts**: Renderiza el estándar americano **4x3+1 Grid** (4 columnas de tiempo de 2.5s cada una, con la derivación II en la parte inferior como *Rhythm Strip* continua de 10s).
*   **RadioButtons Locales**: Implementa el cambio de idioma `es`/`eu` redibujando ejes y traducciones de reportes patológicos a la misma velocidad que la interfaz Web.
