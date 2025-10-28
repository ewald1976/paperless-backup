import os
import tarfile
import subprocess
import shutil
import signal
import sys

from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress
from rich.table import Table

console = Console()

class BackupManager:
    """Verwaltet Dump, Archivierung und Löschung lokaler Backups."""

def __init__(self, config):
        self.cfg = config["backup"]
        self.temp_dir = self.cfg.get("temp_dir", "/tmp/paperless_backup")
        self.output_dir = self.cfg["output_dir"]
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self._partial_files = []  # -> Liste für laufende Dateien

        # Signal-Handler (z.B. STRG+C)
        signal.signal(signal.SIGINT, self._handle_interrupt)

    def _handle_interrupt(self, signum, frame):
        console.print("[red]\n✖ Backup abgebrochen – räume auf...[/red]")
        self._cleanup_partials()
        sys.exit(1)

    def _cleanup_partials(self):
        for f in self._partial_files:
            if os.path.exists(f):
                console.print(f"[yellow]→ Entferne unvollständige Datei:[/yellow] {f}")
                os.remove(f)
    def run_backup(self):
        console.print("[cyan]Starte Paperless-Backup[/cyan]")
        dump_file = os.path.join(self.temp_dir, "paperless_db.dump")
        archive_path = None

        try:
            self._pg_dump(dump_file)
            archive_path = self._create_archive(dump_file)
            console.print(f"[green]✓ Backup erfolgreich erstellt:[/green] {archive_path}")
        except Exception as e:
            console.print(f"[red]Fehler während des Backups:[/red] {e}")
        finally:
            if os.path.exists(dump_file):
                os.remove(dump_file)

        self._cleanup_old_backups()
        return archive_path

    def _pg_dump(self, dump_file):
        container_name = self.cfg.get("db_container")
        if not container_name:
            raise ValueError("Kein 'db_container' in der Konfiguration angegeben.")

        cmd = [
            "bash", "-c",
            f"docker exec -i {container_name} pg_dump -U {self.cfg['db_user']} -d {self.cfg['db_name']} -F c > {dump_file}"
        ]

        result = subprocess.run(cmd, shell=False)
        if result.returncode != 0:
            raise RuntimeError(f"pg_dump im Container fehlgeschlagen (Exitcode {result.returncode})")


    def _create_archive(self, dump_file):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_name = f"paperless_backup_{timestamp}.tar.gz"
        archive_path = os.path.join(self.cfg["output_dir"], archive_name)

        console.print("[yellow]→ Komprimiere Daten...[/yellow]")
        with Progress() as progress:
            task = progress.add_task("Archivieren", total=None)
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(dump_file, arcname=os.path.basename(dump_file))
                for path in self.cfg["data_dirs"]:
                    if os.path.exists(path):
                        tar.add(path, arcname=os.path.basename(path))
            progress.update(task, completed=1)
        return archive_path

    def _cleanup_old_backups(self):
        retention = int(self.cfg.get("retention_days", 7))
        cutoff = datetime.now() - timedelta(days=retention)
        output_dir = self.cfg["output_dir"]

        for f in os.listdir(output_dir):
            path = os.path.join(output_dir, f)
            if os.path.isfile(path):
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    console.print(f"[red]→ Lösche altes Backup:[/red] {f}")
                    os.remove(path)

    def show_summary(self):
        table = Table(title="📦 Lokale Backups")
        table.add_column("Datei")
        table.add_column("Größe (MB)", justify="right")
        table.add_column("Datum")

        for f in sorted(os.listdir(self.cfg["output_dir"])):
            path = os.path.join(self.cfg["output_dir"], f)
            if os.path.isfile(path):
                size = os.path.getsize(path) / 1024 / 1024
                date = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
                table.add_row(f, f"{size:.2f}", date)
        console.print(table)

