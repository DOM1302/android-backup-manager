
"""Tests du planificateur incrémental."""

import unittest

from core.backup import plan_incremental_backup, summarize_plan


class TestBackupPlan(unittest.TestCase):

    def test_incremental_plan(self):
        android_files = {
            "DCIM/photo_recente.jpg": "a" * 64,
            "DCIM/photo_existante.jpg": "b" * 64,
            "Download/document.pdf": "c" * 64,
        }

        local_files = {
            "DCIM/photo_existante.jpg": "b" * 64,
            "Download/document.pdf": "d" * 64,
            "DCIM/ancienne_photo.jpg": "e" * 64,
        }

        plan = plan_incremental_backup(
            android_files, local_files
        )

        actions = {
            item["path"]: item["action"]
            for item in plan
        }

        self.assertEqual(
            actions["DCIM/photo_recente.jpg"], "copy"
        )
        self.assertEqual(
            actions["DCIM/photo_existante.jpg"], "skip"
        )
        self.assertEqual(
            actions["Download/document.pdf"], "version"
        )
        self.assertEqual(
            actions["DCIM/ancienne_photo.jpg"], "keep"
        )

        self.assertEqual(
            summarize_plan(plan),
            {
                "copy": 1,
                "skip": 1,
                "version": 1,
                "keep": 1,
            },
        )

    def test_empty_inventories(self):
        self.assertEqual(
            plan_incremental_backup({}, {}),
            [],
        )


if __name__ == "__main__":
    unittest.main()
