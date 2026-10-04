import os
from dotenv import load_dotenv

class ConfigLoader:
    """Lädt Konfiguration aus .env Datei."""

    def __init__(self):
        load_dotenv()

    def load(self):
        config = {
            "db": {
                "host": os.getenv("DB_HOST", "localhost"),
                "name": os.getenv("DB_NAME", "paperless"),
                "user": os.getenv("DB_USER", "paperless"),
                "password": os.getenv("DB_PASSWORD", "paperless"),
            },
            "backup": {
                "retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", os.getenv("RETENTION_DAYS", "7"))),
                "offsite": self._boolean("OFFSITE", "true"),
                "provider": os.getenv("PROVIDER", "dracoon").lower(),
                "data_dirs": [p.strip() for p in os.getenv("BACKUP_DATA_DIRS", "/data/data,/data/media,/data/consume,/data/export").split(",") if p.strip()],
                "output_dir": os.getenv("BACKUP_OUTPUT_DIR", "./output"),
                "log_file": os.getenv("BACKUP_LOG_FILE", os.getenv("LOG_FILE", "./backup.log")),
                "db_container": os.getenv("DB_CONTAINER", "paperless-db-1"),
            },
            "google": {
                "remote": os.getenv("GOOGLE_DRIVE_REMOTE", "gdrive:Backups/Paperless"),
                "rclone_config": os.getenv("RCLONE_CONFIG"),
            },
            "dracoon": {
                "base_url": os.getenv("DRACOON_BASE_URL"),
                "client_id": os.getenv("DRACOON_CLIENT_ID"),
                "client_secret": os.getenv("DRACOON_CLIENT_SECRET"),
                "username": os.getenv("DRACOON_USERNAME"),
                "password": os.getenv("DRACOON_PASSWORD"),
                "target_path": os.getenv("DRACOON_TARGET_PATH", "/Backups/Paperless/"),
            },
        }

        # Kompatibilitäts-Aliase, falls ältere Codeteile db_* Keys erwarten
        config["backup"].update({
            "db_host": config["db"]["host"],
            "db_name": config["db"]["name"],
            "db_user": config["db"]["user"],
            "db_password": config["db"]["password"],
        })

        if config["backup"]["retention_days"] < 1:
            raise ValueError("RETENTION_DAYS muss mindestens 1 sein")
        if not config["backup"]["data_dirs"]:
            raise ValueError("BACKUP_DATA_DIRS darf nicht leer sein")
        if config["backup"]["offsite"]:
            if config["backup"]["provider"] not in {"dracoon", "google"}:
                raise ValueError("PROVIDER muss dracoon oder google sein")
            if config["backup"]["provider"] == "dracoon":
                missing = [key for key in ("base_url", "client_id", "client_secret", "username", "password") if not config["dracoon"][key]]
                if missing:
                    raise ValueError("Fehlende Dracoon-Konfiguration: " + ", ".join(missing))
        return config

    @staticmethod
    def _boolean(name, default):
        value = os.getenv(name, default).lower()
        if value not in {"true", "false"}:
            raise ValueError(f"{name} muss true oder false sein")
        return value == "true"
