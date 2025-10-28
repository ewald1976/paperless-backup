# 🗂️ Paperless Backup Tool

Automatisches Backup-Tool für [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx)
entwickelt in **Python**, mit **Upload zu Dracoon** und **optionalem Offsite-Toggle**.

Das Tool erstellt vollständige Backups bestehend aus:
- PostgreSQL-Datenbank-Dump
- Paperless-Daten- und Medienverzeichnissen
- Komprimiertem Archiv im `.tar.gz`-Format
- Optionalem Upload in einen definierten Dracoon-Datenraum
- Automatischer Bereinigung alter Backups gemäß Aufbewahrungszeitraum

---

## 🚀 Funktionen

- 🔄 Vollautomatisiertes Offsite-Backup über die Dracoon-API
- 🧮 CRC32-Prüfung nach Upload (Integritätssicherung)
- 🧹 Automatische Bereinigung alter Backups (konfigurierbar)
- 🪶 Headless-Modus für Cron oder systemd-Timer
- 🟡 Retro-Konsolenmodus im interaktiven Betrieb (Amberfarben)
- 🧾 JSON-Logging mit Zeitstempel und Ereignistyp
- 💾 Lokaler Backup-Only-Modus über `OFFSITE=false`

---

## ⚙️ Voraussetzungen

- **Linux oder macOS** mit `docker` und `systemd` (optional)
- **Python 3.11+**
- `pg_dump` im Container verfügbar
- Zugriff auf einen **Dracoon-Account** mit API-Client (Password-Flow aktiviert)
- Paperless-ngx **Docker-Version mit PostgreSQL**
  → siehe [Paperless-ngx Docker Repository](https://github.com/paperless-ngx/paperless-ngx)

---

## 🧩 Installation

```bash
git clone https://github.com/ewald1976/paperless-backup.git
cd paperless-backup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Konfiguration

Erstelle oder bearbeite die Datei `.env` im Projektverzeichnis:

```dotenv
# Paperless Backup Configuration
DB_CONTAINER=paperless-db-1
DB_NAME=paperless
DB_USER=paperless
DB_PASSWORD=paperless

# Offsite Upload aktivieren (true/false)
OFFSITE=true

# Dracoon Connection
DRACOON_BASE_URL=https://example.dracoon.com
DRACOON_CLIENT_ID=xxxxxxxxxxxxxxxx
DRACOON_CLIENT_SECRET=xxxxxxxxxxxxxxxx
DRACOON_USERNAME=paperless-backup
DRACOON_PASSWORD=topsecret
DRACOON_TARGET_PATH=/Backups/Paperless/

# Backup Settings
RETENTION_DAYS=7
LOG_FILE=backup.log
```

Wenn `OFFSITE=false`, wird **nur ein lokales Backup erstellt**
ohne Dracoon-Upload oder Remote-Cleanup.

---

## ▶️ Nutzung

### Manuell:
```bash
source venv/bin/activate
python main.py
```

### Headless (z. B. für Cron oder systemd):
```bash
python main.py --headless
```

---

## ⚙️ Automatischer Start via systemd

Die Systemd-Units (`paperless-backup.service` und `.timer`)
liegen im Verzeichnis `systemd/`.

Beispiel:

```ini
User=<user>
WorkingDirectory=<path-to-your-paperless-backup>
ExecStart=<path-to-your-paperless-backup>/venv/bin/python <path-to-your-paperless-backup>/main.py --headless
EnvironmentFile=<path-to-your-paperless-backup>/.env
```

Installation:

```bash
sudo cp systemd/paperless-backup.* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now paperless-backup.timer
```

Standardmäßig tägliches Backup um **03:00 Uhr**.
Bei ausgeschaltetem System wird der Lauf nachgeholt (`Persistent=true`).

---

## 🧾 Log-Format

Das Tool schreibt strukturierte JSON-Logs, z. B.:

```json
{"timestamp": "2025-10-29T08:23:03", "event": "UPLOAD_EVENT", "message": "CRC32 validiert – lösche lokale Datei"}
```

Diese Logs können z. B. in **Home Assistant**, **Grafana** oder **Kibana** ausgewertet werden.

---

## 📦 Deinstallation

```bash
sudo systemctl disable --now paperless-backup.timer
sudo rm /etc/systemd/system/paperless-backup.*
sudo systemctl daemon-reload
```

---

© 2025 – Paperless Backup Tool (Python + Dracoon API)
Maintainer: [github.com/ewald1976](https://github.com/ewald1976)
