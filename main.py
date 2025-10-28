import os
import asyncio
from datetime import datetime
from backup_manager import BackupManager
from config_loader import ConfigLoader
from logger import JsonLogger
from dracoon_client import DracoonClient


def main():
    print("🗂️  Paperless Backup – Version 1.0.2")

    # Konfiguration laden
    loader = ConfigLoader()
    config = loader.load()

    # Logger initialisieren
    logger = JsonLogger(config["backup"]["log_file"], headless=True)
    logger.info("Starte Paperless Backup Tool")

    try:
        manager = BackupManager(config, logger)
        archive_path = manager.run_backup()

        if not archive_path:
            logger.error("Kein Archiv erstellt – Upload wird übersprungen.")
            return

        offsite = str(config.get("backup", {}).get("offsite", "true")).lower() == "true"

        if offsite:
            logger.info("Offsite-Upload aktiviert. Starte Dracoon-Prozess...")
            dracoon = DracoonClient(config, logger)
            asyncio.run(dracoon.upload_file(archive_path))
            asyncio.run(dracoon.cleanup_old_backups())
        else:
            logger.info("Offsite-Upload deaktiviert. Backup bleibt lokal gespeichert.")

    except Exception as e:
        logger.error(f"Fehler während des Backups: {e}")

    finally:
        logger.backup_event("Backup-Prozess beendet")


if __name__ == "__main__":
    main()
