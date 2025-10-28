# 🗂️ Paperless Backup Tool

Automatisches Backup-Tool für [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx),  
entwickelt in **Python**, mit **Upload zu Dracoon** und optionaler **automatischer Ausführung via systemd**.

Das Tool erstellt vollständige Backups bestehend aus:
- PostgreSQL-Datenbank-Dump  
- Paperless-Daten- und Medienverzeichnissen  
- Komprimiertem Archiv im `.tar.gz`-Format  
- Automatischem Upload in einen definierten Dracoon-Datenraum  
- Optionaler Entfernung älterer Backups gemäß Retention-Einstellung  

---

## 🚀 Funktionen

- 🔄 Vollautomatisiertes Offsite-Backup über die Dracoon-API  
- 🧮 CRC32-Prüfung nach Upload (Integritätssicherung)  
- 🧹 Automatische Bereinigung alter Backups (konfigurierbare Aufbewahrungszeit)  
- 🪶 Headless-Modus für Cron oder systemd-Timer  
- 🧾 JSON-Logging mit Zeitstempel und Ereignistyp (einfach auswertbar, z. B. in Home Assistant)  
- 🧱 Optional interaktive Konsolen-GUI im Retro-Stil (Bernsteinfarben)  

---

## 📦 Voraussetzungen

- **Linux-System** mit `docker` und `systemd`
- **Python 3.11+**
- `pg_dump` (im Container verfügbar)
- Zugriff auf einen **Dracoon-Account** mit gültigem API-Client (Password-Flow aktiviert)

---

## ⚙️ Installation

### 1️⃣ Repository klonen

```bash
git clone https://github.com/<user>/paperless-backup.git
cd paperless-backup
```

### 2️⃣ Python-Umgebung einrichten

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ Konfiguration anpassen

Erstelle oder bearbeite die Datei `.env` im Projektverzeichnis:

```dotenv
# Paperless Backup Configuration
DB_CONTAINER=paperless-db-1
DB_NAME=paperless
DB_USER=paperless
DB_PASSWORD=paperless

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

---

## ▶️ Nutzung

### Manuell:

```bash
source venv/bin/activate
python main.py --headless
```

### Mit GUI (interaktiv):

```bash
python main.py
```

---

## ⚙️ Automatischer Start via systemd

Paperless-Backup kann automatisch über **systemd** ausgeführt werden,  
anstatt per Cron. Die Systemd-Units (`paperless-backup.service` und `paperless-backup.timer`)  
liegen im Verzeichnis [`systemd/`](systemd/).

### Einrichtung

1. Passe in `systemd/paperless-backup.service` folgende Werte an:
   ```ini
   User=<user>
   WorkingDirectory=<path-to-your-paperless-backup>
   ExecStart=<path-to-your-paperless-backup>/venv/bin/python <path-to-your-paperless-backup>/main.py --headless
   EnvironmentFile=<path-to-your-paperless-backup>/.env
   ```

2. Installiere und aktiviere die Units:
   ```bash
   sudo cp systemd/paperless-backup.* /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now paperless-backup.timer
   ```

3. Prüfe den Status:
   ```bash
   systemctl list-timers | grep paperless
   journalctl -u paperless-backup -f
   ```

> Standardmäßig wird das Backup täglich um **03:00 Uhr** ausgeführt.  
> Wenn das System zu dieser Zeit aus war, wird der Lauf beim nächsten Start nachgeholt (`Persistent=true`).

---

## 🧹 Aufräumen alter Backups

- Alte Backups werden anhand des Dateinamens erkannt  
  (`paperless_backup_YYYY-MM-DD_HH-MM-SS.tar.gz`)
- Dateien, die älter sind als der konfigurierte Zeitraum (`RETENTION_DAYS`),  
  werden automatisch aus Dracoon entfernt
- Andere Dateien im Zielraum bleiben unberührt

---

## 🧾 Log-Format

Das Tool schreibt strukturierte JSON-Logs, z. B.:

```json
{"timestamp": "2025-10-28T18:23:03", "event": "UPLOAD_EVENT", "message": "CRC32 validiert – lösche lokale Datei"}
```

Diese Logs können z. B. in Home Assistant oder Grafana visualisiert werden.

---

## 🧩 Projektstruktur

```
paperless-backup/
├── main.py
├── backup_manager.py
├── dracoon_client.py
├── config_loader.py
├── logger.py
├── requirements.txt
├── .env (lokal, nicht im Git)
└── systemd/
    ├── paperless-backup.service
    └── paperless-backup.timer
```

---

## 🧠 Zukunftsplanung

- 🔔 Integration mit Home Assistant (Webhook bei Erfolg/Fehler)  
- 🧰 Konfigurierbarer `target_path` in Dracoon  
- 📊 Dashboard-Widget zur Backup-Übersicht  
- 🪶 Erweiterte GUI mit Status- und Fortschrittsanzeige  

---

## 📦 Deinstallation

```bash
sudo systemctl disable --now paperless-backup.timer
sudo rm /etc/systemd/system/paperless-backup.*
sudo systemctl daemon-reload
```

---

© 2025 – Paperless Backup Tool (Python + Dracoon API)  
Maintainer: [GitHub.com/ewald1976](https://github.com/ewald1976)
