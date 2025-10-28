#!/usr/bin/env python3
from config_loader import ConfigLoader
from backup_manager import BackupManager
from dracoon_client import DracoonClient
from logger import JsonLogger
from rich.console import Console
import argparse
import asyncio

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Paperless Backup Tool")
    parser.add_argument("--headless", action="store_true", help="Headless-Modus (für Cronjobs)")
    args = parser.parse_args()

    # 1️⃣ Konfiguration laden
    loader = ConfigLoader()
    config = loader.load()

    # 2️⃣ Logger initialisieren
    logger = JsonLogger(config["backup"]["log_file"], headless=args.headless)
    logger.info("Starte Paperless Backup Tool")

    # 3️⃣ Backup durchführen
    manager = BackupManager(config, logger)
    archive_path = manager.run_backup()

    # 4️⃣ Wenn erfolgreich: Dracoon-Upload & Remote-Cleanup starten
    if archive_path:
        logger.backup_event("Backup abgeschlossen", file=archive_path)
        asyncio.run(upload_and_cleanup(config, logger, archive_path))
    else:
        logger.error("Kein Archiv erstellt – Upload wird übersprungen.")

async def upload_and_cleanup(config, logger, archive_path):
    """Async-Workflow für Upload und Remote-Retention"""
    try:
        client = DracoonClient(config, logger)
        await client.connect()
        await client.upload_file(archive_path)
        await client.cleanup_old_backups()
    except Exception as e:
        logger.error(f"Fehler im Dracoon-Prozess: {e}")

if __name__ == "__main__":
    main()
