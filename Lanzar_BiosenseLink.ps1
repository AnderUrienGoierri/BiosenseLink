# ==============================================================================
#  BiosenseLink - Lanzador Automatizado del Laboratorio de Simulacion (IoMT)
# ==============================================================================
#  Este script automatiza el arranque seguro y la verificacion de toda la suite:
#   1. Comprueba e inicia los contenedores Docker clinicos (Postgres, HAPI FHIR, etc.).
#   2. Sincroniza e inicializa los usuarios en la base de datos PostgreSQL.
#   3. Abre la consola clinica web en tu navegador predeterminado automaticamente.
#   4. Arranca el motor de telemetria de Python (FastAPI en puerto 8081).
# ==============================================================================

Clear-Host
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " [IoMT] BIOSENSELINK - GATEWAY Y PLATAFORMA DE SIMULACION POINT-OF-CARE" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# --- Paso 1: Comprobar y Arrancar Contenedores Docker ---
Write-Host "[1/3] Verificando contenedores Docker..." -ForegroundColor Yellow
$requiredContainers = @("clinical-postgres-db", "hapi-fhir-server", "ollama")

foreach ($container in $requiredContainers) {
    $status = docker inspect -f '{{.State.Status}}' $container 2>$null
    if ($status -eq "running") {
        Write-Host "  [OK] Contenedor [$container] ya esta activo." -ForegroundColor Green
    } elseif ($status -eq "exited" -or $status -eq "paused") {
        Write-Host "  [*] Iniciando contenedor [$container]..." -ForegroundColor Yellow
        docker start $container | Out-Null
        Write-Host "  [OK] Contenedor [$container] arrancado con exito." -ForegroundColor Green
    } else {
        Write-Host "  [!] No se encontro el contenedor [$container]. Asegurate de que existe en Docker Desktop." -ForegroundColor Red
    }
}
Write-Host ""

# --- Paso 2: Sincronizar BBDD PostgreSQL ---
Write-Host "[2/3] Sincronizando usuarios y roles en PostgreSQL..." -ForegroundColor Yellow
try {
    python scripts/db_setup.py
    Write-Host "  [OK] Base de datos e inicializacion completadas con exito." -ForegroundColor Green
} catch {
    Write-Host "  [!] No se pudo inicializar la BBDD. Asegurate de que Postgres esta respondiendo en el puerto 5432." -ForegroundColor Red
}
Write-Host ""

# --- Paso 3: Arrancar Consola Web y Servidor ---
Write-Host "[3/3] Iniciando Servidor de Telemetria IoMT (FastAPI en Puerto 8081)..." -ForegroundColor Yellow
Write-Host "  [+] Abriendo Consola Clinica Web en tu navegador por defecto..." -ForegroundColor Green
Start-Process "http://localhost:8081/"
Write-Host "  [+] Servidor de telemetria activo y escuchando..." -ForegroundColor Gray
Write-Host "  [*] Para apagar el servidor y terminar la simulacion, cierra esta ventana." -ForegroundColor Gray
Write-Host ""

python scripts/server.py
