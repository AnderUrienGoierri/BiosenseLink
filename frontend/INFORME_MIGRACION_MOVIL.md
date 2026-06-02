# 🔬 Informe Técnico de Migración: Versión Móvil de Simulation Lab
## Desarrollo de Aplicación Multiplataforma (DAM) & Metrología de Datos en Salud (Ph.D.)

Este documento contiene un registro detallado de las decisiones arquitectónicas, resoluciones de errores y configuraciones técnicas realizadas para portar y compilar la suite web del **Laboratorio de Simulación Point-of-Care (PoC) & HAPI FHIR** como una aplicación móvil nativa de Android ejecutable en un dispositivo físico **OnePlus 8 Pro**.

---

## 🏗️ 1. Arquitectura de Portabilidad Móvil (Capacitor)
Para trasladar la aplicación a un formato móvil de alto rendimiento y fidelidad sin reescribir la lógica de simulación (modularizada en JavaScript vanilla con Tailwind CSS y Chart.js), elegimos **Capacitor (por Ionic)** como tecnología de envoltura híbrida.

### ¿Por qué Capacitor?
1. **Contenedor Webview Nativo:** Capacitor monta un motor Webview optimizado dentro de una actividad de Android. Esto permite que tu HTML5, CSS reactivo y librerías modularizadas de JS corran a velocidad nativa.
2. **Compatibilidad Absoluta:** No interfiere en tus ontologías clínicas (LOINC, UCUM) ni en las peticiones AJAX de comunicación FHIR.
3. **Mantenibilidad:** Mantiene un único "core" de desarrollo web y lo despliega de forma multiplataforma.

---

## 🛠️ 2. Resoluciones de Errores Paso a Paso (Bitácora de Ingeniería)

### Paso A: Resolución del Espacio de Trabajo (Workspace) en el IDE
*   **Problema Inicial:** Intentar abrir la ruta virtual MTP del móvil conectado (`Este equipo\OnePlus 8 Pro\Memoria interna`) en el IDE.
*   **Causa:** Los móviles se montan en Windows mediante MTP (Media Transfer Protocol), el cual no crea una letra de volumen de disco físico (como `C:` o `D:`), sino un "Shell Namespace" virtual. Los compiladores, scripts de PowerShell y sistemas de compilación no pueden acceder a estas rutas a través de llamadas clásicas de archivos Win32.
*   **Solución:** Abrir la carpeta local de la PC **`D:\LLM\Simulation_Lab`** como espacio de trabajo activo. Desarrollamos localmente y utilizamos las herramientas ADB del Android SDK para enviar y arrancar las compilaciones en el móvil por el cable USB de forma automática.

---

### Paso B: Solución al Error de `webDir: "."` en Capacitor
*   **Problema:** Al agregar la plataforma de Android con `npx cap add android`, Capacitor arrojó el error `[error] "." is not a valid value for webDir` y falló al buscar el archivo `capacitor.plugins.json`.
*   **Causa:** Capacitor requiere por seguridad que los recursos web estén ubicados dentro de un subdirectorio limpio (por ejemplo, `www`, `dist` o `public`) para no empaquetar archivos pesados de desarrollo como `node_modules/` o la propia carpeta nativa `android/` en el instalador `.apk`.
*   **Solución Aplicada:**
    1. Creamos la subcarpeta **`Dashboard/www`**.
    2. Copiamos allí de forma estructurada `index.html`, `style.css` y el directorio `js/`.
    3. Copiamos el directorio externo de logotipos de la suite ubicado en `D:\LLM\Assets` hacia **`Dashboard/www/Assets`** para que las imágenes se empaqueten dentro del `.apk`.
    4. Cambiamos la referencia en el HTML de la imagen de `../../Assets/` a `Assets/` para que sea local dentro de la App.
    5. Actualizamos el script de automatización de Windows [run_simulation_lab.ps1](file:///D:/LLM/Simulation_Lab/run_simulation_lab.ps1) (Línea 73) para que al arrancar en el ordenador abra la nueva ruta `Dashboard/www/index.html`.
    6. Modificamos [capacitor.config.json](file:///D:/LLM/Simulation_Lab/Dashboard/capacitor.config.json) estableciendo `"webDir": "www"`.
    7. Al reejecutar `npx cap add android`, el proyecto de Android nativo se generó al 100% y sin errores.

---

### Paso C: Solución al Error de Licencias de Build-Tools 35
*   **Problema:** La compilación de Gradle falló debido a que no se habían aceptado las licencias del SDK de Android para `build-tools;35.0.0`.
*   **Causa:** Google requiere que aceptes expresamente los contratos de licencia de cada API o conjunto de herramientas antes de descargarlas mediante scripts automatizados.
*   **Solución Aplicada:**
    Utilizamos la herramienta especializada **Android CLI** integrada en el IDE para descargar e instalar directamente las dependencias del SDK:
    ```powershell
    android sdk install build-tools/35.0.0
    android sdk install platforms/android-35 platforms/android-34
    ```
    El gestor del SDK firmó e integró automáticamente las licencias requeridas por Google en tu entorno local.

---

### Paso D: Resolución del Conflicto de Versión de Java (`invalid source release: 21`)
*   **Problema:** Gradle abortó la compilación arrojando el error `Execution failed for task ':capacitor-android:compileDebugJavaWithJavac' > Java compilation initialization error > error: invalid source release: 21`.
*   **Causa:** Tu PC tiene instalado y activo **Java 17 (Microsoft OpenJDK LTS)**, mientras que Capacitor 7 / Android Gradle Plugin están configurados para compilar por defecto con **Java 21**. Al intentar compilar, el compilador Java 17 de tu PC no reconoce la bandera de versión superior 21 y aborta.
*   **Solución Aplicada (El "Gradle Override Hack"):**
    Para no obligarte a descargar y configurar un JDK 21 entero (y alterar tus variables de entorno globales del sistema), añadimos un script de anulación dinámico en el archivo de compilación raíz [build.gradle](file:///D:/LLM/Simulation_Lab/Dashboard/android/build.gradle):
    ```groovy
    subprojects {
        afterEvaluate { project ->
            if (project.hasProperty("android")) {
                project.android {
                    compileOptions {
                        sourceCompatibility JavaVersion.VERSION_17
                        targetCompatibility JavaVersion.VERSION_17
                    }
                }
            }
        }
    }
    ```
    Este script intercepta a todos los subproyectos (el núcleo de Capacitor `:capacitor-android` y la aplicación móvil `:app`) y les obliga a compilar bajo la especificación **Java 17**. Al volver a lanzar la compilación, se generó con éxito en 46.67 segundos.

---

## 📡 3. Integración de Comunicaciones en Bucle Cerrado (ADB Reverse)
Uno de los mayores retos en DAM al correr apps en dispositivos físicos es conectar el móvil al servidor `localhost` de la PC.

### El Reto de Red
En móviles, `localhost` apunta al propio teléfono y no a tu PC, lo que haría que las llamadas a HAPI FHIR (`localhost:8080`) y al Biosensor (`localhost:8081`) fallaran de inmediato.

### La Solución de Puente USB
Configuramos túneles de transmisión directa TCP sobre el cable de datos usando **ADB (Android Debug Bridge)** desde tu ordenador:
```powershell
adb reverse tcp:8080 tcp:8080
adb reverse tcp:8081 tcp:8081
```
*   **Resultado:** Cada vez que la aplicación móvil instalada en tu **OnePlus 8 Pro** realiza un `fetch()` a `http://localhost:8080/fhir`, el sistema operativo Android desvía la petición a través del cable USB hacia los servidores Docker HAPI FHIR y PostgreSQL activos en tu PC.

¡La versión móvil de tu laboratorio clínico ya está instalada, activa y operando en bucle cerrado sobre tu OnePlus 8 Pro!
