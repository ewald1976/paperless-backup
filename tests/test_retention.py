import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from retention import cleanup_local_backups


class RetentionTests(unittest.TestCase):
    def test_only_expired_archives_deleted_and_current_kept(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            now = datetime(2026, 10, 4, 12)
            def archive(days, suffix=''):
                name = 'paperless_backup_' + (now - timedelta(days=days)).strftime('%Y-%m-%d_%H-%M-%S') + suffix + '.tar.gz'
                p = root / name
                p.write_bytes(b'backup')
                return p
            old = archive(15)
            boundary = archive(14)
            recent = archive(13, '_123456')
            current = archive(30)
            foreign = root / 'notes.tar.gz'; foreign.write_bytes(b'notes')
            invalid = root / 'paperless_backup_2026-99-99_00-00-00.tar.gz'; invalid.write_bytes(b'invalid')
            link = root / 'paperless_backup_2000-01-01_00-00-00.tar.gz'; link.symlink_to(foreign)
            nested = root / 'nested'; nested.mkdir()
            nested_backup = nested / old.name; nested_backup.write_bytes(b'backup')
            with patch('retention.datetime') as clock:
                clock.now.return_value = now
                clock.strptime.side_effect = datetime.strptime
                cleanup_local_backups({'backup': {'output_dir': folder, 'local_retention_days': 14}}, Mock(), current)
            self.assertFalse(old.exists())
            for p in (boundary, recent, current, foreign, invalid, link, nested_backup):
                self.assertTrue(p.exists(), str(p))

    def test_upload_failure_does_not_run_local_cleanup(self):
        import sys
        import types
        dotenv = types.ModuleType('dotenv'); dotenv.load_dotenv = Mock()
        logger_module = types.ModuleType('logger'); logger_module.JsonLogger = Mock()
        with patch.dict(sys.modules, {'dotenv': dotenv, 'logger': logger_module}):
            import main
        config = {'backup': {'log_file': 'backup.log', 'offsite': True}}
        with patch.object(main, 'ConfigLoader') as loader, patch.object(main, 'JsonLogger'), patch.object(main, 'BackupManager') as manager, patch.object(main.asyncio, 'run', side_effect=RuntimeError('upload failed')), patch.object(main, 'upload_backup', new=Mock(return_value=None)), patch.object(main, 'cleanup_local_backups') as cleanup, patch.object(sys, 'argv', ['main.py', '--headless']):
            loader.return_value.load.return_value = config
            manager.return_value.run_backup.return_value = 'backup.tar.gz'
            self.assertEqual(main.main(), 1)
            cleanup.assert_not_called()
