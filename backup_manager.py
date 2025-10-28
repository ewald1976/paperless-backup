import os
import tarfile
import subprocess
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

class BackupManager:
    def __init__(self, config, logger):
        self.cfg = config["backup"]
        self.logger = logger
        self.temp_dir = self.cfg.get("temp_dir", "/tmp/paperless_backup")
        self.output_dir = self.cfg["output_dir"]
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self._partial_files = []

    def run_backup(self):
        self.logger.backup_event("Backup gestartet")
        dump_file = os.path.join(self.temp_dir, "paperless_db.dump")
        archive_path = None

        try:
            self._partial_files.append(dump_file)
            self._pg_dump(dump_file)

            archive_path = self._create_archive(dump_file)
            self._partial_files.append(archive_path)

            self.logger.backup_event("Backup erfolgreich erstellt", file=archive_path)

        except Exception as e:
            self.logger.error(f"Fehler während des Backups: {e}")
            self._cleanup_partials()

        finally:
            if os.path.exists(dump_file):
                os.remove(dump_file)

        self._cleanup_old_backups()
        return archive_path

    def _pg_dump(self, dump_file):
        container_name = self.cfg.get("db_container")
        if not container_name:
            raise ValueError("Kein 'db_container' in der Konfiguration angegeben.")

        self.logger.backup_event(f"Erstelle Datenbankdump im Container {container_name}")

        cmd = [
            "bash", "-c",
            f"docker exec -i {container_name} pg_dump -U {self.cfg['db_user']} -d {self.cfg['db_name']} -F c > {dump_file}"
        ]
        result = subprocess.run(cmd, shell=False)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump im Container fehlgeschlagen (Exitcode {result.returncode})")

        size_mb = os.path.getsize(dump_file) / 1024 / 1024
        self.logger.backup_event("Datenbankdump abgeschlossen", file=dump_file, size_mb=round(size_mb, 2))

    def _create_archive(self, dump_file):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_name = f"paperless_backup_{timestamp}.tar.gz"
        archive_path = os.path.join(self.output_dir, archive_name)
        self.logger.backup_event(f"Erstelle Archiv {archive_name}")

        with Progress() as progress:
            task = progress.add_task("Komprimiere Daten...", total=None)
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(dump_file, arcname=os.path.basename(dump_file))
                for path in self.cfg["data_dirs"]:
                    if os.path.exists(path):
                        tar.add(path, arcname=os.path.basename(path))
            progress.update(task, completed=1)

        size_mb = os.path.getsize(archive_path) / 1024 / 1024
        self.logger.backup_event("Archiv fertiggestellt", file=archive_name, size_mb=round(size_mb, 2))
        return archive_path

    def _cleanup_old_backups(self):
        retention = int(self.cfg.get("retention_days", 7))
        cutoff = datetime.now() - timedelta(days=retention)
        output_dir = self.output_dir

        for f in os.listdir(output_dir):
            path = os.path.join(output_dir, f)
            if not os.path.isfile(path):
                continue
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            if mtime < cutoff:
                if f.startswith("paperless_backup_") and f.endswith(".tar.gz"):
                    self.logger.delete_event("Lösche altes Backup", file=f)
                    os.remove(path)
                else:
                    self.logger.info(f"Überspringe Datei (kein Backup): {f}")

    def _cleanup_partials(self):
        for f in self._partial_files:
            if os.path.exists(f):
                self.logger.delete_event("Entferne unvollständige Datei", file=f)
                os.remove(f)
