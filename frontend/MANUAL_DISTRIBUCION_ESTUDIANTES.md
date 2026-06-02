# 📱 Manual de Distribución e Instalación para Estudiantes
## Suite de Simulación Point-of-Care (PoC) & HAPI FHIR R4

Este manual está diseñado para enseñar a los **estudiantes de enfermería, medicina, profesionales de la salud y profesores** cómo instalar la aplicación de simulación clínica en sus propios teléfonos móviles y conectarse al laboratorio de simulación en bucle cerrado.

---

## 📦 1. Ubicación y Distribución de la Aplicación (`.apk`)

La aplicación móvil nativa ya ha sido compilada con éxito en la PC de Ander. 

### Dónde encontrar el instalador en la PC:
El archivo instalador para Android se encuentra en la siguiente ruta física de tu proyecto:
👉 **`D:\LLM\Simulation_Lab\Dashboard\android\app\build\outputs\apk\debug\app-debug.apk`**

### Cómo compartirlo con los estudiantes:
Puedes renombrar el archivo `app-debug.apk` a un nombre más amigable (como `Simulation_Lab_Osakidetza.apk`) y enviarlo directamente:
*   Por un grupo de **WhatsApp** o **Telegram**.
*   Subirlo a una carpeta compartida de **Google Drive** o **OneDrive** y pasarles el enlace.
*   Enviarlo por correo electrónico.

---

## 📲 2. Instrucciones de Instalación para el Estudiante (Android)

Los estudiantes que reciban el archivo `.apk` en sus teléfonos deben seguir estos sencillos pasos:

1.  **Descargar el archivo:** Tocar el archivo `.apk` recibido en WhatsApp, Drive o navegador para descargarlo en el móvil.
2.  **Permitir Fuentes Desconocidas:** Al abrir el archivo por primera vez, Android mostrará una advertencia de seguridad. Tocar en **Ajustes** y activar la opción **"Permitir desde esta fuente"** (o "Instalar aplicaciones desconocidas").
3.  **Instalar:** Regresar a la pantalla anterior y presionar **Instalar**.
4.  **Abrir la App:** Una vez instalada, aparecerá el icono de **Simulation Lab** en el menú de aplicaciones del móvil. ¡Listo para iniciar!

---

## 📡 3. Cómo Conectar los Móviles de los Estudiantes al Servidor en Clase (Conexión Wi-Fi)

Por defecto, la aplicación instalada busca los servidores de datos clínicos y control en `localhost` (la propia PC de Ander por USB). Para que los móviles de **otros estudiantes** puedan ver la telemetría en vivo, deben conectarse al ordenador de Ander a través de la **red Wi-Fi local** (por ejemplo, el Wi-Fi de Goierri Eskola o un Punto de Acceso/Hotspot móvil creado desde el propio móvil).

### Paso A: Obtener la IP Local de la PC de Ander
En la PC de Ander:
1. Abre una consola de PowerShell o CMD.
2. Ejecuta el comando:
   ```powershell
   ipconfig
   ```
3. Busca la sección de tu adaptador Wi-Fi y anota la **Dirección IPv4** (por ejemplo: `192.168.1.35` o `10.0.0.12`).

### Paso B: Compilar la Versión de Red Wi-Fi
Para que la app busque los servidores en la IP de tu PC, realiza esta pequeña modificación rápida en el código:

1. Abre el archivo [Dashboard/www/js/app.js](file:///D:/LLM/Simulation_Lab/Dashboard/www/js/app.js) en tu PC.
2. En las **líneas 7 y 8**, reemplaza `localhost` por la IP de tu ordenador (por ejemplo, si tu IP es `192.168.1.35`):
   ```javascript
   // Cambiar esto:
   // const FHIR_URL = "http://localhost:8080/fhir";
   // const CONTROL_URL = "http://localhost:8081/api/control";

   // Por la IP de tu PC:
   const FHIR_URL = "http://192.168.1.35:8080/fhir";
   const CONTROL_URL = "http://192.168.1.35:8081/api/control";
   ```
3. Abre el archivo [Dashboard/www/js/api.js](file:///D:/LLM/Simulation_Lab/Dashboard/www/js/api.js) y reemplaza las menciones de `localhost:8081` en las **líneas 78 y 156** por la IP de tu PC:
   ```javascript
   // Línea 78:
   const response = await fetch(`http://192.168.1.35:8081/api/config/triage`, ...
   
   // Línea 156:
   const biosensorResponse = await fetch(`http://192.168.1.35:8081/api/config/patient`, ...
   ```
4. En tu terminal, sincroniza el código y vuelve a compilar la App ejecutando:
   ```powershell
   npx cap sync
   npx cap run android
   ```
5. **¡Listo!** El archivo `app-debug.apk` resultante ya está configurado para la red local. Comparte **este nuevo `.apk`** con tus estudiantes. Todos los móviles que estén conectados a la misma red Wi-Fi que tu ordenador recibirán los signos vitales, las gráficas y las alarmas acústicas en tiempo real directamente desde tu servidor.

---

## 🔒 4. Nota Importante de Ciberseguridad (Cortafuegos/Firewall)
Si los estudiantes se instalan el `.apk` con tu IP local pero la App se queda en pantalla de carga o marca "Offline" (Puerto 8081 desconectado), es casi seguro que el **Firewall de Windows** en tu PC está bloqueando las conexiones entrantes desde el exterior.

### Cómo solucionarlo en 1 minuto en la PC de Ander:
1. Presiona la tecla Windows, escribe **Firewall de Windows Defender** y ábrelo.
2. En la barra lateral izquierda, selecciona **Configuración avanzada**.
3. Haz clic en **Reglas de entrada** y luego en **Nueva regla** (barra derecha).
4. Elige **Puerto**, haz clic en Siguiente.
5. Selecciona **TCP** y en Puertos locales específicos escribe: **`8080, 8081`**.
6. Elige **Permitir la conexión**, haz clic en Siguiente.
7. Asegúrate de marcar **Privado** y **Doméstico/Trabajo** (puedes marcar Público si estás usando un Hotspot móvil).
8. Ponle un nombre (por ejemplo: "Laboratorio Simulación Clínica PoC") y haz clic en Finalizar.

¡Con esto, tu laboratorio se convertirá en un entorno de simulación clínica multi-dispositivo real de primer nivel para toda tu clase de Goierri Eskola!
