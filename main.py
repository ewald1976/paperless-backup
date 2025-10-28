#!/usr/bin/env python3
from config_loader import ConfigLoader
from backup_manager import BackupManager
from rich.console import Console

console = Console()

def main():
    console.print("[bold amber3]Paperless-Backup – Hybrid-Version[/bold amber3]")
    loader = ConfigLoader()
    config = loader.load()

    manager = BackupManager(config)
    archive_path = manager.run_backup()
    if archive_path:
        manager.show_summary()

if __name__ == "__main__":
    main()

