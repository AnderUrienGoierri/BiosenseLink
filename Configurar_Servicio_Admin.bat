@echo off
:: ============================================================
::  BiosenseLink - Configurador de Servicio Windows
::  Doble clic -> pide UAC -> configura y arranca el servicio
:: ============================================================

:: Auto-elevacion UAC
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Solicitando permisos de Administrador...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ---- Variables ----
set NSSM=C:\Users\anurt\AppData\Local\Microsoft\WinGet\Packages\NSSM.NSSM_Microsoft.Winget.Source_8wekyb3d8bbwe\nssm-2.24-101-g897c7ad\win64\nssm.exe
set SVCNAME=BiosenseLink
set LOGDIR=C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink\logs
set POWERSHELL=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
set SCRIPT=C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink\scripts\launchers\BiosenseLink_Service.ps1
set WORKDIR=C:\Dev\05_Projects\Biomedical_IoMT\BiosenseLink

echo.
echo ================================================================
echo   BiosenseLink - Configuracion de Servicio Windows
echo ================================================================
echo.

:: Crear directorio de logs si no existe
if not exist "%LOGDIR%" mkdir "%LOGDIR%"

:: Detener si estaba corriendo
echo [1/5] Deteniendo servicio si estaba activo...
net stop %SVCNAME% >nul 2>&1

:: Aplicar configuracion completa con NSSM
echo [2/5] Aplicando configuracion del servicio...
"%NSSM%" set %SVCNAME% AppDirectory "%WORKDIR%"
"%NSSM%" set %SVCNAME% Description "BiosenseLink IoMT Telemetry Server (FastAPI puerto 8081)"
"%NSSM%" set %SVCNAME% AppStdout "%LOGDIR%\biosenselink_service.log"
"%NSSM%" set %SVCNAME% AppStderr "%LOGDIR%\biosenselink_error.log"
"%NSSM%" set %SVCNAME% AppRotateFiles 1
"%NSSM%" set %SVCNAME% AppRotateSeconds 86400
"%NSSM%" set %SVCNAME% AppRotateBytes 10485760
"%NSSM%" set %SVCNAME% AppRestartDelay 5000
"%NSSM%" set %SVCNAME% AppThrottle 1500

:: Arranque automatico retrasado (espera a que Docker Desktop este listo)
echo [3/5] Configurando inicio automatico retrasado...
sc.exe config %SVCNAME% start= delayed-auto
sc.exe description %SVCNAME% "BiosenseLink IoMT Telemetry Server - FastAPI puerto 8081"

:: Configurar reinicio automatico si falla
echo [4/5] Configurando reinicio automatico ante fallos...
sc.exe failure %SVCNAME% reset= 60 actions= restart/10000/restart/30000/restart/60000

:: Arrancar el servicio ahora
echo [5/5] Arrancando servicio BiosenseLink...
net start %SVCNAME%

echo.
echo ================================================================
if %errorLevel% equ 0 (
    echo   EXITO: BiosenseLink corriendo en http://localhost:8081
) else (
    echo   AVISO: El servicio puede tardar unos segundos en arrancar.
    echo   Revisa los logs en: %LOGDIR%
)
echo ================================================================
echo.
echo Puedes cerrar esta ventana.
pause
