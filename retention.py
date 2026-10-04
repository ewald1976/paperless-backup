"""Retention for backup archives directly inside the configured output directory."""
import re
from datetime import datetime, timedelta
from pathlib import Path

BACKUP_PATTERN = re.compile(r"paperless_backup_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})(?:_\d{6})?\.tar\.gz")


def cleanup_local_backups(config, logger, current_archive):
    """Run only after a successful backup/upload; always keep the current archive."""
    output = Path(config["backup"]["output_dir"])
    cutoff = datetime.now() - timedelta(days=config["backup"]["local_retention_days"])
    current = Path(current_archive).resolve()
    for path in output.iterdir():
        match = BACKUP_PATTERN.fullmatch(path.name)
        if not match or path.is_symlink() or not path.is_file() or path.resolve() == current:
            continue
        try:
            timestamp = datetime.strptime(match[1], "%Y-%m-%d_%H-%M-%S")
        except ValueError:
            continue
        if timestamp < cutoff:
            path.unlink()
            logger.delete_event("Altes lokales Backup entfernt", file=str(path))
