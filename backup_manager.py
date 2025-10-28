import os
import subprocess
from datetime import datetime


class BackupManager:
    """Verwaltet Erstellung des Paperless-Datenbankdumps."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_conf = config["db"]
        self.backup_conf = config["backup"]

    def create_db_dump(self) -> str:
        """Erstellt einen PostgreSQL-Dump innerhalb des angegebenen Containers."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dump_dir = "/tmp/paperless_backup"
        os.makedirs(dump_dir, exist_ok=True)

        dump_path = os.path.join(dump_dir, f"paperless_db_{timestamp}.dump")

        container = self.backup_conf["db_container"]
        db_name = self.db_conf["name"]
        db_user = self.db_conf["user"]

        cmd = [
            "docker",
            "exec",
            "-t",
            container,
            "pg_dump",
            "-U", db_user,
            "-d", db_name,
            "-F", "c",
            "-f", dump_path,
        ]

        self.logger.info(f"→ Führe Datenbankdump im Container {container} aus...")

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            self.logger.info("→ Datenbankdump erfolgreich abgeschlossen.")
            return dump_path

        except subprocess.CalledProcessError as e:
            self.logger.error(f"pg_dump fehlgeschlagen: {e.stderr.strip()}")
            raise Exception("Fehler beim Erstellen des Datenbankdumps")

        except Exception as e:
            self.logger.error(f"Allgemeiner Fehler beim Dump: {e}")
            raise
