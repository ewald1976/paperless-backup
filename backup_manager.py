import os
import tarfile
import subprocess
import tempfile
from datetime import datetime


class BackupManager:
    def __init__(self, config, logger):
        self.cfg = config
        self.logger = logger
        self.db_container = self.cfg["backup"]["db_container"]
        self.db_name = self.cfg["backup"]["db_name"]
        self.db_user = self.cfg["backup"]["db_user"]
        self.db_password = self.cfg["backup"]["db_password"]
        self.output_dir = os.path.abspath(self.cfg["backup"]["output_dir"])
        os.makedirs(self.output_dir, exist_ok=True)

    def run_backup(self):
        """Führt den vollständigen Backup-Prozess aus."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
        backup_name = f"paperless_backup_{timestamp}.tar.gz"
        backup_path = os.path.join(self.output_dir, backup_name)
        temporary = tempfile.TemporaryDirectory(prefix="paperless_backup_")
        tmp_dir = temporary.name

        os.makedirs(tmp_dir, exist_ok=True)
        db_dump_path = os.path.join(tmp_dir, "paperless_db.dump")

        self.logger.backup_event("Backup gestartet")

        try:
            names = [os.path.basename(os.path.normpath(d)) for d in self.cfg["backup"]["data_dirs"]]
            if len(names) != len(set(names)) or "db_dump" in names:
                raise ValueError("Backup-Verzeichnisse benötigen eindeutige Namen außer db_dump")
            for directory in self.cfg["backup"]["data_dirs"]:
                if not os.path.isdir(directory):
                    raise ValueError(f"Backup-Verzeichnis fehlt: {directory}")
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
            temporary.cleanup()

    def _create_db_dump(self, dump_path):
        """Streamt den Dump direkt auf den Host, ohne temporäre Containerdatei."""
        self.logger.info(f"Erstelle Datenbankdump im Container {self.db_container}")
        env = os.environ.copy()
        env["PGPASSWORD"] = self.db_password
        command = ["docker", "exec", "-e", "PGPASSWORD", self.db_container,
                   "pg_dump", "-U", self.db_user, "-d", self.db_name, "-F", "c"]
        with open(dump_path, "wb") as stream:
            subprocess.run(command, stdout=stream, env=env, check=True)
        if os.path.getsize(dump_path) == 0:
            raise RuntimeError("Leerer Datenbankdump")

    def _create_archive(self, tmp_dir, backup_path):
        """Erstellt ein komprimiertes tar.gz-Archiv."""
        data_dirs = self.cfg["backup"]["data_dirs"]
        self.logger.info("→ Komprimiere Daten...")
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add(tmp_dir, arcname="db_dump")
            for d in data_dirs:
                if os.path.exists(d):
                    tar.add(d, arcname=os.path.basename(d))
        return backup_path
