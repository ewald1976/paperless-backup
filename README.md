# Paperless Backup Tool

Python-Tool für PostgreSQL-Dumps und Paperless-Verzeichnisse als `.tar.gz`,
mit optionalem Upload zu **Dracoon oder Google Drive**.

## Installation

Voraussetzungen: Python 3.11+, Docker mit PostgreSQL-Container und Zugriff auf
die Paperless-Verzeichnisse auf dem Host. Für Google Drive zusätzlich `rclone`.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Konfiguration

Passe `.env` an deine Installation an:

```dotenv
DB_CONTAINER=paperless-db-1
DB_NAME=paperless
DB_USER=paperless
DB_PASSWORD=paperless
BACKUP_DATA_DIRS=/data/data,/data/media,/data/consume,/data/export
BACKUP_OUTPUT_DIR=./output
OFFSITE=true
PROVIDER=dracoon
RETENTION_DAYS=7
LOG_FILE=backup.log
```

`BACKUP_DATA_DIRS` enthält kommagetrennte **Host-Pfade**, keine Container-Pfade.
Alle angegebenen Verzeichnisse müssen existieren. Optional nicht vorhandene
Consume-/Export-Verzeichnisse aus der Liste entfernen. Fehlende Pfade brechen
das Backup ab, damit kein unvollständiges Archiv als erfolgreich gemeldet wird.
Verzeichnisnamen müssen eindeutig sein, weil sie im Archiv als Basename erscheinen.

`OFFSITE=false` erstellt nur das lokale Archiv und benötigt keine Cloud-Zugangsdaten.
`PROVIDER=dracoon` bleibt der Standard. `BACKUP_RETENTION_DAYS` und
`BACKUP_LOG_FILE` werden ebenfalls unterstützt und haben Vorrang vor den alten Namen.

### Google Drive

1. Installiere [rclone](https://rclone.org/install/).
2. Führe `rclone config` **als den Benutzer des späteren Backup-Dienstes** aus.
3. Lege einen Remote namens `gdrive` vom Typ Google Drive an und autorisiere ihn
   per OAuth im Browser. Für Server ohne Browser siehe
   [rclone-Einrichtung auf einem entfernten Rechner](https://rclone.org/remote_setup/).
4. Setze in `.env`:

```dotenv
OFFSITE=true
PROVIDER=google
GOOGLE_DRIVE_REMOTE=gdrive:Backups/Paperless
# Optional, besonders bei systemd: absoluter Konfigurationspfad
RCLONE_CONFIG=/home/your-user/.config/rclone/rclone.conf
# Bei Installation nur für den Benutzer (systemd findet ~/.local/bin oft nicht):
RCLONE_BINARY=/home/your-user/.local/bin/rclone
```

Teste den Zugang mit `rclone lsd gdrive:`. Die rclone-Konfiguration enthält
OAuth-Tokens: nur für den Dienstbenutzer lesbar halten und nicht ins Repository aufnehmen.
Verwende einen dedizierten Backup-Ordner und einen gewöhnlichen Drive-Remote.

Der Upload vergleicht die lokale MD5-Prüfsumme und Dateigröße mit den von Drive
zurückgelieferten Werten. Fehlende oder abweichende Prüfsummen führen zum Fehler.
Siehe [rclone Google Drive](https://rclone.org/drive/) und
[lsjson mit Prüfsummen](https://rclone.org/commands/rclone_lsjson/).

Nach verifiziertem Upload werden nur unmittelbar im Zielordner liegende Dateien
mit dem Muster `paperless_backup_YYYY-MM-DD_HH-MM-SS[_ffffff].tar.gz` bereinigt.
Das Datum im Dateinamen entscheidet über `RETENTION_DAYS`; Unterordner und andere
Dateinamen bleiben erhalten. Standardmäßig verschiebt rclone Drive-Dateien in den
Papierkorb. Keine Einstellung `use_trash=false` verwenden, wenn das gewünscht ist.

### Dracoon

Setze `PROVIDER=dracoon` und die `DRACOON_*`-Werte aus `.env.example`.
Der bisherige SDK-Upload bleibt bestehen. Eine Remote-Prüfsumme wird hier derzeit
**nicht verifiziert**. Die bisherige globale Remote-Bereinigung ist deaktiviert,
weil sie Dateien außerhalb des Zielordners erfassen konnte.

## Ausführen

```bash
python main.py
python main.py --headless
```

Fehler liefern Exit-Code 1, Erfolg Exit-Code 0. JSON-Logs stehen in `LOG_FILE`.
Lokale Archive bleiben auch nach erfolgreichem Upload erhalten. Es gibt derzeit
keine automatische lokale Bereinigung; Speicherbedarf entsprechend einplanen.
Starte keine parallelen Backupläufe.

Die Dateien werden während des laufenden Paperless-Betriebs gelesen. Für einen
konsistenten Stand Schreibzugriffe/Importer während des gesamten Backups pausieren.
Die Archive sind nicht zusätzlich verschlüsselt. Vor produktivem Einsatz einen
Restore in einer separaten Installation testen: Dump mit `pg_restore` einspielen,
Verzeichnisse zurückkopieren und Paperless-Version sowie Besitzerrechte beachten.
Deployment-Konfiguration und Secrets separat sichern.

## systemd

Passe `User`, `WorkingDirectory`, `ExecStart` und `EnvironmentFile` in
`systemd/paperless-backup.service` an, bevor du die Units installierst.
Der Benutzer benötigt Docker-, Verzeichnis- und gegebenenfalls rclone-Zugriff.

```bash
sudo cp systemd/paperless-backup.service systemd/paperless-backup.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now paperless-backup.timer
```

Der Timer läuft täglich um 03:00 Uhr und holt ausgefallene Läufe nach.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Die Tests verwenden simulierte Cloud-Aufrufe; echte Cloud-Uploads und Restore
müssen mit deiner Installation geprüft werden.
