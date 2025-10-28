# 🧩 Installation & Setup – Paperless Backup Service

Dieses Dokument beschreibt die Installation des automatischen Backup-Systems  
für **Paperless-ngx**, inklusive Upload zu **Dracoon** und täglicher Ausführung über systemd.

---

## 📋 Voraussetzungen

- **Linux-System** mit systemd (z. B. Debian, Ubuntu)
- **Python 3.11+**
- **Virtualenv** aktiv im Projektordner
- Das Repository wurde z. B. nach `/home/<user>/paperless-backup` oder `/opt/paperless-backup` geklont
- Eine gültige `.env`-Datei mit allen Zugangsdaten (siehe unten)
- Docker mit laufendem Paperless-Container

---

## ⚙️ Schritt 1 – Abhängigkeiten installieren

```bash
cd <path-to-your-paperless-backup>
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## ⚙️ Schritt 2 – Systemd-Units bereitstellen

```bash
sudo cp systemd/paperless-backup.* /etc/systemd/system/
sudo systemctl daemon-reload
```

Öffne anschließend die Datei `systemd/paperless-backup.service` und passe folgende Werte an:

```ini
User=<user>
WorkingDirectory=<path-to-your-paperless-backup>
ExecStart=<path-to-your-paperless-backup>/venv/bin/python <path-to-your-paperless-backup>/main.py --headless
EnvironmentFile=<path-to-your-paperless-backup>/.env
```

Beispiel:

```ini
User=paperless
WorkingDirectory=/opt/paperless-backup
```

Dann aktivieren:

```bash
sudo systemctl enable --now paperless-backup.timer
```

---

## ⏰ Schritt 3 – Automatische Ausführung (Timer)

Standardmäßig wird das Backup **täglich um 03:00 Uhr** ausgeführt.  
Wenn der Rechner zu dieser Zeit ausgeschaltet war, holt systemd den Lauf beim nächsten Start nach.

Prüfen:

```bash
systemctl list-timers | grep paperless
```

---

## ▶️ Schritt 4 – Manuell starten / prüfen

Manueller Start:

```bash
systemctl start paperless-backup.service
```

Status und Log:

```bash
journalctl -u paperless-backup -f
```

---

## 🧾 Beispiel – `.env`

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

## 🧹 Hinweise

- Der Dienst löscht **lokale Archive** nach erfolgreichem Upload automatisch.  
- Alte Backups in Dracoon werden anhand des Namensmusters  
  `paperless_backup_YYYY-MM-DD_HH-MM-SS.tar.gz` erkannt und nach Ablauf der Retention entfernt.  
- Im Fehlerfall wird das lokale Archiv **nicht gelöscht**.

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
