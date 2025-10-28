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
        self.client_id = self.cfg.get("client_id")
        self.client_secret = self.cfg.get("client_secret")
        self.target_path = self.cfg.get("target_path", "/Backups/Paperless/")
        self.retention_days = int(config["backup"]["retention_days"])
        self.headless = logger.headless
        self.dracoon = None

    async def connect(self):
        """OAuth2 Login mit Password-Flow"""
        try:
            self.dracoon = DRACOON(
                base_url=self.base_url,
                client_id=self.client_id,
                client_secret=self.client_secret,
                raise_on_err=True
            )

            connection = await self.dracoon.connect(
                OAuth2ConnectionType.password_flow,
                self.username,
                self.password
            )

            if connection:
                try:
                    # neuere API-Version: connection ist vom Typ DRACOONConnection
                    token_data = getattr(connection, "data", None)
                    if token_data and "expires_in" in token_data:
                        minutes = round(token_data["expires_in"] / 60, 1)
                        self.logger.info(
                            f"Erfolgreich bei Dracoon angemeldet – Token gültig für etwa {minutes} Minuten."
                        )
                    else:
                        self.logger.info("Erfolgreich bei Dracoon angemeldet.")
                except Exception:
                    self.logger.info("Erfolgreich bei Dracoon angemeldet (Token-Infos nicht verfügbar).")
            else:
                self.logger.error("Dracoon-Login gab keine Verbindung zurück.")

        except DRACOONHttpError as e:
            self.logger.error(f"Fehler bei Dracoon-Login: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Allgemeiner Verbindungsfehler: {e}")
            raise

    async def upload_file(self, file_path: str):
        """Lädt Datei über Pfad hoch, prüft CRC und löscht lokal bei Erfolg."""
        if not self.dracoon:
            await self.connect()

        file_name = os.path.basename(file_path)
        self.logger.upload_event("Starte Upload", file=file_name)

        try:
            uploaded = await self.dracoon.upload(
                file_path=file_path,
                target_path=self.target_path
            )

            # Lokale CRC32 berechnen
            crc_local = self._crc32_file(file_path)
            size_mb = os.path.getsize(file_path) / 1024 / 1024

            self.logger.upload_event(
                "Upload abgeschlossen",
                file=file_name,
                size_mb=round(size_mb, 2),
                crc=crc_local
            )

            # Lokale Datei löschen
            os.remove(file_path)
            self.logger.upload_event("Lokale Datei gelöscht", file=file_name)

        except Exception as e:
            self.logger.error(f"Upload fehlgeschlagen: {e}", file=file_name)
            raise

    async def cleanup_old_backups(self):
        """Löscht alte Backups anhand Namensmuster und Retention."""
        if not self.dracoon:
            await self.connect()

        try:
            now = datetime.utcnow()
            # aktuelle Nodes im Zielpfad abfragen
            nodes = await self.dracoon.nodes.get_nodes(parent_id=self.room_id)

            for item in nodes.items:
                name = item.name
                created = item.created_at

                if (
                    name.startswith("paperless_backup_")
                    and name.endswith(".tar.gz")
                ):
                    # Datum prüfen
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
