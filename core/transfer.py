
"""Installation sécurisée de fichiers sauvegardés."""

import hashlib
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath


class TransferError(Exception):
    """Erreur de transfert ou d'intégrité."""


def sha256(path):
    digest = hashlib.sha256()

    with open(path, "rb") as stream:
        for block in iter(
            lambda: stream.read(1024 * 1024), b""
        ):
            digest.update(block)

    return digest.hexdigest()


def safe_target(root, relative):
    """Empêcher les chemins de sortir du dossier cible."""
    path = PurePosixPath(relative)

    if (
        not relative
        or path.is_absolute()
        or any(part in ("", ".", "..") for part in relative.split("/"))
        or "\\" in relative
    ):
        raise TransferError(f"Chemin interdit : {relative!r}")

    root = Path(root).resolve(strict=True)
    target = root.joinpath(*path.parts)

    # Refuser les liens symboliques existants.
    current = root

    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise TransferError("Lien symbolique interdit.")

    if not target.resolve().is_relative_to(root):
        raise TransferError("Destination hors du dossier autorisé.")

    return target


def stage_file(root, relative, source, expected_sha256):
    """
    Préparer un fichier temporaire vérifié.

    Le fichier final n'est pas encore remplacé.
    """
    root = Path(root).resolve(strict=True)
    target = safe_target(root, relative)

    target.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary = tempfile.mkstemp(
        prefix=".abm-",
        suffix=".part",
        dir=target.parent,
    )
    os.close(fd)
    temporary = Path(temporary)

    try:
        shutil.copyfile(source, temporary)

        actual = sha256(temporary)

        if actual != expected_sha256.lower():
            raise TransferError(
                f"SHA-256 différent pour {relative}"
            )

        return temporary, target

    except Exception:
        temporary.unlink(missing_ok=True)
        raise




def install_new_file(temporary, target):
    """Installer un nouveau fichier vérifié, sans écrasement volontaire."""
    temporary = Path(temporary)
    target = Path(target)

    if temporary.is_symlink() or not temporary.is_file():
        raise TransferError("Fichier temporaire invalide.")

    if target.is_symlink():
        raise TransferError("Destination symbolique interdite.")

    if temporary.parent.resolve() != target.parent.resolve():
        raise TransferError(
            "Le temporaire doit être dans le dossier cible."
        )

    # Réservation exclusive du nom définitif.
    try:
        fd = os.open(
            target,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        os.close(fd)
    except FileExistsError as exc:
        raise TransferError(
            f"Destination déjà occupée : {target}"
        ) from exc

    try:
        with open(temporary, "rb") as stream:
            os.fsync(stream.fileno())

        os.replace(temporary, target)

    except Exception as exc:
        # Ne pas effacer une destination dont l'état est incertain.
        raise TransferError(
            f"Installation incomplète : {target}"
        ) from exc
