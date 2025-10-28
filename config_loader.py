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
                "retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "7")),
                "output_dir": os.getenv("BACKUP_OUTPUT_DIR", "./output"),
                "log_file": os.getenv("BACKUP_LOG_FILE", "./backup.log"),
                "db_container": os.getenv("DB_CONTAINER", "paperless-db-1"),
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
        return config
