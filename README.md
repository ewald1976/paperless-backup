# 🗂️ Paperless Backup Tool

Automatisches Backup-Tool für [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx),
entwickelt in **Python**, mit **Upload zu Dracoon** und optionaler **automatischer Ausführung über systemd**.

> ⚠️ **Hinweis:**  
> Dieses Tool ist aktuell **ausschließlich für die Container-Version** von  
> [Paperless-ngx (Docker-Image)](https://github.com/paperless-ngx/paperless-ngx)  
> und für **PostgreSQL-Datenbanken** ausgelegt.  
> Es nutzt Docker-Befehle für den Datenbank-Dump und greift auf Container-Volumes zu.

Das Tool erstellt vollständige Backups bestehend aus:
- PostgreSQL-Datenbank-Dump  
- Paperless-Daten- und Medienverzeichnissen  
- Komprimiertem Archiv im `.tar.gz`-Format  
- Automatischem Upload in einen definierten Dracoon-Datenraum  
- Optionaler Entfernung älterer Backups gemäß Aufbewahrungszeit  

---

## 🚀 Funktionen

- 🔄 Vollautomatisiertes Offsite-Backup über die Dracoon-API  
- 🧮 CRC32-Prüfung nach Upload (Integritätsprüfung)  
- 🧹 Automatische Bereinigung alter Backups  
- 🪶 Headless-Modus für Cron / systemd-Timer  
- 🧾 JSON-Logging mit Zeitstempel und Ereignistyp (z. B. für Home Assistant-Auswertung)

---

## 📦 Voraussetzungen

- **Paperless-ngx** als Docker-Installation  
  → [Offizielles Repository](https://github.com/paperless-ngx/paperless-ngx)  
- **PostgreSQL** als Datenbank (Standard in Paperless-ngx-Docker)  
- **Linux-System** mit `docker` und `systemd`  
- **Python 3.11 oder höher**  
- `pg_dump` (im Paperless-Datenbank-Container verfügbar)  
- Zugriff auf einen **Dracoon-Account** mit aktiviertem Password-Flow-Client  

---

## ⚙️ Installation

### 1️⃣ Repository klonen
```bash
git clone https://github.com/ewald1976/paperless-backup.git
cd paperless-backup
```

### 2️⃣ Python-Umgebung einrichten
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ Konfiguration anlegen
Erstelle eine Datei `.env` im Projektverzeichnis:

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

---

## ▶️ Nutzung

### Manuell starten
```bash
source venv/bin/activate
python main.py --headless
```

### Testweise mit Konsolenausgabe
```bash
python main.py
```

---

## ⚙️ Automatischer Start via systemd

Paperless-Backup kann automatisch über **systemd** ausgeführt werden.  
Die passenden Units (`paperless-backup.service` und `paperless-backup.timer`)  
liegen im Verzeichnis `systemd/`.

### Einrichtung
1. In `systemd/paperless-backup.service` anpassen:
   ```ini
   User=<user>
   WorkingDirectory=<path-to-your-paperless-backup>
   ExecStart=<path-to-your-paperless-backup>/venv/bin/python <path-to-your-paperless-backup>/main.py --headless
   EnvironmentFile=<path-to-your-paperless-backup>/.env
   ```

2. Aktivieren:
   ```bash
   sudo cp systemd/paperless-backup.* /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now paperless-backup.timer
   ```

3. Status prüfen:
   ```bash
   systemctl list-timers | grep paperless
   journalctl -u paperless-backup -f
   ```

> Standardmäßig läuft das Backup täglich um **03:00 Uhr**.  
> Wenn das System zu diesem Zeitpunkt aus war, wird der Lauf beim nächsten Start nachgeholt (`Persistent=true`).

---

## 🧹 Bereinigung alter Backups

- Alte Backups werden am Dateinamen erkannt (`paperless_backup_YYYY-MM-DD_HH-MM-SS.tar.gz`)  
- Dateien, die älter sind als `RETENTION_DAYS`, werden aus Dracoon gelöscht  
- Andere Dateien im Zielordner bleiben unangetastet

---

## 🧾 Log-Format

Das Tool erzeugt strukturierte JSON-Logs, z. B.:

```json
{"timestamp": "2025-10-28T18:23:03", "event": "UPLOAD_EVENT", "message": "CRC32 validiert – lösche lokale Datei"}
```

Diese können z. B. von Home Assistant oder Grafana verarbeitet werden.

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
├── .env        # lokale Konfiguration (nicht im Git)
└── systemd/
    ├── paperless-backup.service
    └── paperless-backup.timer
```

---

## 🔮 Ausblick (Version 2.0)

- Unterstützung weiterer Provider (OwnCloud, Google Drive, S3 usw.)  
- Interaktiver Installer / Setup-Wizard  
- Optionale GUI im Retro-Look  
- Verbesserte Status- und Log-Ansicht  

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
