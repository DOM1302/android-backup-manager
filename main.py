
"""Point d'entrée Android Backup Manager."""

from core.adb import ADBError, list_devices, get_device_info


def main():
    print("=" * 50)
    print("ANDROID BACKUP MANAGER")
    print("=" * 50)

    try:
        devices = list_devices()

        if not devices:
            print("Aucun appareil Android détecté.")
            return

        for device in devices:
            serial = device["serial"]
            status = device["status"]

            print(f"\nAppareil : {serial}")
            print(f"État : {status}")

            if status == "device":
                info = get_device_info(serial)

                print("Fabricant :", info["manufacturer"])
                print("Modèle :", info["model"])
                print("Android :", info["android_version"])
                print("SDK :", info["sdk"])

            elif status == "unauthorized":
                print("Autoriser le débogage USB sur le téléphone.")

            elif status == "offline":
                print("Téléphone hors ligne.")

    except ADBError as error:
        print("Erreur :", error)


if __name__ == "__main__":
    main()
