@echo off
title BiosenseLink Launcher
echo ==============================================
echo  Iniciando Lanzador Clinico BiosenseLink...
echo ==============================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Lanzar_BiosenseLink.ps1"
echo.
echo Servidor apagado. Presione una tecla para salir.
pause > null
