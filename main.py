#!/usr/bin/env python3
from config_loader import ConfigLoader
from backup_manager import BackupManager
from logger import JsonLogger
from rich.console import Console
import argparse

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Paperless Backup Tool")
    parser.add_argument("--headless", action="store_true", help="Headless-Modus (für Cronjobs)")
    args = parser.parse_args()

    loader = ConfigLoader()
    config = loader.load()

    logger = JsonLogger(config["backup"]["log_file"], headless=args.headless)

    logger.info("Starte Paperless Backup Tool", headless=args.headless)

    manager = BackupManager(config, logger)
    archive_path = manager.run_backup()

    if archive_path:
        logger.backup_event("Backup abgeschlossen", file=archive_path)

if __name__ == "__main__":
    main()
