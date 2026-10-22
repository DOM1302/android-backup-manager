
"""Vérification SHA-256 complète du dossier Download."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from core.integrity import verify_file

SERIAL = "43161JEKB02692"
ANDROID_ROOT = "/sdcard/Download"
LOCAL_ROOT = Path("/backups/Tests_Developpement/Download")
REPORT = Path("/backups/Tests_Developpement/rapport_download_sha256.json")


def list_android_files():
    """Lister les fichiers Android avec séparation NUL."""
    result = subprocess.run(
        [
            "adb", "-s", SERIAL,
            "exec-out", "find",
            ANDROID_ROOT, "-type", "f", "-print0"
        ],
        capture_output=True,
        timeout=120,
        check=True,
    )

    prefix = (ANDROID_ROOT + "/").encode()

    paths = result.stdout.split(b"\0")
    files = []

    for raw_path in paths:
        if not raw_path:
            continue

        if not raw_path.startswith(prefix):
            raise RuntimeError("Chemin Android inattendu.")

        files.append(raw_path.decode("utf-8"))

    return sorted(files)


def main():
    if not LOCAL_ROOT.is_dir():
        raise RuntimeError(
            f"Dossier local introuvable : {LOCAL_ROOT}"
        )

    remote_files = list_android_files()

    if not remote_files:
        raise RuntimeError(
            "Aucun fichier Android trouvé : vérification interrompue."
        )

    entries = []
    remote_relatives = set()

    for index, android_path in enumerate(remote_files, 1):
        relative = android_path[len(ANDROID_ROOT) + 1:]
        remote_relatives.add(relative)

        local_path = LOCAL_ROOT.joinpath(*relative.split("/"))

        print(
            f"[{index}/{len(remote_files)}] {relative}",
            flush=True,
        )

        try:
            result = verify_file(
                SERIAL, android_path, local_path
            )
            status = (
                "identical" if result["identical"]
                else "different"
            )
            detail = result
        except Exception as error:
            status = "error"
            detail = {"error": str(error)}

        entries.append({
            "file": relative,
            "status": status,
            **detail,
        })

    local_relatives = {
        path.relative_to(LOCAL_ROOT).as_posix()
        for path in LOCAL_ROOT.rglob("*")
        if path.is_file()
    }

    for relative in sorted(local_relatives - remote_relatives):
        entries.append({
            "file": relative,
            "status": "local_only",
        })

    counts = {
        status: sum(
            item["status"] == status for item in entries
        )
        for status in (
            "identical", "different", "error", "local_only"
        )
    }

    complete = (
        counts["identical"] == len(remote_files)
        and counts["different"] == 0
        and counts["error"] == 0
    )

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "device": SERIAL,
        "android_root": ANDROID_ROOT,
        "local_root": str(LOCAL_ROOT),
        "remote_file_count": len(remote_files),
        "counts": counts,
        "verified": complete,
        "files": entries,
    }

    REPORT.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== RAPPORT D'INTÉGRITÉ ===")
    print("Fichiers Android :", len(remote_files))
    print("Identiques       :", counts["identical"])
    print("Différents       :", counts["different"])
    print("Erreurs          :", counts["error"])
    print("Locaux uniquement:", counts["local_only"])
    print("Vérification     :", "OK" if complete else "ÉCHEC")
    print("Rapport          :", REPORT)

    if not complete:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
