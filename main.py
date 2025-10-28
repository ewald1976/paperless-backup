import os
import tarfile
import argparse
import io
from datetime import datetime
from config_loader import ConfigLoader
from dracoon_client import DracoonClient
from logger import JsonLogger
from backup_manager import BackupManager


def main():
    parser = argparse.ArgumentParser(description="Paperless Backup Tool")
    parser.add_argument("--headless", action="store_true", help="Headless mode (no interactive UI)")
    args = parser.parse_args()

    # --- Konfiguration laden ---
    loader = ConfigLoader()
    config = loader.load()

    # --- Logger initialisieren ---
    logger = JsonLogger(config["backup"]["log_file"], headless=args.headless)
    logger.info("Starte Paperless Backup Tool")

    # --- Feste Datenverzeichnisse ---
    data_dirs = [
        "/data/data",
        "/data/media",
        "/data/export",
        "/data/consume",
    ]

    try:
        backup_mgr = BackupManager(config, logger)
        logger.backup_event("Backup gestartet")

        # --- Datenbankdump im Container erstellen ---
        logger.info(f"→ Erstelle Datenbankdump im Container {config['backup']['db_container']} ...")
        db_dump_path = backup_mgr.create_db_dump()

        # --- Archiv erstellen ---
        logger.info("Komprimiere Daten...")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_dir = config["backup"]["output_dir"]
        os.makedirs(output_dir, exist_ok=True)

        archive_name = f"paperless_backup_{timestamp}.tar.gz"
        archive_path = os.path.join(output_dir, archive_name)

        with tarfile.open(archive_path, "w:gz") as tar:
            # --- Stream: Datenbankdump direkt aus dem Container lesen ---
            logger.info("→ Füge Datenbankdump aus Container hinzu ...")
            container = config["backup"]["db_container"]
            stream_cmd = f"docker exec {container} cat {db_dump_path}"
            dump_bytes = os.popen(stream_cmd).buffer.read()

            if dump_bytes:
                tarinfo = tarfile.TarInfo(name=os.path.basename(db_dump_path))
                tarinfo.size = len(dump_bytes)
                tar.addfile(tarinfo, io.BytesIO(dump_bytes))
                logger.info(f"→ Dump erfolgreich ins Archiv integriert: {os.path.basename(db_dump_path)}")
            else:
                raise Exception("Leerer Dump-Stream erhalten (pg_dump fehlgeschlagen?)")

            # --- Datenverzeichnisse hinzufügen ---
            for d in data_dirs:
                if os.path.exists(d):
                    tar.add(d, arcname=os.path.basename(d))
                else:
                    logger.info(f"Überspringe nicht vorhandenes Verzeichnis: {d}")

        logger.backup_event("Backup erfolgreich erstellt", file=archive_path)
        logger.backup_event("Backup abgeschlossen", file=archive_path)

        # --- Upload zu Dracoon ---
        dracoon_client = DracoonClient(config, logger)
        import asyncio
        asyncio.run(dracoon_client.upload_file(archive_path))
        asyncio.run(dracoon_client.cleanup_old_backups())

    except Exception as e:
        logger.error(f"Fehler während des Backups: {e}")
        if "archive_path" in locals() and os.path.exists(archive_path):
            os.remove(archive_path)
            logger.delete_event("Entferne unvollständige Datei")
        logger.error("Kein Archiv erstellt – Upload wird übersprungen.")

    finally:
        logger.backup_event("Backup-Prozess beendet")


if __name__ == "__main__":
    main()
