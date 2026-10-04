"""Google Drive uploads using an OAuth remote configured with rclone."""
import asyncio
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_PATTERN = re.compile(r"paperless_backup_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})(?:_\d{6})?\.tar\.gz")


class GoogleDriveClient:
    def __init__(self, config, logger):
        self.logger = logger
        self.remote = config["google"]["remote"].rstrip("/")
        self.retention_days = config["backup"]["retention_days"]
        if not re.match(r"^[\w-]+:", self.remote):
            raise ValueError("GOOGLE_DRIVE_REMOTE muss ein rclone-Ziel wie gdrive:Backups/Paperless sein")
        binary = config["google"].get("rclone_binary", "rclone")
        if not shutil.which(binary):
            raise RuntimeError("rclone fehlt. Bitte installieren und mit 'rclone config' Google Drive einrichten.")
        self.command = [binary]
        if config["google"].get("rclone_config"):
            self.command += ["--config", config["google"]["rclone_config"]]

    def _run(self, *arguments):
        result = subprocess.run(self.command + list(arguments), check=True,
                                capture_output=True, text=True)
        return result.stdout

    def _target(self, name):
        return self.remote + ("" if self.remote.endswith(":") else "/") + name

    async def upload_file(self, file_path):
        return await asyncio.to_thread(self._upload, file_path)

    def _upload(self, file_path):
        path = Path(file_path)
        target = self._target(path.name)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "md5").hexdigest()
        self.logger.upload_event("Starte Google-Drive-Upload", file=path.name)
        self._run("copyto", str(path), target, "--checksum")
        metadata = json.loads(self._run("lsjson", target, "--stat", "--hash"))
        remote_hash = metadata.get("Hashes", {}).get("MD5", "")
        if metadata.get("Size") != path.stat().st_size or remote_hash.lower() != digest:
            raise RuntimeError("Google-Drive-Prüfsumme oder Dateigröße stimmt nicht überein")
        self.logger.upload_event("Google-Drive-Upload verifiziert; Archiv bleibt lokal", file=path.name, md5=digest)

    async def cleanup_old_backups(self):
        await asyncio.to_thread(self._cleanup)

    def _cleanup(self):
        entries = json.loads(self._run("lsjson", self.remote, "--files-only"))
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for entry in entries:
            name = entry.get("Name", "")
            match = BACKUP_PATTERN.fullmatch(name)
            if not match or entry.get("IsDir") or entry.get("Path") != name:
                continue
            try:
                timestamp = datetime.strptime(match[1], "%Y-%m-%d_%H-%M-%S")
            except ValueError:
                continue
            if timestamp < cutoff:
                self._run("deletefile", self._target(name))
                self.logger.delete_event("Altes Google-Drive-Backup in den Papierkorb verschoben", file=name)
