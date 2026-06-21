from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path


APP_NAME = "GeminiAutoClean"


def current_os() -> str:
    system = platform.system().lower()
    if system.startswith("darwin"):
        return "macos"
    if system.startswith("windows"):
        return "windows"
    if system.startswith("linux"):
        return "linux"
    raise RuntimeError(f"Unsupported platform: {platform.system()}")


def home_dir() -> Path:
    return Path.home()


def app_config_dir() -> Path:
    return home_dir() / ".gemini-autoclean"


def app_data_dir() -> Path:
    return app_config_dir()


def user_bin_dir() -> Path:
    os_name = current_os()
    if os_name == "windows":
        return home_dir() / "bin"
    return home_dir() / ".local" / "bin"


def default_downloads_dir() -> Path:
    if current_os() == "linux":
        xdg = shutil.which("xdg-user-dir")
        if xdg:
            try:
                path = Path(
                    os.popen(f'"{xdg}" DOWNLOAD').read().strip()
                )
                if path.exists():
                    return path
            except OSError:
                pass
        config_file = Path(os.environ.get("XDG_CONFIG_HOME", home_dir() / ".config")) / "user-dirs.dirs"
        if config_file.exists():
            text = config_file.read_text(encoding="utf-8", errors="ignore")
            for line in text.splitlines():
                if line.startswith("XDG_DOWNLOAD_DIR="):
                    value = line.split("=", 1)[1].strip().strip('"')
                    value = value.replace("$HOME", str(home_dir()))
                    return Path(value)
    return home_dir() / "Downloads"


def startup_dir_windows() -> Path:
    return home_dir() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
