import os
import tarfile
import subprocess
from datetime import datetime


class BackupManager:
    def __init__(self, config, logger):
        self.cfg = config
        self.logger = logger
        self.db_container = self.cfg["backup"]["db_container"]
        self.db_name = self.cfg["backup"]["db_name"]
        self.db_user = self.cfg["backup"]["db_user"]
        self.db_password = self.cfg["backup"]["db_password"]
        self.output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def run_backup(self):
        """Führt den vollständigen Backup-Prozess aus."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_name = f"paperless_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.output_dir, backup_name)
        tmp_dir = "/tmp/paperless_backup"

        os.makedirs(tmp_dir, exist_ok=True)
        db_dump_path = os.path.join(tmp_dir, "paperless_db.dump")

        self.logger.backup_event("Backup gestartet")

        try:
            # 1️⃣ Datenbankdump im Container
            self._create_db_dump(db_dump_path)

            # 2️⃣ Daten und Medienverzeichnisse packen
            self._create_archive(tmp_dir, backup_path)

            self.logger.backup_event("Backup erfolgreich erstellt", file=backup_path)
            return backup_path

        except Exception as e:
            self.logger.error(f"Fehler während des Backups: {e}")
            if os.path.exists(backup_path):
                self.logger.delete_event("Entferne unvollständige Datei", file=backup_path)
                os.remove(backup_path)
            raise

        finally:
            # Aufräumen
            if os.path.exists(db_dump_path):
                os.remove(db_dump_path)

    def _create_db_dump(self, dump_path):
        """Erstellt einen PostgreSQL-Dump über docker exec."""
        self.logger.info(f"→ Erstelle Datenbankdump im Container {self.db_container} ...")
        try:
            cmd = [
                "docker", "exec", self.db_container,
                "pg_dump",
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "c",
                "-f", "/tmp/paperless_db.dump"
            ]
            subprocess.run(cmd, check=True)

            # Datei aus Container holen
            subprocess.run(["docker", "cp",
                            f"{self.db_container}:/tmp/paperless_db.dump", dump_path],
                           check=True)

            # Dump im Container löschen
            subprocess.run(["docker", "exec", self.db_container, "rm", "-f", "/tmp/paperless_db.dump"],
                           check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error("pg_dump fehlgeschlagen:")
            raise RuntimeError("Fehler beim Erstellen des Datenbankdumps") from e

    def _create_archive(self, tmp_dir, backup_path):
        """Erstellt ein komprimiertes tar.gz-Archiv."""
        data_dirs = [
            "/data/data",
            "/data/media",
            "/data/consume",
            "/data/export"
        ]
        self.logger.info("→ Komprimiere Daten...")
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(tmp_dir, arcname="db_dump")
            for d in data_dirs:
                if os.path.exists(d):
                    tar.add(d, arcname=os.path.basename(d))
        return backup_path
