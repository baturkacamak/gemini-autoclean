from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from .config import AppConfig, ensure_config, load_config, save_config
from .paths import app_data_dir, current_os, user_bin_dir


RELEASE_API = "https://api.github.com/repos/allenk/GeminiWatermarkTool/releases/latest"
ASSET_MAP = {
    "windows": "GeminiWatermarkTool-Windows-x64.zip",
    "linux": "GeminiWatermarkTool-Linux-x64.zip",
    "macos": "GeminiWatermarkTool-macOS-Universal.zip",
}


def fetch_latest_release() -> dict:
    request = urllib.request.Request(RELEASE_API, headers={"User-Agent": "gemini-autoclean"})
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def find_asset_url(release: dict) -> tuple[str, str]:
    asset_name = ASSET_MAP[current_os()]
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return asset_name, asset["browser_download_url"]
    raise RuntimeError(f"Release asset not found: {asset_name}")


def ensure_tool_installed(config: AppConfig | None = None) -> Path:
    config = config or load_config()
    tool_path = Path(config.tool_path)
    if tool_path.exists():
        ensure_global_shim(tool_path)
        return tool_path

    release = fetch_latest_release()
    asset_name, url = find_asset_url(release)
    install_dir = app_data_dir() / "bin"
    install_dir.mkdir(parents=True, exist_ok=True)
    archive_path = app_data_dir() / asset_name

    download_file(url, archive_path)
    extract_archive(archive_path, install_dir)

    if not tool_path.exists():
        fallback = install_dir / tool_path.name
        if fallback.exists():
            tool_path = fallback
        else:
            raise RuntimeError(f"Expected tool binary not found after extraction: {tool_path}")

    if current_os() != "windows":
        tool_path.chmod(tool_path.stat().st_mode | stat.S_IEXEC)

    config.tool_path = str(tool_path)
    save_config(config)
    ensure_global_shim(tool_path)
    return tool_path


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "gemini-autoclean"})
    with urllib.request.urlopen(request) as response, destination.open("wb") as output:
        shutil.copyfileobj(response, output)


def extract_archive(archive_path: Path, install_dir: Path) -> None:
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(install_dir)


def ensure_global_shim(tool_path: Path) -> Path:
    bin_dir = user_bin_dir()
    bin_dir.mkdir(parents=True, exist_ok=True)
    if current_os() == "windows":
        shim = bin_dir / "GeminiWatermarkTool.cmd"
        shim.write_text(f'@"{tool_path}" %*\n', encoding="utf-8")
        ensure_windows_path(bin_dir)
    else:
        shim = bin_dir / "GeminiWatermarkTool"
        shim.write_text(f'#!/usr/bin/env bash\nexec "{tool_path}" "$@"\n', encoding="utf-8")
        shim.chmod(0o755)
    return shim


def ensure_windows_path(bin_dir: Path) -> None:
    if current_os() != "windows":
        return
    try:
        import winreg  # type: ignore
    except ImportError:
        return

    current = os.environ.get("PATH", "")
    if str(bin_dir) in current.split(";"):
        return

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Environment",
        0,
        winreg.KEY_READ | winreg.KEY_SET_VALUE,
    ) as key:
        try:
            user_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            user_path = ""
        parts = [part for part in user_path.split(";") if part]
        if str(bin_dir) not in parts:
            parts.append(str(bin_dir))
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, ";".join(parts))


def ensure_python_invocation() -> str:
    return sys.executable


def setup_install(source_dir: str | None, target_dir: str | None, patterns: list[str] | None) -> AppConfig:
    overrides = {}
    if source_dir:
        overrides["source_dir"] = source_dir
    if target_dir:
        overrides["target_dir"] = target_dir
    if patterns:
        overrides["patterns"] = patterns
    config = ensure_config(overrides)
    ensure_tool_installed(config)
    return config


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=False, capture_output=True, text=True)
