# 🗃️ Paperless-ngx Backup Tool

Ein leichtgewichtiges, modular aufgebautes Python-Tool zum Erstellen und Verwalten von Backups einer **Paperless-ngx**-Installation.  
Das Projekt läuft lokal oder auf einem separaten Server und unterstützt in Zukunft auch **Offsite-Uploads zu Dracoon**.

---

## 🚀 Funktionsübersicht

✅ Erzeugt automatisch:
- PostgreSQL-Datenbank-Dump aus dem Paperless-Container  
- Archiv (`.tar.gz`) der Daten- und Medienverzeichnisse  
- Zeitstempel-basierte Dateinamen (z. B. `paperless_backup_2025-10-28_08-00-00.tar.gz`)  

✅ Bereinigt:
- Alte Backups automatisch nach konfigurierbarer Aufbewahrungszeit  
- Teilweise oder abgebrochene Backups werden zuverlässig entfernt  

✅ Geplant:
- Upload zum Dracoon-Space über `dracoon-python-api`
- Interaktive TUI im Retro-Bernstein-Look (Status, Logs, Upload-Verlauf)
- Build als Standalone-Binary (über PyInstaller)

---

## 🧩 Projektstruktur

```
paperless-backup/
├── main.py               # Einstiegspunkt
├── backup_manager.py     # Logik für Dump, Archivierung, Cleanup
├── config_loader.py      # YAML-Konfiguration
├── backup.yaml           # Einstellungen
├── requirements.txt      # Python-Abhängigkeiten
└── .gitignore
```

---

## ⚙️ Installation

### 1️⃣ Repository klonen
```bash
git clone https://github.com/ewald1976/paperless-backup.git
cd paperless-backup
```

### 2️⃣ Virtuelle Umgebung erstellen
```bash
sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🧾 Beispielkonfiguration (`backup.yaml`)

```yaml
backup:
  db_container: paperless-db-1        # Name des PostgreSQL-Containers
  db_host: localhost
  db_name: paperless
  db_user: paperless
  db_password: paperless
  data_dirs:
    - /data/data
    - /data/media
  temp_dir: /tmp/paperless_backup
  output_dir: /home/elmar/paperless-backup/output
  retention_days: 7
  compression: tar.gz
  log_file: /home/elmar/paperless-backup/backup.log
```

---

## ▶️ Nutzung

Backup starten:
```bash
source venv/bin/activate
python main.py
```

Oder als Cronjob (z. B. täglich 03:00 Uhr):
```bash
0 3 * * * cd /home/elmar/paperless-backup && source venv/bin/activate && python main.py >> /var/log/paperless_backup.log 2>&1
```

---

## 🔒 Aufräumen bei Abbruch

Falls der Backup-Prozess fehlschlägt oder manuell abgebrochen wird (z. B. STRG + C),
werden alle unvollständigen Dateien automatisch entfernt.

---

## ☁️ (Geplant) Offsite-Upload zu Dracoon

In einer späteren Etappe:
- Authentifizierung via `dracoon-python-api`
- Upload des Archivs in konfigurierbaren Datenraum
- Fortschrittsanzeige und automatisches Löschen alter Offsite-Backups

---

## 💡 Lizenz

MIT License  
(c) 2025 ewald1976  

---

## 👨‍💻 Autor

**ewald1976**  
Linux-Spezialist, Homelab-Enthusiast & Automatisierungsfreund  
Projektbegleitung durch **Lt. Commander Data 🤖**
