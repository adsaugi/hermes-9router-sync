#!/bin/bash
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "[!] Please run this uninstaller as root or with sudo."
    exit 1
fi

echo "==> Stopping and disabling systemd timer & service..."
systemctl stop hermes-9router-sync.timer 2>/dev/null || true
systemctl disable hermes-9router-sync.timer 2>/dev/null || true
systemctl stop hermes-9router-sync.service 2>/dev/null || true

rm -f /etc/systemd/system/hermes-9router-sync.service
rm -f /etc/systemd/system/hermes-9router-sync.timer
systemctl daemon-reload

rm -f /usr/local/bin/sync-9router-hermes
rm -f /home/xs/.hermes/scripts/sync_9router_models.py

echo "==> hermes-9router-sync has been completely removed."