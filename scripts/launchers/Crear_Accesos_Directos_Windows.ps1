# ==============================================================================
#  BiosenseLink - Creador de Accesos Directos PWA (Modo App) para Windows
# ==============================================================================
#  Este script detecta Chrome o Edge y genera accesos directos en el escritorio
#  de Windows para abrir todos los servicios de telemetría y bases de datos
#  locales como si fuesen aplicaciones nativas de escritorio.
# ==============================================================================

# 1. Buscar Navegador Chromium compatible
$browserPath = ""
$browserName = ""

$pathsToCheck = @(
    @{ Name = "Google Chrome"; Path = "C:\Program Files\Google\Chrome\Application\chrome.exe" },
    @{ Name = "Google Chrome (x86)"; Path = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" },
    @{ Name = "Google Chrome (User)"; Path = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe" },
    @{ Name = "Microsoft Edge"; Path = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" },
    @{ Name = "Microsoft Edge (x64)"; Path = "C:\Program Files\Microsoft\Edge\Application\msedge.exe" }
)

foreach ($item in $pathsToCheck) {
    if (Test-Path $item.Path) {
        $browserPath = $item.Path
        $browserName = $item.Name
        break
    }
}

if (-not $browserPath) {
    Write-Host "[!] Error: No se encontró Google Chrome ni Microsoft Edge instalado en las rutas estándar." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Detectado navegador: $browserName" -ForegroundColor Green
Write-Host "[*] Ruta de ejecutable: $browserPath" -ForegroundColor Gray

# 2. Definir servicios y accesos directos
$desktopDir = [System.IO.Path]::Combine([Environment]::GetFolderPath("Desktop"))
$WshShell = New-Object -ComObject WScript.Shell

$shortcuts = @(
    @{
        Name = "Portal de Enlaces"
        Description = "Dashboard centralizado para todos los puertos e infraestructura"
        Url = "http://localhost:8085"
        Icon = "shell32.dll,24"  # Icono de Casa
    },
    @{
        Name = "BiosenseLink Console"
        Description = "Consola de Simulación y Telemetría Point-of-Care"
        Url = "http://localhost:8081"
        Icon = "imageres.dll,97" # Icono de Estrella/Favorito
    },
    @{
        Name = "Portainer CE"
        Description = "Controlador y Panel Docker de Contenedores"
        Url = "http://localhost:9000"
        Icon = "shell32.dll,21"  # Icono de Engranajes
    },
    @{
        Name = "Paperless-ngx"
        Description = "Gestor Documental y OCR Clínico Inteligente"
        Url = "http://localhost:8010"
        Icon = "shell32.dll,22"  # Icono de Carpeta/Documento
    },
    @{
        Name = "HAPI FHIR Server"
        Description = "Servidor HL7 FHIR R4 de Historia Clínica"
        Url = "http://localhost:8080"
        Icon = "shell32.dll,85"  # Icono de BD en Red
    },
    @{
        Name = "n8n Automation"
        Description = "Orquestador e Integrador de Flujos de Trabajo"
        Url = "http://localhost:5678"
        Icon = "shell32.dll,220" # Icono de Aplicación Ejecutándose
    },
    @{
        Name = "pgAdmin 4"
        Description = "Consola Web de PostgreSQL"
        Url = "http://localhost:5050"
        Icon = "shell32.dll,85"  # Icono de BD
    },
    @{
        Name = "phpMyAdmin"
        Description = "Consola Web de MySQL"
        Url = "http://localhost:8082"
        Icon = "shell32.dll,85"  # Icono de BD
    },
    @{
        Name = "Apache Server"
        Description = "Servidor Web Apache Local (LAMP)"
        Url = "http://localhost:8000"
        Icon = "shell32.dll,14"  # Icono de Red/Globo
    },
    @{
        Name = "Gotenberg PDF"
        Description = "Motor PDF y Generador de Informes Médicos"
        Url = "http://localhost:3000"
        Icon = "shell32.dll,46"  # Icono de Impresora/Documento
    },
    @{
        Name = "Gmail Local App"
        Description = "Bandeja de Correo Electrónico"
        Url = "https://mail.google.com"
        Icon = "shell32.dll,156" # Icono de Correo/Sobre
    }
)

# 3. Crear accesos directos
Write-Host "[*] Generando accesos directos en el escritorio..." -ForegroundColor Yellow
$systemRoot = [Environment]::GetFolderPath("System")

foreach ($item in $shortcuts) {
    $shortcutPath = Join-Path $desktopDir "$($item.Name).lnk"
    
    # Resolver la ruta del icono (ej. C:\Windows\System32\shell32.dll)
    $iconParts = $item.Icon.Split(",")
    $iconFile = Join-Path $systemRoot $iconParts[0]
    $iconIndex = [int]$iconParts[1]
    
    try {
        $Shortcut = $WshShell.CreateShortcut($shortcutPath)
        $Shortcut.TargetPath = $browserPath
        $Shortcut.Arguments = "--app=$($item.Url)"
        $Shortcut.Description = $item.Description
        $Shortcut.WorkingDirectory = [System.IO.Path]::GetDirectoryName($browserPath)
        $Shortcut.IconLocation = "$iconFile,$iconIndex"
        $Shortcut.Save()
        Write-Host "  [OK] Creado: $($item.Name)" -ForegroundColor Green
    }
    catch {
        Write-Host "  [!] Error al crear $($item.Name): $_" -ForegroundColor Red
    }
}

Write-Host "[*] ¡Completado! Tienes todos los accesos en tu escritorio de Windows." -ForegroundColor Green
