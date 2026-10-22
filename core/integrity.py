
"""Vérification SHA-256 des sauvegardes Android."""

import hashlib
import re
import shlex
import subprocess
from pathlib import Path


class IntegrityError(Exception):
    """Erreur lors d'une vérification d'intégrité."""


def sha256_local(path):
    """Calculer le SHA-256 d'un fichier sauvegardé."""
    digest = hashlib.sha256()

    with open(path, "rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def sha256_android(serial, path):
    """Calculer le SHA-256 sur Android, avec chemin protégé."""
    command = f"sha256sum {shlex.quote(path)}"

    try:
        result = subprocess.run(
            ["adb", "-s", serial, "shell", command],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired as exc:
        raise IntegrityError(
            f"Délai ADB dépassé pour : {path}"
        ) from exc
    except OSError as exc:
        raise IntegrityError(
            f"Impossible d'exécuter ADB : {exc}"
        ) from exc

    if result.returncode != 0:
        raise IntegrityError(
            f"Erreur SHA-256 Android : "
            f"{result.stderr.strip() or path}"
        )

    match = re.match(
        r"^([0-9a-fA-F]{64})\s",
        result.stdout,
    )

    if not match:
        raise IntegrityError(
            f"Réponse SHA-256 invalide pour : {path}"
        )

    return match.group(1).lower()


def verify_file(serial, android_path, local_path):
    """Comparer les empreintes SHA-256 du téléphone et du SSD."""
    local_path = Path(local_path)

    if not local_path.is_file():
        raise IntegrityError(
            f"Fichier local introuvable : {local_path}"
        )

    remote_hash = sha256_android(serial, android_path)
    local_hash = sha256_local(local_path)

    return {
        "android_path": android_path,
        "local_path": str(local_path),
        "remote_sha256": remote_hash,
        "local_sha256": local_hash,
        "identical": remote_hash == local_hash,
    }
