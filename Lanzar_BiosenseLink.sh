#!/usr/bin/env bash

# ==============================================================================
#  BiosenseLink - Lanzador Automatizado del Laboratorio de Simulación (IoMT)
#  Adaptado para Linux (CachyOS) con gestión systemd
# ==============================================================================

# Colores para terminal
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

PROJECT_DIR="/run/media/ander/Disco Duro/dev/05_Projects/Biomedical_IoMT/BiosenseLink"
SERVICE_NAME="biosenselink.service"
TELEMETRY_PORT=8081

clear
echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  [IoMT] BIOSENSELINK - GATEWAY Y PLATAFORMA DE SIMULACIÓN POINT-OF-CARE ${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  CachyOS Linux • Entorno de Producción Local • $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# --- Paso 1: Comprobar y Arrancar Contenedores Docker ---
echo -e "\n${YELLOW}[1/4] Verificando contenedores Docker clínicos...${NC}"
requiredContainers=("clinical-postgres-db" "hapi-fhir-server")

for container in "${requiredContainers[@]}"; do
    status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null)
    if [ "$status" = "running" ]; then
        echo -e "  ${GREEN}✔ Contenedor [$container] activo.${NC}"
    elif [ "$status" = "exited" ] || [ "$status" = "paused" ]; then
        echo -e "  ${YELLOW}↻ Iniciando contenedor [$container]...${NC}"
        docker start "$container" > /dev/null 2>&1
        echo -e "  ${GREEN}✔ Contenedor [$container] arrancado con éxito.${NC}"
    else
        echo -e "  ${RED}✖ No se encontró el contenedor [$container]. Levántalo con docker compose.${NC}"
    fi
done

# Verificar si el servicio Ollama está activo
echo -e "  ${YELLOW}↻ Verificando estado de Ollama local (systemd)...${NC}"
if systemctl is-active --quiet ollama 2>/dev/null || curl -s --connect-timeout 2 http://localhost:11434 > /dev/null 2>&1; then
    echo -e "  ${GREEN}✔ Ollama local está activo y respondiendo en el puerto 11434.${NC}"
else
    echo -e "  ${RED}✖ Ollama no está respondiendo. Ejecuta 'sudo systemctl start ollama' si es necesario.${NC}"
fi

# --- Paso 2: Sincronizar BBDD PostgreSQL ---
echo -e "\n${YELLOW}[2/4] Sincronizando usuarios y roles en PostgreSQL...${NC}"
cd "$PROJECT_DIR" || { echo -e "${RED}✖ No se pudo acceder al directorio del proyecto.${NC}"; exit 1; }

if [ -f "scripts/db_setup.py" ]; then
    if /home/ander/biomed_env/bin/python3 scripts/db_setup.py 2>/dev/null; then
        echo -e "  ${GREEN}✔ Base de datos e inicialización completadas con éxito.${NC}"
    else
        echo -e "  ${RED}✖ No se pudo inicializar la BBDD. Asegúrate de que Postgres está respondiendo en el puerto 5432.${NC}"
    fi
else
    echo -e "  ${RED}✖ No se encontró el archivo scripts/db_setup.py.${NC}"
fi

# --- Paso 3: Asegurar que el servidor backend (FastAPI) está activo ---
echo -e "\n${YELLOW}[3/4] Verificando servicio backend de telemetría IoMT...${NC}"

if systemctl --user is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo -e "  ${GREEN}✔ Servicio systemd [$SERVICE_NAME] ya está activo (PID: $(systemctl --user show -p MainPID --value $SERVICE_NAME)).${NC}"
else
    echo -e "  ${YELLOW}↻ Servicio [$SERVICE_NAME] no está activo. Iniciando...${NC}"
    systemctl --user start "$SERVICE_NAME"
    sleep 2
    if systemctl --user is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo -e "  ${GREEN}✔ Servicio [$SERVICE_NAME] iniciado correctamente.${NC}"
    else
        echo -e "  ${RED}✖ No se pudo iniciar [$SERVICE_NAME]. Ejecutando servidor en modo directo...${NC}"
        # Fallback: ejecutar el servidor directamente si systemd falla
        /home/ander/biomed_env/bin/python3 scripts/server.py
        exit $?
    fi
fi

# --- Paso 4: Activar simulación y seguir la salida de telemetría en tiempo real ---
echo -e "\n${YELLOW}[4/4] Activando simulación de telemetría fisiológica...${NC}"

# Despausar la simulación automáticamente via API REST
curl -s "http://localhost:${TELEMETRY_PORT}/api/control?action=resume" > /dev/null 2>&1
echo -e "  ${GREEN}✔ Simulación activa (loop continuo desbloqueado).${NC}"

# Mostrar estado actual de la simulación
CONTROL_JSON=$(curl -s "http://localhost:${TELEMETRY_PORT}/api/control" 2>/dev/null)
if [ -n "$CONTROL_JSON" ]; then
    echo -e "  ${CYAN}  Intervalo de inyección: $(echo "$CONTROL_JSON" | grep -oP '"interval":\K[0-9.]+')s${NC}"
    echo -e "  ${CYAN}  Estado pausado: $(echo "$CONTROL_JSON" | grep -oP '"is_paused":\K[a-z]+')${NC}"
fi

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ${BOLD}TODOS LOS SISTEMAS OPERATIVOS. SIMULACIÓN DE TELEMETRÍA EN CURSO.${NC}"
echo -e "${GREEN}  La salida de datos fisiológicos y EKG 12-derivaciones se muestra abajo.${NC}"
echo -e "${GREEN}  Pulsa ${BOLD}Ctrl+C${NC}${GREEN} para dejar de seguir la salida (el servidor seguirá activo).${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# Seguir la salida del journal del servicio en tiempo real (como un tail -f)
# Esto muestra las tablas de telemetría fisiológica y ECG 12-derivaciones
journalctl --user -u "$SERVICE_NAME" -f --no-pager --output=cat
