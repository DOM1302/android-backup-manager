
"""Interface interactive d'Android Backup Manager."""

from core.adb import list_devices, get_device_info, ADBError
from core.discovery import discover_directories


def select_device():
    devices = list_devices()
    available = [d for d in devices if d["status"] == "device"]

    if not available:
        print("Aucun téléphone Android autorisé.")
        return None

    print("\n=== APPAREILS CONNECTÉS ===")

    for index, device in enumerate(available, 1):
        info = get_device_info(device["serial"])
        print(
            f"{index}. {info['manufacturer']} "
            f"{info['model']} ({device['serial']})"
        )

    while True:
        answer = input("\nChoisir un appareil (0 = quitter) : ")

        if answer == "0":
            return None

        if answer.isdigit() and 1 <= int(answer) <= len(available):
            return available[int(answer) - 1]["serial"]

        print("Choix invalide.")


def select_directories(serial):
    directories = discover_directories(serial)

    print("\n=== DOSSIERS ANDROID ===")

    for key, item in directories.items():
        status = "Disponible" if item["available"] else "Absent"
        print(f"{key}. {item['name']} [{status}]")

    print("\nSélectionne plusieurs dossiers avec des virgules.")
    print("Exemple : 1,2,3")

    while True:
        answer = input("\nDossiers à sauvegarder : ").strip()

        choices = [x.strip() for x in answer.split(",")]

        if (
            choices
            and all(x in directories for x in choices)
            and all(directories[x]["available"] for x in choices)
        ):
            return list(dict.fromkeys(
                directories[x]["path"] for x in choices
            ))

        print("Sélection invalide ou dossier indisponible.")


def ask_destination():
    print("\n=== DESTINATION ===")
    print("Volume Docker disponible : /backups")

    while True:
        answer = input(
            "Nom du sous-dossier de sauvegarde [Android] : "
        ).strip() or "Android"

        if (
            answer not in (".", "..")
            and "/" not in answer
            and "\\" not in answer
            and not any(ord(c) < 32 for c in answer)
        ):
            return "/backups/" + answer

        print("Nom de dossier invalide.")


def run_terminal():
    print("=" * 50)
    print("ANDROID BACKUP MANAGER")
    print("=" * 50)

    try:
        serial = select_device()

        if serial is None:
            return

        folders = select_directories(serial)
        destination = ask_destination()

        print("\n=== RÉCAPITULATIF ===")
        print("Appareil :", serial)
        print("Destination :", destination)

        for folder in folders:
            print("Source :", folder)

        print("\nMODE SIMULATION")
        print("Aucun fichier copié ou supprimé.")

    except (ADBError, EOFError, KeyboardInterrupt) as error:
        print("\nOpération interrompue :", error)
