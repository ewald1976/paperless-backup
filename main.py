import os
import sys
import asyncio
from datetime import datetime
from backup_manager import BackupManager
from config_loader import ConfigLoader
from logger import JsonLogger
from dracoon_client import DracoonClient

# ANSI-Farben für den Retro-Look
AMBER = "\033[38;5;214m"
RESET = "\033[0m"

def banner(mode_text):
    print(f"{AMBER}╔══════════════════════════════════════════╗{RESET}")
    print(f"{AMBER}║  🗂️  Paperless Backup  v1.0.2            ║{RESET}")
    print(f"{AMBER}║  Mode: {mode_text:<31}                   ║{RESET}")
    print(f"{AMBER}╚══════════════════════════════════════════╝{RESET}\n")

def main():
    headless = "--headless" in sys.argv
    loader = ConfigLoader()
    config = loader.load()

    logger = JsonLogger(config["backup"]["log_file"], headless=headless)
    offsite = str(config.get("backup", {}).get("offsite", "true")).lower() == "true"

    if not headless:
        banner("OFFSITE" if offsite else "LOCAL ONLY")
        print(f"{AMBER}⏳ Starte Backup...{RESET}")

    try:
        manager = BackupManager(config, logger)
        archive_path = manager.run_backup()

        if not archive_path:
            logger.error("Kein Archiv erstellt – Upload wird übersprungen.")
            return

        if offsite:
            if not headless: print(f"{AMBER}☁️  Lade zu Dracoon hoch...{RESET}")
            dracoon = DracoonClient(config, logger)
            asyncio.run(dracoon.upload_file(archive_path))
            asyncio.run(dracoon.cleanup_old_backups())
        else:
            logger.info("Offsite-Upload deaktiviert. Backup bleibt lokal gespeichert.")
            if not headless: print(f"{AMBER}💾 Lokales Backup abgeschlossen.{RESET}")

    except Exception as e:
        logger.error(f"Fehler während des Backups: {e}")
        if not headless:
            print(f"\033[31m❌ Fehler: {e}{RESET}")
    finally:
        logger.backup_event("Backup-Prozess beendet")
        if not headless:
            print(f"{AMBER}✅ Backup abgeschlossen.{RESET}\n")


if __name__ == "__main__":
    main()
