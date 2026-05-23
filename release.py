#!/usr/bin/env python3
"""
release.py — Script de publicación de nueva versión
Uso: python release.py 1.2.0 "Descripción de los cambios"

Pasos que ejecuta:
  1. Actualiza local_version.json con la nueva versión.
  2. Compila el .exe con PyInstaller.
  3. Genera el instalador .exe con Inno Setup.
  4. Calcula el SHA-256 del instalador.
  5. Actualiza version.json con la URL de descarga y el checksum.
  6. Hace commit y push (incluyendo el nuevo release en GitHub Releases).

Requisitos:
  - PyInstaller instalado: pip install pyinstaller
  - Inno Setup instalado en C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe
  - GitHub CLI instalado: https://cli.github.com/
  - Variables de entorno o edición manual de REPO_OWNER / REPO_NAME
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────────────────────
REPO_OWNER = "marcelojuarez"
REPO_NAME = "veterinary-stock-management"
APP_NAME = "VeterinariaApp"
MAIN_SCRIPT = "main.py"
INNO_SCRIPT = "installer.iss"
ISCC_PATH = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
DIST_DIR = Path("dist")
# ───────────────────────────────────────────────────────────────────────────────


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def run(cmd: list, **kwargs):
    print(f"\n▶  {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, check=True, **kwargs)
    return result


def main():
    if len(sys.argv) < 3:
        print("Uso: python release.py <version> <notas>")
        print('Ejemplo: python release.py 1.2.0 "Corrección de errores en stock"')
        sys.exit(1)

    new_version = sys.argv[1].strip()
    release_notes = sys.argv[2].strip()
    today = date.today().isoformat()
    tag = f"v{new_version}"
    installer_name = f"{APP_NAME}Setup_{tag}.exe"
    installer_path = DIST_DIR / installer_name

    print(f"\n{'='*60}")
    print(f"  Publicando versión {new_version}")
    print(f"  Notas: {release_notes}")
    print(f"{'='*60}\n")

    # ── 1. Actualizar local_version.json ──────────────────────────────────────
    local_ver = {"version": new_version, "build_date": today}
    Path("local_version.json").write_text(json.dumps(local_ver, indent=2))
    print(f"✅  local_version.json → {new_version}")

    # ── 2. Compilar con PyInstaller ───────────────────────────────────────────
    run([
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        "--icon=assets/logo.ico",
        "--add-data=local_version.json;.",
        "--add-data=db;db",
        "--add-data=assets;assets",
        MAIN_SCRIPT,
    ])
    exe_path = DIST_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        print(f"❌  No se encontró el exe en {exe_path}")
        sys.exit(1)
    print(f"✅  Ejecutable generado: {exe_path}")

    # ── 3. Generar instalador con Inno Setup ──────────────────────────────────
    if not Path(ISCC_PATH).exists():
        print(f"⚠️  Inno Setup no encontrado en {ISCC_PATH}. Saltando paso.")
    else:
        run([
            ISCC_PATH,
            INNO_SCRIPT,
            f"/DMyAppVersion={new_version}",
            f"/DOutputBaseFilename={APP_NAME}Setup_{tag}",
        ])
        if not installer_path.exists():
            # Inno a veces pone el output en Output/
            alt = Path("Output") / installer_name
            if alt.exists():
                installer_path = alt
            else:
                print(f"❌  Instalador no generado. Revisá {INNO_SCRIPT}")
                sys.exit(1)
        print(f"✅  Instalador generado: {installer_path}")

    # ── 4. Calcular SHA-256 ───────────────────────────────────────────────────
    checksum = sha256_of(installer_path)
    print(f"✅  SHA-256: {checksum}")

    # ── 5. Actualizar version.json ────────────────────────────────────────────
    installer_url = (
        f"https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/download/"
        f"{tag}/{installer_name}"
    )
    version_data = {
        "version": new_version,
        "release_date": today,
        "release_notes": release_notes,
        "installer_url": installer_url,
        "checksum_sha256": checksum,
        "mandatory": False,
    }
    Path("version.json").write_text(json.dumps(version_data, indent=2, ensure_ascii=False))
    print(f"✅  version.json actualizado")

    # ── 6. Git commit + push + GitHub Release ─────────────────────────────────
    run(["git", "add", "version.json", "local_version.json"])
    run(["git", "commit", "-m", f"release: v{new_version}"])
    run(["git", "tag", tag])
    run(["git", "push", "origin", "main"])
    run(["git", "push", "origin", tag])

    # Subir el instalador al release de GitHub (requiere GitHub CLI)
    run([
        "gh", "release", "create", tag,
        str(installer_path),
        "--title", f"Versión {new_version}",
        "--notes", release_notes,
    ])

    print(f"\n🎉  ¡Versión {new_version} publicada exitosamente!")
    print(f"   URL: https://github.com/{REPO_OWNER}/{REPO_NAME}/releases/tag/{tag}")


if __name__ == "__main__":
    main()