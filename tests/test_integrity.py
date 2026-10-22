
"""Tests du module de vérification SHA-256."""

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.integrity import (
    IntegrityError,
    sha256_local,
    sha256_android,
    verify_file,
)


class TestIntegrity(unittest.TestCase):

    def test_sha256_local(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "photo test.jpg"
            path.write_bytes(b"test android backup")

            expected = hashlib.sha256(
                b"test android backup"
            ).hexdigest()

            self.assertEqual(sha256_local(path), expected)

    @patch("core.integrity.subprocess.run")
    def test_android_filename_with_spaces(self, mock_run):
        digest = "a" * 64
        mock_run.return_value = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f"{digest}  /sdcard/Download/mon fichier.pdf\n",
            stderr="",
        )

        result = sha256_android(
            "TEST_SERIAL",
            "/sdcard/Download/mon fichier.pdf",
        )

        self.assertEqual(result, digest)

        command = mock_run.call_args.args[0]
        self.assertIn(
            "'/sdcard/Download/mon fichier.pdf'",
            command[-1],
        )

    @patch("core.integrity.subprocess.run")
    def test_android_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="adb", timeout=30
        )

        with self.assertRaises(IntegrityError):
            sha256_android(
                "TEST_SERIAL",
                "/sdcard/Download/file.pdf",
            )

    def test_missing_local_file(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.jpg"

            with self.assertRaises(IntegrityError):
                verify_file(
                    "TEST_SERIAL",
                    "/sdcard/DCIM/missing.jpg",
                    missing,
                )

    @patch("core.integrity.sha256_android")
    def test_identical_file(self, mock_sha):
        content = b"photo android"
        mock_sha.return_value = hashlib.sha256(
            content
        ).hexdigest()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "photo.jpg"
            path.write_bytes(content)

            result = verify_file(
                "TEST_SERIAL",
                "/sdcard/DCIM/photo.jpg",
                path,
            )

            self.assertTrue(result["identical"])

    @patch("core.integrity.sha256_android")
    def test_different_file(self, mock_sha):
        mock_sha.return_value = "0" * 64

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "photo.jpg"
            path.write_bytes(b"contenu different")

            result = verify_file(
                "TEST_SERIAL",
                "/sdcard/DCIM/photo.jpg",
                path,
            )

            self.assertFalse(result["identical"])


if __name__ == "__main__":
    unittest.main()
