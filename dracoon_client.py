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
        self.room_id = int(self.cfg["target_room_id"])
        self.retention_days = int(config["backup"]["retention_days"])
        self.headless = logger.headless
        self.dracoon = None

    async def connect(self):
        """OAuth2 Login mit aktuellem Password-Flow (Octavio-API)"""
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

            # nur wenn connection zurückkommt, Token-Infos ausgeben
            if connection:
                try:
                    token_info = connection.json()
                    expires_in = token_info.get("expires_in")
                    if expires_in:
                        minutes = round(expires_in / 60, 1)
                        self.logger.info(
                            f"Erfolgreich bei Dracoon angemeldet – Token gültig für etwa {minutes} Minuten."
                        )
                    else:
                        self.logger.info("Erfolgreich bei Dracoon angemeldet.")
                except Exception:
                    # falls das Objekt keine json()-Methode hat
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
            # Zielpfad im Dracoon-Raum (aktuell statisch, später konfigurierbar)
            target_path = self.cfg.get("target_path", "/Backup/")

            # Upload durchführen – ohne encrypt-Parameter
            uploaded = await self.dracoon.upload(
                file_path=file_path,
                target_path=target_path
            )

            # CRC prüfen
            crc_local = self._crc32_file(file_path)
            size_mb = os.path.getsize(file_path) / 1024 / 1024

            self.logger.upload_event(
                "Upload abgeschlossen",
                file=file_name,
                size_mb=round(size_mb, 2),
                crc=crc_local
            )

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
