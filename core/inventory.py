
"""Inventaires SHA-256 Android et locaux."""

import re
import shlex
import subprocess
from pathlib import Path

from core.integrity import IntegrityError, sha256_local

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class InventoryError(Exception):
    """Erreur lors de la création d'un inventaire."""


def android_inventory(serial, source):
    """Construire l'inventaire SHA-256 d'un dossier Android."""
    source = source.rstrip("/")

    if not source.startswith("/sdcard/"):
        raise InventoryError("Source Android non autorisée.")

    result = subprocess.run(
        [
            "adb", "-s", serial, "exec-out",
            "find", source, "-type", "f", "-print0"
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )

    prefix = (source + "/").encode("utf-8")
    inventory = {}

    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue

        if not raw.startswith(prefix):
            raise InventoryError("Chemin Android inattendu.")

        path = raw.decode("utf-8")
        relative = path[len(source) + 1:]

        command = f"sha256sum {shlex.quote(path)}"

        try:
            digest_result = subprocess.run(
                ["adb", "-s", serial, "shell", command],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            OSError,
        ) as error:
            raise InventoryError(
                f"Calcul SHA-256 impossible : {path}"
            ) from error

        digest = digest_result.stdout.split(maxsplit=1)[0]

        if not SHA256_RE.fullmatch(digest):
            raise InventoryError(
                f"Empreinte SHA-256 invalide : {path}"
            )

        inventory[relative] = digest.lower()

    return inventory


def local_inventory(destination):
    """Construire l'inventaire SHA-256 d'un dossier local."""
    root = Path(destination)

    if not root.is_dir():
        return {}

    inventory = {}

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue

        relative = path.relative_to(root).as_posix()

        try:
            inventory[relative] = sha256_local(path)
        except OSError as error:
            raise InventoryError(
                f"Lecture impossible : {path}"
            ) from error

    return inventory
