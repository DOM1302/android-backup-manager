
"""Moteur de sauvegarde Android utilisant ADB."""

import os
import subprocess
from pathlib import Path


class BackupError(Exception):
    """Erreur pendant la préparation ou la sauvegarde."""


def check_destination(destination):
    """Vérifier que la destination est dans le volume /backups."""
    root = Path("/backups")
    dest = Path(destination).resolve()

    if not root.is_mount():
        raise BackupError(
            "/backups n'est pas un volume monté."
        )

    if not dest.is_relative_to(root.resolve()) or dest == root.resolve():
        raise BackupError(
            "La destination doit être un sous-dossier de /backups."
        )

    if not os.access(root, os.W_OK):
        raise BackupError(
            "Le volume de sauvegarde n'est pas accessible en écriture."
        )

    return dest


def check_device(serial):
    """Vérifier que le téléphone est autorisé via ADB."""
    result = subprocess.run(
        ["adb", "-s", serial, "get-state"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0 or result.stdout.strip() != "device":
        raise BackupError("Téléphone non accessible ou non autorisé.")


def backup_directories(serial, directories, destination):
    """Copier les dossiers sélectionnés via ADB."""
    dest = check_destination(destination)
    check_device(serial)

    dest.mkdir(parents=True, exist_ok=True)

    print("\n=== SAUVEGARDE ANDROID ===", flush=True)

    results = []

    for source in directories:
        folder_name = source.rstrip("/").split("/")[-1]
        target = dest / folder_name

        print(f"\nSource : {source}", flush=True)
        print(f"Destination : {target}", flush=True)

        # adb pull crée le sous-dossier source dans dest.
        command = [
            "adb", "-s", serial,
            "pull", "-a", source, str(dest)
        ]

        result = subprocess.run(command)

        results.append({
            "source": source,
            "destination": str(target),
            "success": result.returncode == 0,
        })

        if result.returncode != 0:
            raise BackupError(
                f"Échec du transfert : {source}"
            )

        print(f"Copie terminée : {folder_name}", flush=True)

    return results
