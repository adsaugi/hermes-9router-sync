# Hermes 9Router Auto-Sync

Automated two-way model synchronization daemon between **9Router** API Gateway and **Hermes Agent** (`vm101`).

Eliminates the need to manually update `config.yaml` or disk caches whenever new models, combos, or custom providers are added, modified, or removed in 9Router.

---

## Architecture Overview

```text
  ┌──────────────────────────────────────────────┐
  │         9Router (ct107 / VPS Gateway)        │
  │    Endpoint: https://router.xaiserv.my.id    │
  └──────────────────────┬───────────────────────┘
                         │ /v1/models (poll every 30s)
                         ▼
  ┌──────────────────────────────────────────────┐
  │       Hermes Auto-Sync (systemd.timer)       │
  │   /home/xs/.hermes/scripts/sync_9router_models.py
  └──────────────┬───────────────────────────────┘
                 │
        Diff detected? (added / removed)
        ├── Yes ──> 1. Atomically update ~/.hermes/config.yaml
        │           2. Refresh ~/.hermes/provider_models_cache.json
        │           3. Log changes to journalctl
        └── No  ──> 0 disk writes (0 overhead)
```

---

## Features

- **Hands-Free Integration:** Create or delete models/combos in 9Router; Hermes picks them up within 30 seconds automatically.
- **Atomic File Writing:** Writes config via temporary files and `os.replace` to prevent any file corruption during power outages or restarts.
- **Zero Disk Overhead:** If no changes exist on the upstream gateway, zero write operations are performed to preserve SSD/NVMe lifespan.
- **Native Cache Warming:** Keeps `provider_models_cache.json` up to date so the interactive `/model` picker opens instantly without network lag.
- **CLI Wrapper Included:** Run `sync-9router-hermes -v` anytime for instant one-off synchronization.

---

## Repository Structure

```text
hermes-9router-sync/
├── bin/
│   └── sync-9router-hermes          # System-wide CLI command wrapper
├── systemd/
│   ├── hermes-9router-sync.service  # Oneshot systemd execution unit
│   └── hermes-9router-sync.timer    # Periodic systemd timer (30s interval)
├── sync_9router_models.py           # Core Python synchronization engine
├── install.sh                       # One-click installation script
├── uninstall.sh                     # Complete uninstaller script
├── .gitignore
└── README.md                        # Documentation
```

---

## Installation

### 1. Clone this repository
```bash
git clone <your-private-repo-url> hermes-9router-sync
cd hermes-9router-sync
```

### 2. Run the Installer (as root)
```bash
sudo ./install.sh
```

The installer will:
1. Copy the script to `~/.hermes/scripts/sync_9router_models.py`.
2. Link the CLI command to `/usr/local/bin/sync-9router-hermes`.
3. Install and enable the systemd timer (`hermes-9router-sync.timer`).
4. Execute an initial sync test.

---

## Verification & Usage

### Check Background Timer Status
```bash
systemctl status hermes-9router-sync.timer
```

### View Real-Time Logs
```bash
journalctl -u hermes-9router-sync.service -f
```

### Run Manual Sync Instantly
```bash
sync-9router-hermes -v
```

Output example:
```text
[SYNC] OK: 27 models synced from 9Router (added: 1, removed: 0)
[SYNC] Added: ['Zcombo2']
```

---

## Uninstallation

To cleanly remove all services, timers, and scripts:
```bash
sudo ./uninstall.sh
```

---

## License & Privacy
Private documentation and internal infrastructure tooling.