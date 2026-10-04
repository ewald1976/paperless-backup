import os
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.errors import DRACOONHttpError


class DracoonClient:
    """Verwaltet Dracoon-Uploads unter Beibehaltung des lokalen Archivs."""

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
        """Lädt die Datei hoch und behält das lokale Archiv."""
        if not self.dracoon:
            await self.connect()

        file_name = os.path.basename(file_path)
        self.logger.upload_event("Starte Upload", file=file_name)

        try:
            await self.dracoon.upload(file_path=file_path, target_path=self.target_path)

            self.logger.upload_event(
                "Dracoon-Upload abgeschlossen; Archiv bleibt lokal (keine Remote-Prüfsumme verifiziert)",
                file=file_name,
            )

        except Exception as e:
            self.logger.error(f"Upload fehlgeschlagen: {e}", file=file_name)
            raise

    async def cleanup_old_backups(self):
        """Löscht alte Backups anhand Namensmuster und Retention."""
        self.logger.info(
            "Dracoon-Retention deaktiviert: Die bisherige globale Suche ist nicht sicher auf den Zielordner begrenzt."
        )
