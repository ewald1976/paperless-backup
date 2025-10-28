# 📦 Changelog

Alle wichtigen Änderungen werden hier dokumentiert.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## 🟡 [1.0.2] – 2025-10-29
### ✨ Added
- `OFFSITE`-Toggle in `.env` für lokalen Backup-Only-Modus
- Amber-Retro-Konsolenmodus mit Banner und Fortschrittsausgabe
- Getrennte Ausgabe für Headless- und Interaktiv-Modus
- Verbesserte JSON-Logik und Fehlerausgabe

### 🧹 Fixed
- Fehlende `run_backup()`-Methode im `BackupManager` ergänzt
- Stabilität beim Datenbankdump und Aufräumen
- Sauberere Fehlerbehandlung im interaktiven Modus

---

## 🟢 [1.0.1] – 2025-10-28
### ✨ Added
- Erstveröffentlichung des Paperless Backup Tools
- Vollständiger Backup-Prozess (PostgreSQL + Datenverzeichnisse)
- Upload zu Dracoon mit CRC32-Prüfung
- Automatische Bereinigung alter Backups
- JSON-Logging und systemd-Integration
