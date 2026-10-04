import asyncio
import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from backup_manager import BackupManager
from google_drive_client import GoogleDriveClient


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.config = {"backup": {"retention_days": 7}, "google": {"remote": "gdrive:Backups/Paperless"}}

    def client(self):
        with patch("shutil.which", return_value="/usr/bin/rclone"):
            return GoogleDriveClient(self.config, self.logger)

    def test_verified_upload_keeps_local_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backup.tar.gz"
            path.write_bytes(b"backup")
            client = self.client()
            client._run = Mock(side_effect=["", json.dumps({"Size": 6, "Hashes": {"md5": hashlib.md5(b"backup").hexdigest()}})])
            asyncio.run(client.upload_file(str(path)))
            self.assertTrue(path.exists())

    def test_bad_or_missing_checksum_fails_and_keeps_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backup.tar.gz"
            path.write_bytes(b"backup")
            for metadata in [{"Size": 6}, {"Size": 6, "Hashes": {"MD5": "wrong"}}]:
                client = self.client()
                client._run = Mock(side_effect=["", json.dumps(metadata)])
                with self.assertRaises(RuntimeError):
                    asyncio.run(client.upload_file(str(path)))
                self.assertTrue(path.exists())

    def test_retention_only_matches_backups_in_target_folder(self):
        client = self.client()
        old = "paperless_backup_2000-01-01_00-00-00.tar.gz"
        unrelated = "notes.tar.gz"
        entries = [{"Name": old, "Path": old}, {"Name": unrelated, "Path": unrelated},
                   {"Name": old, "Path": "nested/" + old},
                   {"Name": "paperless_backup_2000-99-99_00-00-00.tar.gz", "Path": "paperless_backup_2000-99-99_00-00-00.tar.gz"}]
        client._run = Mock(side_effect=[json.dumps(entries), ""])
        client._cleanup()
        self.assertEqual(client._run.call_count, 2)
        self.assertEqual(client._run.call_args.args, ("deletefile", "gdrive:Backups/Paperless/" + old))

    def test_archive_has_dump_and_configured_data(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "media"
            data.mkdir()
            (data / "document.pdf").write_bytes(b"document")
            config = {"backup": {"db_container": "db", "db_name": "paperless", "db_user": "user", "db_password": "secret", "output_dir": str(Path(directory) / "output"), "data_dirs": [str(data)]}}
            manager = BackupManager(config, self.logger)
            manager._create_db_dump = lambda path: Path(path).write_bytes(b"dump")
            archive = manager.run_backup()
            with tarfile.open(archive) as stream:
                self.assertIn("db_dump/paperless_db.dump", stream.getnames())
                self.assertIn("media/document.pdf", stream.getnames())
            config["backup"]["data_dirs"] = [str(Path(directory) / "missing")]
            with self.assertRaises(ValueError):
                manager.run_backup()
            self.assertEqual(len(list(Path(config["backup"]["output_dir"]).glob("*.tar.gz"))), 1)


if __name__ == "__main__":
    unittest.main()
