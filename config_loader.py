import yaml
import os
from rich.console import Console

console = Console()

class ConfigLoader:
    """Lädt und validiert die YAML-Konfiguration."""

    def __init__(self, path="backup.yaml"):
        self.path = path
        self.config = None

    def load(self):
        if not os.path.exists(self.path):
            console.print(f"[red]Fehler:[/red] Konfigurationsdatei {self.path} nicht gefunden.")
            raise FileNotFoundError(self.path)

        with open(self.path, "r") as f:
            self.config = yaml.safe_load(f)

        self._validate()
        return self.config

    def _validate(self):
        if "backup" not in self.config:
            raise ValueError("Fehlender Abschnitt: 'backup'")
        required = ["db_host", "db_name", "db_user", "db_password", "data_dirs", "output_dir"]
        for key in required:
            if key not in self.config["backup"]:
                raise ValueError(f"Fehlender Parameter in backup: {key}")

