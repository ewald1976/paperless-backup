# 📦 Changelog

Alle wichtigen Änderungen werden hier dokumentiert.
Das Format orientiert sich an [Keep a Changelog](https://keepachangelog.com/de/1.0.0/).

---

## [1.1.0] – 2026-10-04

### Neu
- Google Drive als Backup-Ziel über rclone und `PROVIDER=google`.
- Upload-Verifikation anhand der entfernten MD5-Prüfsumme und Dateigröße.
- Ordnergebundene Google-Drive-Retention über `RETENTION_DAYS`.
- Lokale Retention über `LOCAL_RETENTION_DAYS` (Standard: 14 Tage), nur nach erfolgreichen Läufen.
- Beispielkonfiguration für 14 Tage Aufbewahrung lokal und in Google Drive.
- Konfigurierbare Host-Verzeichnisse und expliziter rclone-Pfad für systemd.

### Behoben
- `OFFSITE=false` wird berücksichtigt; lokale Backups benötigen keine Cloud-Zugangsdaten.
- Fehlende Datenverzeichnisse und leere Datenbankdumps brechen das Backup ab.
- Temporäre Dump-Dateien sind pro Lauf isoliert; Dumps werden direkt aus Docker gestreamt.
- Fehler liefern Exit-Code 1 und enthalten rclone-Diagnosen.
- Logdateien ohne Verzeichnispfad funktionieren.
- Aktuelle rclone-Prüfsummennamen werden unterstützt.

### Geändertes Verhalten
- Lokale Archive werden nach dem Upload behalten und später gemäß Retention bereinigt.
- Dracoon-Retention ist deaktiviert, da die bisherige Suche nicht auf den Zielordner begrenzt war.
- Bei Dracoon wird keine Remote-Prüfsumme verifiziert; die bisherige CRC32-Erfolgsmeldung war unzutreffend.
- Nicht verwendete Python-Abhängigkeiten entfernt; Konsolenausgabe vereinfacht.

### Validierung
- Sechs automatisierte Tests erfolgreich.
- Reales PostgreSQL-/Paperless-Backup mit Google-Drive-Upload, Prüfsummenvergleich und lokaler Bereinigung getestet.
- Wiederherstellung in einer separaten Paperless-Installation noch nicht getestet.

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
