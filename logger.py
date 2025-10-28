import json
import os
from datetime import datetime
from rich.console import Console
from rich.text import Text

console = Console()

class JsonLogger:
    """
    Kombinierter JSON- und Konsolenlogger für Paperless Backup Tool.
    Schreibt strukturierte Logs für spätere Auswertung in HA / Grafana.
    """

    def __init__(self, log_file: str, headless: bool = False):
        self.log_file = log_file
        self.headless = headless
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

    def _timestamp(self):
        return datetime.now().isoformat(timespec="seconds")

    def log(self, event: str, message: str, **kwargs):
        """Zentrale Logfunktion"""
        entry = {
            "timestamp": self._timestamp(),
            "event": event,
            "message": message,
            **kwargs
        }

        # JSON-Dateilog
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False)
                f.write("\n")
        except Exception as e:
            console.print(f"[red]Fehler beim Schreiben der Logdatei:[/red] {e}")

        # Konsolenausgabe (falls nicht headless)
        if not self.headless:
            color = self._color_for_event(event)
            text = Text(f"[{entry['timestamp']}] {event.upper():<18} {message}", style=color)
            console.print(text)

    def _color_for_event(self, event: str) -> str:
        """Einheitliche Farbzuordnung nach Ereignistyp"""
        if "error" in event:
            return "red"
        if "upload" in event or "backup" in event:
            return "green"
        if "delete" in event or "cleanup" in event:
            return "yellow"
        return "cyan"

    def info(self, message: str, **kwargs):
        self.log("info", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log("error", message, **kwargs)

    def backup_event(self, message: str, **kwargs):
        self.log("backup_event", message, **kwargs)

    def upload_event(self, message: str, **kwargs):
        self.log("upload_event", message, **kwargs)

    def delete_event(self, message: str, **kwargs):
        self.log("delete_event", message, **kwargs)
