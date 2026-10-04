import argparse
import asyncio
import sys

from backup_manager import BackupManager
from config_loader import ConfigLoader
from logger import JsonLogger


async def upload_backup(config, logger, archive):
    if config["backup"]["provider"] == "google":
        from google_drive_client import GoogleDriveClient
        storage = GoogleDriveClient(config, logger)
    else:
        from dracoon_client import DracoonClient
        storage = DracoonClient(config, logger)
    await storage.upload_file(archive)
    await storage.cleanup_old_backups()


def main():
    parser = argparse.ArgumentParser(description="Paperless-Backup mit Dracoon oder Google Drive")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    logger = None
    try:
        config = ConfigLoader().load()
        logger = JsonLogger(config["backup"]["log_file"], headless=args.headless)
        archive = BackupManager(config, logger).run_backup()
        if not archive:
            raise RuntimeError("Kein Archiv erstellt")
        if config["backup"]["offsite"]:
            asyncio.run(upload_backup(config, logger, archive))
        else:
            logger.info("Offsite deaktiviert; Backup bleibt lokal gespeichert.")
        logger.backup_event("Backup erfolgreich abgeschlossen", file=archive)
        return 0
    except Exception as error:
        if logger:
            logger.error(f"Backup fehlgeschlagen: {error}")
        print(f"Backup fehlgeschlagen: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
