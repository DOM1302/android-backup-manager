
"""Communication avec Android Debug Bridge."""

import subprocess


class ADBError(Exception):
    """Erreur de communication avec ADB."""


def run_adb(*args, timeout=30):
    """Exécuter une commande ADB et retourner sa sortie."""
    try:
        result = subprocess.run(
            ["adb", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        return result.stdout.strip()
    except FileNotFoundError as exc:
        raise ADBError("ADB n'est pas installé.") from exc
    except subprocess.TimeoutExpired as exc:
        raise ADBError("Délai de réponse ADB dépassé.") from exc
    except subprocess.CalledProcessError as exc:
        raise ADBError(
            exc.stderr.strip() or "Commande ADB échouée."
        ) from exc


def list_devices():
    """Lister les appareils détectés par ADB."""
    output = run_adb("devices", "-l")
    devices = []

    for line in output.splitlines()[1:]:
        parts = line.split()

        if len(parts) < 2:
            continue

        devices.append({
            "serial": parts[0],
            "status": parts[1],
        })

    return devices


def get_device_info(serial):
    """Obtenir les informations d'un téléphone autorisé."""
    def prop(name):
        return run_adb(
            "-s", serial, "shell", "getprop", name
        )

    return {
        "serial": serial,
        "manufacturer": prop("ro.product.manufacturer"),
        "model": prop("ro.product.model"),
        "android_version": prop("ro.build.version.release"),
        "sdk": prop("ro.build.version.sdk"),
    }
