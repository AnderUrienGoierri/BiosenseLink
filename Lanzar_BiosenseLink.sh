#!/usr/bin/env bash

# ==============================================================================
#  BiosenseLink - Lanzador Automatizado del Laboratorio de Simulacion (IoMT)
# ==============================================================================

# Colores para terminal
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}======================================================================${NC}"
echo -e "${CYAN} [IoMT] BIOSENSELINK - GATEWAY Y PLATAFORMA DE SIMULACION POINT-OF-CARE${NC}"
echo -e "${CYAN}======================================================================${NC}"
echo ""

# Activar el entorno virtual de Python si existe
if [ -f "$HOME/biomed_env/bin/activate" ]; then
    source "$HOME/biomed_env/bin/activate"
    echo -e "${GREEN}[OK] Entorno virtual 'biomed_env' activado.${NC}"
else
    echo -e "${YELLOW}[!] Advertencia: No se encontró el entorno virtual en ~/biomed_env.${NC}"
fi

# --- Paso 1: Comprobar y Arrancar Contenedores Docker ---
echo -e "\n${YELLOW}[1/3] Verificando contenedores Docker...${NC}"
requiredContainers=("clinical-postgres-db" "hapi-fhir-server")

for container in "${requiredContainers[@]}"; do
    status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null)
    if [ "$status" = "running" ]; then
        echo -e "  ${GREEN}[OK] Contenedor [$container] ya está activo.${NC}"
    elif [ "$status" = "exited" ] || [ "$status" = "paused" ]; then
        echo -e "  ${YELLOW}[*] Iniciando contenedor [$container]...${NC}"
        docker start "$container" > /dev/null
        echo -e "  ${GREEN}[OK] Contenedor [$container] arrancado con éxito.${NC}"
    else
        echo -e "  ${RED}[!] No se encontró el contenedor [$container]. Levántalo con docker compose.${NC}"
    fi
done

# Verificar si el servicio Ollama está activo (nativo en Fedora)
echo -e "  ${YELLOW}[*] Verificando estado de Ollama local (systemd)...${NC}"
if systemctl is-active --quiet ollama || curl -s http://localhost:11434 > /dev/null; then
    echo -e "  ${GREEN}[OK] Ollama local está activo y respondiendo en el puerto 11434.${NC}"
else
    echo -e "  ${RED}[!] Ollama no está respondiendo. Ejecuta 'sudo systemctl start ollama' o inicia el servicio.${NC}"
fi

# --- Paso 2: Sincronizar BBDD PostgreSQL ---
echo -e "\n${YELLOW}[2/3] Sincronizando usuarios y roles en PostgreSQL...${NC}"
if [ -f "scripts/db_setup.py" ]; then
    if python3 scripts/db_setup.py; then
        echo -e "  ${GREEN}[OK] Base de datos e inicialización completadas con éxito.${NC}"
    else
        echo -e "  ${RED}[!] No se pudo inicializar la BBDD. Asegúrate de que Postgres está respondiendo en el puerto 5432.${NC}"
    fi
else
    echo -e "  ${RED}[!] No se encontró el archivo scripts/db_setup.py. Ejecuta el script desde la raíz del proyecto.${NC}"
fi

# --- Paso 3: Arrancar Consola Web y Servidor ---
echo -e "\n${YELLOW}[3/3] Iniciando Servidor de Telemetría IoMT (FastAPI en Puerto 8081)...${NC}"
echo -e "  ${GREEN}[+] Abriendo Consola Clínica Web en tu navegador por defecto...${NC}"

# Abrir el navegador en Fedora
xdg-open "http://localhost:8081/" &> /dev/null &

echo -e "  ${CYAN}[+] Servidor de telemetría activo y escuchando...${NC}"
echo -e "  ${YELLOW}[*] Para apagar el servidor y terminar la simulación, pulsa Ctrl + C.${NC}"
echo ""

if [ -f "scripts/server.py" ]; then
    python3 scripts/server.py
else
    echo -e "${RED}[!] Error: No se encontró el archivo scripts/server.py.${NC}"
fi
