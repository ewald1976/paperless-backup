import os
import zlib
import asyncio
from datetime import datetime, timedelta
from dracoon import DRACOON
from dracoon.errors import DRACOONHttpError


class DracoonClient:
    """Verwaltet Upload, CRC-Prüfung und Remote-Retention im Dracoon-Space."""

    def __init__(self, config, logger):
        self.cfg = config["dracoon"]
        self.logger = logger
        self.base_url = self.cfg["base_url"].rstrip("/")
        self.username = self.cfg["username"]
        self.password = self.cfg["password"]
        self.client_id = self.cfg.get("client_id")
        self.client_secret = self.cfg.get("client_secret")
        self.room_id = int(self.cfg["target_room_id"])
        self.retention_days = int(config["backup"]["retention_days"])
        self.headless = logger.headless
        self.dracoon = None

    async def connect(self):
        """OAuth2 Login mit aktueller Dracoon-PyPI-Version."""
        try:
            self.dracoon = DRACOON(base_url=self.base_url, raise_on_err=True)
        await self.dracoon.connect(
            username=self.username,
            password=self.password,
            client_id=self.client_id,
            client_secret=self.client_secret,
            grant_type="password"
            )       

            self.logger.info("Erfolgreich bei Dracoon angemeldet.")
        except DRACOONHttpError as e:
            self.logger.error(f"Fehler bei Dracoon-Login: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Allgemeiner Verbindungsfehler: {e}")
            raise

    async def upload_file(self, file_path: str):
        """Lädt Datei hoch, prüft CRC, löscht lokal bei Erfolg."""
        if not self.dracoon:
            await self.connect()

        file_name = os.path.basename(file_path)
        self.logger.upload_event("Starte Upload", file=file_name)

        try:
            upload = await self.dracoon.nodes.upload_file(
                file_path=file_path, target_id=self.room_id
            )

            # Lokale CRC32 berechnen
            crc_local = self._crc32_file(file_path)
            # Remote-Hash abrufen (kann None sein, daher optional)
            crc_remote = getattr(upload, "hash", None)
            self.logger.upload_event("Upload abgeschlossen", file=file_name, crc=crc_remote)

            # Vergleich
            if crc_remote and crc_local == crc_remote:
                size_mb = os.path.getsize(file_path) / 1024 / 1024
                self.logger.upload_event(
                    "CRC32 erfolgreich validiert – lösche lokale Datei",
                    file=file_name,
                    size_mb=round(size_mb, 2),
                    crc=crc_local,
                )
                os.remove(file_path)
            else:
                self.logger.error(
                    f"CRC32-Fehler oder kein Remote-Hash! Lokal={crc_local}, Remote={crc_remote}",
                    file=file_name,
                )
                # Remote-Datei löschen, um inkonsistente Uploads zu vermeiden
                await self.dracoon.nodes.delete_node(upload.id)

        except Exception as e:
            self.logger.error(f"Upload fehlgeschlagen: {e}", file=file_name)
            raise

    async def cleanup_old_backups(self):
        """Löscht alte Backups anhand Namensmuster und Retention."""
        if not self.dracoon:
            await self.connect()

        try:
            now = datetime.utcnow()
            result = await self.dracoon.nodes.get_room_nodes(room_id=self.room_id)
            for item in result.items:
                name = item.name
                created = item.created_at
                if (
                    name.startswith("paperless_backup_")
                    and name.endswith(".tar.gz")
                    and created < (now - timedelta(days=self.retention_days))
                ):
                    self.logger.delete_event("Lösche altes Remote-Backup", file=name)
                    await self.dracoon.nodes.delete_node(item.id)
                else:
                    self.logger.info(f"Überspringe Datei im Dracoon-Raum: {name}")

        except Exception as e:
            self.logger.error(f"Fehler bei Remote-Cleanup: {e}")

    def _crc32_file(self, path: str) -> str:
        """Berechnet CRC32 Prüfsumme."""
        prev = 0
        with open(path, "rb") as f:
            for line in f:
                prev = zlib.crc32(line, prev)
        return f"{prev & 0xFFFFFFFF:08x}"
