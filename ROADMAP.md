# 🧭 Paperless Backup – Roadmap

## 🏷️ Version 2.0.0 (Geplant)

### 🔸 1. Multi‑Provider‑Support
Ziel: Auswahl des Speicherdienstes über `.env`:

```
PROVIDER=dracoon | owncloud | google | s3
```

**Geplante Provider:**
| Provider | SDK / API | Status |
|-----------|------------|--------|
| 🟢 Dracoon | `dracoon` | läuft |
| 🟡 OwnCloud / NextCloud | `owncloud` SDK | geplant |
| 🟡 Google Drive | `google-api-python-client` | geplant |
| ⚪ S3-kompatibel (z. B. MinIO, Wasabi) | `boto3` | optional |

---

### 🔸 2. Interaktiver Installer / Setup‑Wizard
Ein optionaler `install.py`, der:
- `.env`‑Parameter abfragt (Provider, Credentials, Pfade, Retention)
- systemd‑Service & Timer automatisch erstellt
- Logrotate optional einrichtet
- Docker‑Container erkennt und automatisch zur Auswahl anbietet

---

### 🔸 3. Automatischer Container‑Finder
Das Setup sucht nach laufenden Paperless‑Containern:
```
docker ps --format "{{.Names}}" | grep paperless
```
und bietet gefundene Namen zur Auswahl an (z. B. `paperless-db-1`).

---

### 🔸 4. Erweiterte Text‑GUI (Bernstein‑Look)
Ziele:
- Übersicht der letzten Backups
- Anzeige von Status, Dauer, Größe, CRC
- Manuelle Auslösung von Backups
- Provider‑Verwaltung
- Fortschrittsanzeige & Log‑Viewer

---

### 🔸 5. Modularer Codeaufbau
Einheitliches Interface für alle Provider:
```python
storage = StorageFactory.create(provider_name, config, logger)
await storage.upload_file(backup_file)
await storage.cleanup_old_backups()
```

---

### 🔸 6. Paketierung & Distribution
- Option für `pipx install paperless-backup`
- Optionaler Binary‑Build über PyInstaller
- Einheitliche CLI:
  ```bash
  paperless-backup install
  paperless-backup run
  paperless-backup gui
  ```

---

## 💡 Version 3.x (Langfristige Ideen)
- Remote‑Status‑Dashboard (Weboberfläche)
- HA‑Benachrichtigung via REST‑Webhook
- Differential‑Backups
- Verschlüsselung lokaler Archive
