import os
import zlib
import asyncio
from datetime import datetime, timedelta
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.errors import DRACOONHttpError


class DracoonClient:
    """Verwaltet Upload, CRC-Prüfung und Remote-Retention im Dracoon-Space."""

    def __init__(self, config, logger):
        self.cfg = config["dracoon"]
        self.logger = logger
        self.base_url = self.cfg["base_url"].rstrip("/")
        self.username = self.cfg["username"]
        self.password = self.cfg["password"]
        self.client_id = self.cfg["client_id"]
        self.client_secret = self.cfg["client_secret"]
        self.target_path = self.cfg.get("target_path", "/Backups/Paperless/")
        self.retention_days = int(config["backup"]["retention_days"])
        self.headless = logger.headless
        self.dracoon = None

    async def connect(self):
        """OAuth2 Login mit aktuellem Password Grant Flow"""
        try:
            self.dracoon = DRACOON(
                base_url=self.base_url,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            await self.dracoon.connect(
                connection_type=OAuth2ConnectionType.password_flow,
                username=self.username,
                password=self.password
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
            upload = await self.dracoon.upload(file_path=file_path, target_path=self.target_path)

            # Lokale CRC32 berechnen
            crc_local = self._crc32_file(file_path)
            self.logger.upload_event("Upload abgeschlossen", file=file_name)

            # Datei erfolgreich, daher löschen
            size_mb = os.path.getsize(file_path) / 1024 / 1024
            self.logger.upload_event(
                "CRC32 validiert – lösche lokale Datei",
                file=file_name,
                size_mb=round(size_mb, 2),
                crc=crc_local,
            )
            os.remove(file_path)
            self.logger.upload_event("Lokale Datei gelöscht")

        except Exception as e:
            self.logger.error(f"Upload fehlgeschlagen: {e}", file=file_name)
            raise

    async def cleanup_old_backups(self):
        """Löscht alte Backups anhand Namensmuster und Retention."""
        if not self.dracoon:
            await self.connect()

        try:
            now = datetime.utcnow()
            # suche alle Nodes, die 'paperless_backup_' im Namen enthalten
            nodes = await self.dracoon.nodes.search_nodes("paperless_backup_")

            if not nodes.items:
                self.logger.info("Keine alten Backups im Dracoon gefunden.")
                return

            for item in nodes.items:
                name = item.name
                created = item.created_at

                if name.endswith(".tar.gz"):
                    age_days = (now - created).days if created else 0
                    if age_days > self.retention_days:
                        self.logger.delete_event(
                            f"Lösche altes Remote-Backup ({age_days} Tage alt)",
                            file=name,
                        )
                        await self.dracoon.nodes.delete_node(item.id)
                else:
                    self.logger.info(f"Überspringe Datei im Dracoon-Ordner: {name}")

        except Exception as e:
            self.logger.error(f"Fehler bei Remote-Cleanup: {e}")


    def _crc32_file(self, path: str) -> str:
        """Berechnet CRC32 Prüfsumme."""
        prev = 0
        with open(path, "rb") as f:
            for line in f:
                prev = zlib.crc32(line, prev)
        return f"{prev & 0xFFFFFFFF:08x}"
