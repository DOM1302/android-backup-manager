
"""Découverte des dossiers Android accessibles via ADB."""

import shlex

from core.adb import run_adb, ADBError


ANDROID_DIRECTORIES = {
    "1": ("Photos et vidéos", "/sdcard/DCIM"),
    "2": ("Images", "/sdcard/Pictures"),
    "3": ("Vidéos", "/sdcard/Movies"),
    "4": ("Téléchargements", "/sdcard/Download"),
    "5": ("Médias des applications", "/sdcard/Android/media"),
}


def directory_exists(serial, path):
    """Vérifie l'existence d'un dossier sur Android."""

    command = f"if test -d {shlex.quote(path)}; then echo EXISTS; else echo ABSENT; fi"

    try:
        output = run_adb(
            "-s", serial,
            "shell", command
        )

        return output.strip() == "EXISTS"

    except ADBError as error:
        print(f"Erreur de vérification {path} : {error}")
        raise


def discover_directories(serial):
    """Identifie les dossiers disponibles sur Android."""

    results = {}

    for key, (name, path) in ANDROID_DIRECTORIES.items():

        available = directory_exists(serial, path)

        results[key] = {
            "name": name,
            "path": path,
            "available": available,
        }

    return results
