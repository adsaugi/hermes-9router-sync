#!/bin/bash
set -e

# Installer for hermes-9router-sync
if [ "$(id -u)" -ne 0 ]; then
    echo "[!] Please run this installer as root or with sudo."
    exit 1
fi

HERMES_USER="xs"
HERMES_HOME="/home/${HERMES_USER}/.hermes"
INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Installing hermes-9router-sync..."

# 1. Setup target directories
mkdir -p "${HERMES_HOME}/scripts"

# 2. Copy script
cp "${INSTALL_DIR}/sync_9router_models.py" "${HERMES_HOME}/scripts/sync_9router_models.py"
chown -R ${HERMES_USER}:${HERMES_USER} "${HERMES_HOME}/scripts"
chmod +x "${HERMES_HOME}/scripts/sync_9router_models.py"

# 3. Copy CLI wrapper
cp "${INSTALL_DIR}/bin/sync-9router-hermes" "/usr/local/bin/sync-9router-hermes"
chmod +x "/usr/local/bin/sync-9router-hermes"

# 4. Copy systemd units
cp "${INSTALL_DIR}/systemd/hermes-9router-sync.service" "/etc/systemd/system/hermes-9router-sync.service"
cp "${INSTALL_DIR}/systemd/hermes-9router-sync.timer" "/etc/systemd/system/hermes-9router-sync.timer"

# 5. Reload and activate systemd
systemctl daemon-reload
systemctl enable --now hermes-9router-sync.timer

echo "==> Installation complete!"
echo "==> Timer status:"
systemctl status hermes-9router-sync.timer --no-pager -l

echo ""
echo "==> Running initial test sync:"
su - ${HERMES_USER} -c "sync-9router-hermes -v"