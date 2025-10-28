import subprocess
from datetime import datetime


class BackupManager:
    """Erstellt den Paperless-Datenbankdump direkt im Container."""

    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.db_conf = config["db"]
        self.backup_conf = config["backup"]

    def create_db_dump(self) -> str:
        """Erstellt den Dump im Container und gibt den Pfad dort zurück."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        container = self.backup_conf["db_container"]
        db_name = self.db_conf["name"]
        db_user = self.db_conf["user"]

        dump_path_container = f"/tmp/paperless_db_{timestamp}.dump"

        cmd = [
            "docker", "exec", "-t",
            container,
            "pg_dump",
            "-U", db_user,
            "-d", db_name,
            "-F", "c",
            "-f", dump_path_container
        ]

        self.logger.info(f"→ Erstelle Datenbankdump im Container {container} ...")

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.info(f"→ Dump erfolgreich im Container erstellt: {dump_path_container}")
            return dump_path_container
        except subprocess.CalledProcessError as e:
            self.logger.error(f"pg_dump fehlgeschlagen: {e.stderr.strip() if e.stderr else 'unbekannter Fehler'}")
            raise Exception("Fehler beim Erstellen des Datenbankdumps")
