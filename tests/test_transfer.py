
"""Tests de préparation sécurisée des transferts."""

import hashlib
import tempfile
import unittest
from pathlib import Path

from core.transfer import (
    TransferError,
    safe_target,
    stage_file,
    install_new_file,
)


class TestTransfer(unittest.TestCase):

    def test_safe_path(self):
        with tempfile.TemporaryDirectory() as directory:
            target = safe_target(
                directory,
                "DCIM/Camera/photo.jpg",
            )
            self.assertEqual(
                target,
                Path(directory) / "DCIM/Camera/photo.jpg",
            )

    def test_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TransferError):
                safe_target(directory, "../photo.jpg")

    def test_absolute_path_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TransferError):
                safe_target(directory, "/tmp/photo.jpg")

    def test_staged_file_sha256(self):
        content = b"fichier de test"
        digest = hashlib.sha256(content).hexdigest()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jpg"
            source.write_bytes(content)

            temporary, target = stage_file(
                root,
                "DCIM/photo.jpg",
                source,
                digest,
            )

            self.assertTrue(temporary.is_file())
            self.assertFalse(target.exists())
            self.assertEqual(
                temporary.read_bytes(),
                content,
            )

    def test_bad_sha256_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jpg"
            source.write_bytes(b"contenu")

            with self.assertRaises(TransferError):
                stage_file(
                    root,
                    "DCIM/photo.jpg",
                    source,
                    "0" * 64,
                )


    def test_install_new_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temporary = root / ".photo.part"
            target = root / "photo.jpg"

            temporary.write_bytes(b"photo test")

            install_new_file(temporary, target)

            self.assertEqual(target.read_bytes(), b"photo test")
            self.assertFalse(temporary.exists())

    def test_existing_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temporary = root / ".photo.part"
            target = root / "photo.jpg"

            temporary.write_bytes(b"nouveau contenu")
            target.write_bytes(b"ancienne sauvegarde")

            with self.assertRaises(TransferError):
                install_new_file(temporary, target)

            self.assertEqual(
                target.read_bytes(),
                b"ancienne sauvegarde",
            )


if __name__ == "__main__":
    unittest.main()
