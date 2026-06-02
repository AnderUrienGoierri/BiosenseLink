# 🎨 Biblioteca de Iconos Vectoriales Premium (SVG)
## Catálogo Completo de Activos para Markdown, HTML5 y Automatizaciones (n8n)

¡Enhorabuena! Has creado una colección masiva de **55 iconos vectoriales minimalistas y profesionales** estilo Lucide/Feather. 

Todos los iconos están diseñados con **trazos transparentes (`stroke="currentColor"`)** y un tamaño base (`viewBox`) de `0 0 24 24`. Esto significa que **heredan automáticamente el tamaño y el color del texto CSS** del contenedor que los aloja, adaptándose perfectamente a temas claros o nocturnos.

---

## 📂 Directorio de Activos Compilados

Los iconos están organizados de manera lógica en tu disco duro en la ruta **`D:\LLM\Assets\Icons\`**:

### 🩺 1. Clínica y Diagnósticos (`📁 Medical/`)
Ideales para Point-of-Care, CDSS, registros FHIR y telemetría de pacientes:
*   `heart-pulse.svg`: Corazón con señal de pulso cardíaco integrada.
*   `droplet-blood.svg`: Gota fluida para saturación de oxígeno ($SpO_2$) o hematología.
*   `thermometer.svg`: Termómetro clínico de precisión.
*   `patient-user.svg`: Expediente clínico o perfil de paciente.
*   `shield-health.svg`: Escudo médico para ciberseguridad y protección de datos.
*   `pill.svg`: Cápsula farmacéutica / Medicación.
*   `stethoscope.svg`: Fonendoscopio de auscultación.
*   `syringe.svg`: Jeringuilla clínica para vacunas o reactivos.
*   `bandage.svg`: Tirita / Primeros auxilios.
*   `brain.svg`: Cerebro (neurología, neurociencia o inteligencia artificial).
*   `eye.svg`: Ojo / Monitorización visual / Oftalmología.

### 🧬 2. Biotecnología y Laboratorio (`📁 Biotech/`)
Diseñados para biorreactores, bioquímica, cultivos celulares e ingeniería de procesos:
*   `dna.svg`: Cadena de doble hélice de ADN.
*   `microscope.svg`: Microscopio de análisis metrológico.
*   `flask-conical.svg`: Matraz Erlenmeyer de laboratorio.
*   `test-tube.svg`: Tubo de ensayo con marcas de volumen graduado.
*   `flame-burner.svg`: Llama de mechero Bunsen o energía térmica.
*   `leaf.svg`: Hoja orgánica (biotecnología verde / ambiental).
*   `sprout.svg`: Brote (cultivo celular / crecimiento bacteriano).
*   `biohazard.svg`: Símbolo internacional de Riesgo Biológico.
*   `radiation.svg`: Símbolo internacional de Riesgo de Radiación.

### 💻 3. Tecnología, Sistemas y Código (`📁 Tech/`)
Perfecto para control de versiones, hardware, conectividad y seguridad de redes:
*   `cpu.svg`: Microprocesador de hardware.
*   `database.svg`: Servidor de base de datos de persistencia.
*   `terminal.svg`: Consola de comandos / CLI.
*   `activity-signal.svg`: Pulso o señal de onda de transductores analógicos.
*   `server.svg`: Servidor web / Docker Container.
*   `code.svg`: Etiquetas de código de programación (`</>`).
*   `git-branch.svg`: Ramificación de control de versiones.
*   `git-commit.svg`: Registro de confirmación de cambios.
*   "git-pull-request.svg": Solicitud de fusión de código.
*   `settings-cog.svg`: Engranaje de configuración o calibración.
*   `sliders.svg`: Deslizadores analógicos de sintonización de procesos.
*   `wifi.svg`: Conexión inalámbrica a Internet o pasarela PoC.
*   `bluetooth.svg`: Conexión de sensores de rango corto.
*   `usb.svg`: Conexión física para transductores por cable.
*   `hard-drive.svg`: Almacenamiento local o disco duro.
*   `lock-secure.svg`: Candado de cifrado SSL/TLS.
*   `key-auth.svg`: Llave de autenticación API o token.

### ⚠️ 4. Alertas y Utilidades Generales (`📁 General/`)
Ideal para sustituir emoticonos en tus archivos de texto y flujos de navegación:
*   `alert-circle.svg`: Alerta crítica / Fallo de sistema (Color sugerido: Rojo).
*   `alert-triangle.svg`: Advertencia moderada / Precaución (Color sugerido: Amarillo).
*   `check-circle.svg`: Éxito / Operación completada (Color sugerido: Verde).
*   `info.svg`: Detalle informativo de contexto (Color sugerido: Azul).
*   `refresh.svg`: Recargar / Sincronizar datos.
*   `home.svg`: Página de inicio o directorio raíz.
*   `search.svg`: Lupa de búsqueda o filtrado.
*   `trash.svg`: Eliminar / Depurar datos.
*   `edit.svg`: Lápiz de edición o modificación.
*   `download.svg`: Descargar archivos o logs.
*   `upload.svg`: Cargar configuraciones o imágenes.
*   `copy-clipboard.svg`: Copiar texto al portapapeles.
*   `external-link.svg`: Enlace a recursos externos.
*   `arrow-right.svg`: Flecha derecha para navegación.
*   `arrow-left.svg`: Flecha izquierda para retroceso.
*   `mail.svg`: Notificaciones por correo electrónico.
*   `clock.svg`: Temporizador o reloj de marcas temporales.
*   `user-simple.svg`: Perfil de usuario estándar.

---

## 🛠️ Cómo Utilizarlos

### 📄 En tus Archivos Markdown (`.md`)
Sustituye emojis insertando la ruta local del SVG de alta definición:

```markdown
![Biohazard](file:///D:/LLM/Assets/Icons/Biotech/biohazard.svg) **NIVEL DE BIOSEGURIDAD: BSL-2**

![Git Commit](file:///D:/LLM/Assets/Icons/Tech/git-commit.svg) Repositorio sincronizado en el SSD Lunar Lake.
```

### 🌐 En tus Desarrollos e Interfaces Web (HTML5 / Tailwind)
Copia el código SVG en línea para modificar el color dinámicamente con clases de texto de Tailwind:

```html
<!-- Icono de ADN en color verde esmeralda -->
<div class="flex items-center gap-2 text-emerald-400">
    <svg class="w-6 h-6 animate-pulse" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="m8 3 4 8 5-5M4 14l8-8 4 4M14 21l-4-8-5 5M20 10l-8 8-4-4"/>
    </svg>
    <span>Secuencia Genómica</span>
</div>
```
