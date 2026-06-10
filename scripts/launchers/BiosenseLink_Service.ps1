# ==============================================================================
#  BiosenseLink - Script de Servicio Windows (para NSSM)
# ==============================================================================
#  Versión sin interacción de usuario, diseñada para ejecutarse como servicio.
#  Diferencias con el launcher manual:
#   - Sin Clear-Host ni colores (NSSM captura stdout/stderr a archivo de log)
#   - Sin Start-Process para el navegador (no hay sesión de usuario en servicios)
#   - Espera activa a que Docker Desktop esté listo antes de continuar
#   - Reintentos automáticos si los contenedores no responden
# ==============================================================================

$PYTHON     = "C:\Users\anurt\AppData\Local\Python\pythoncore-3.14-64\python.exe"
$WORKDIR    = "C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink"
$SERVER_PY  = "$WORKDIR\scripts\server.py"
$DB_SETUP   = "$WORKDIR\scripts\db_setup.py"

Set-Location $WORKDIR

Write-Output "[BiosenseLink-Service] =============================================="
Write-Output "[BiosenseLink-Service] Iniciando BiosenseLink como Servicio Windows"
Write-Output "[BiosenseLink-Service] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "[BiosenseLink-Service] =============================================="

# --- Paso 1: Esperar a que Docker Desktop esté operativo ---
Write-Output "[1/3] Esperando a que Docker Desktop esté disponible..."
$maxWait = 120  # segundos máximos de espera
$elapsed = 0
$dockerReady = $false

while ($elapsed -lt $maxWait) {
    try {
        $info = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            Write-Output "  [OK] Docker Desktop está operativo."
            break
        }
    } catch {}
    Write-Output "  [*] Docker no está listo aún, reintentando en 5s... ($elapsed/$maxWait s)"
    Start-Sleep -Seconds 5
    $elapsed += 5
}

if (-not $dockerReady) {
    Write-Output "  [!] ADVERTENCIA: Docker no respondió tras $maxWait segundos. Continuando sin Docker..."
}

# --- Paso 2: Verificar y arrancar contenedores requeridos ---
Write-Output "[2/3] Verificando contenedores Docker clínicos..."
$requiredContainers = @("clinical-postgres-db", "hapi-fhir-server", "ollama")

foreach ($container in $requiredContainers) {
    $status = docker inspect -f '{{.State.Status}}' $container 2>$null
    if ($status -eq "running") {
        Write-Output "  [OK] [$container] ya activo."
    } elseif ($status -eq "exited" -or $status -eq "paused") {
        Write-Output "  [*] Arrancando [$container]..."
        docker start $container | Out-Null
        Start-Sleep -Seconds 2
        Write-Output "  [OK] [$container] arrancado."
    } else {
        Write-Output "  [!] [$container] no encontrado o en estado desconocido: '$status'"
    }
}

# Esperar a que Postgres esté listo (el servidor Python depende de él)
Write-Output "  [*] Esperando 5s para que PostgreSQL inicialice completamente..."
Start-Sleep -Seconds 5

# --- Paso 3: Sincronizar base de datos ---
Write-Output "[3/3] Sincronizando base de datos PostgreSQL..."
try {
    & $PYTHON $DB_SETUP
    if ($LASTEXITCODE -eq 0) {
        Write-Output "  [OK] Base de datos sincronizada correctamente."
    } else {
        Write-Output "  [!] db_setup.py terminó con código $LASTEXITCODE — continuando igualmente."
    }
} catch {
    Write-Output "  [!] Error en db_setup: $_"
}

# --- Paso 4: Arrancar servidor FastAPI (proceso principal del servicio) ---
Write-Output "[OK] Lanzando servidor BiosenseLink en puerto 8081..."
Write-Output "[OK] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') — Servidor iniciado."

& $PYTHON $SERVER_PY
