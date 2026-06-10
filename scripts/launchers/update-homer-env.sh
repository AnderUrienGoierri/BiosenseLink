#!/bin/bash
# ================================================================
# update-homer-env.sh  — Auto-update Homer footer with host OS name
# No sudo required · User systemd service
# ================================================================

CONFIG="/home/ander/dev/infra/homer-dashboard-assets/config.yml"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME="${PRETTY_NAME:-${NAME:-Unknown OS}}"
else
    OS_NAME="Unknown OS"
fi

if [ ! -f "$CONFIG" ]; then
    echo "[WARN] Config not found: $CONFIG"
    exit 0
fi

# Use python3 to safely replace the footer line (avoids sed special char issues)
python3 - "$CONFIG" "$OS_NAME" << 'PYEOF'
import sys, re

config_path = sys.argv[1]
os_name     = sys.argv[2]

with open(config_path, 'r') as f:
    content = f.read()

new_footer = f"footer: '<p>Biomedical Hub \u00a9 2026 | Entorno de Desarrollo y Simulaci\u00f3n Cl\u00ednico | {os_name}</p>'"
content = re.sub(r'^footer:.*', new_footer, content, flags=re.MULTILINE)

with open(config_path, 'w') as f:
    f.write(content)

print(f"[OK] Homer footer updated: {os_name}")
PYEOF

echo "[$(date '+%H:%M:%S')] Homer footer updated → ${OS_NAME}"
