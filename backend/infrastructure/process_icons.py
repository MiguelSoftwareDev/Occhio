"""Read icons installed with applications, with bounded extraction and caching."""

import base64
import configparser
import os
import platform
import shlex
import subprocess
import tempfile
import threading
from functools import lru_cache
from pathlib import Path

_slots = threading.Semaphore(2)


# Lê somente PNGs pequenos
def read_png(path: Path) -> bytes | None:
    if path.is_file() and path.stat().st_size <= 262144:
        data = path.read_bytes()
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return data
    return None


# Indexa ícones declarados pelos aplicativos
@lru_cache(maxsize=1)
def linux_icons() -> dict[str, Path]:
    roots = [Path.home() / ".local/share"]
    roots += [
        Path(p) for p in os.getenv("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":") if p
    ]
    result = {}
    for root in roots:
        for desktop in (root / "applications").glob("*.desktop"):
            try:
                cfg = configparser.ConfigParser(interpolation=None, strict=False)
                cfg.read(desktop, encoding="utf-8")
                entry = cfg["Desktop Entry"]
                command = shlex.split(entry.get("Exec", ""))
                icon = entry.get("Icon", "")
                if not command or not icon:
                    continue
                candidates = [Path(icon)] if Path(icon).is_absolute() else []
                if not candidates:
                    for base in roots:
                        for size in ("48x48", "64x64", "32x32", "128x128", "256x256"):
                            candidates.append(
                                base / "icons/hicolor" / size / "apps" / (icon + ".png")
                            )
                        candidates.append(base / "pixmaps" / (icon + ".png"))
                found = next((p for p in candidates if p.is_file()), None)
                if found:
                    result[Path(command[0]).name] = found
                    result[desktop.stem] = found
            except (OSError, ValueError, KeyError, configparser.Error):
                continue
    return result


# Extrai o ícone original do executável
@lru_cache(maxsize=256)
def extract_icon(executable: str) -> bytes | None:
    with _slots:
        try:
            system = platform.system()
            if system == "Windows":
                script = Path(__file__).parent / "platform" / "extract-icon.ps1"
                result = subprocess.run(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-NonInteractive",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script),
                        "-Executable",
                        executable,
                    ],
                    capture_output=True,
                    timeout=5,
                    check=True,
                    creationflags=0x08000000,
                )
                data = base64.b64decode(result.stdout.strip(), validate=True)
                return data if len(data) <= 262144 and data.startswith(b"\x89PNG") else None
            if system == "Darwin":
                import plistlib

                app = next((p for p in Path(executable).parents if p.suffix == ".app"), None)
                if app:
                    with (app / "Contents/Info.plist").open("rb") as f:
                        name = plistlib.load(f).get("CFBundleIconFile", "")
                    if not name:
                        return None
                    path = app / "Contents/Resources" / name
                    if not path.suffix:
                        path = path.with_suffix(".icns")
                    with tempfile.TemporaryDirectory() as tmp:
                        target = Path(tmp) / "icon.png"
                        subprocess.run(
                            [
                                "sips",
                                "-s",
                                "format",
                                "png",
                                "-Z",
                                "64",
                                str(path),
                                "--out",
                                str(target),
                            ],
                            capture_output=True,
                            check=True,
                            timeout=5,
                        )
                        return read_png(target)
            icon = linux_icons().get(Path(executable).name)
            return read_png(icon) if icon else None
        except (OSError, ValueError, subprocess.SubprocessError):
            return None
