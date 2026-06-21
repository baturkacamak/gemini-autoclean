from __future__ import annotations

import plistlib
import subprocess
from pathlib import Path

from .installer import ensure_python_invocation
from .paths import app_config_dir, current_os, startup_dir_windows


SERVICE_NAME = "gemini-autoclean"


def install_autostart() -> Path:
    os_name = current_os()
    if os_name == "windows":
        return install_windows_startup()
    if os_name == "linux":
        return install_linux_service()
    return install_macos_launch_agent()


def start_watcher_now() -> None:
    python = ensure_python_invocation()
    args = [python, "-m", "gemini_autoclean.cli", "watch"]
    kwargs: dict = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
        "close_fds": True,
    }
    if current_os() == "windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    subprocess.Popen(args, **kwargs)


def install_windows_startup() -> Path:
    startup_dir = startup_dir_windows()
    startup_dir.mkdir(parents=True, exist_ok=True)
    launcher = startup_dir / "gemini_autoclean_watcher.vbs"
    python = ensure_python_invocation()
    launcher.write_text(
        'Set shell = CreateObject("WScript.Shell")\n'
        f'command = "\"{python}\" -m gemini_autoclean.cli watch"\n'
        'shell.Run command, 0, False\n',
        encoding="utf-8",
    )
    return launcher


def install_linux_service() -> Path:
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    service_path = service_dir / f"{SERVICE_NAME}.service"
    python = ensure_python_invocation()
    service_path.write_text(
        "[Unit]\n"
        "Description=Gemini AutoClean watcher\n\n"
        "[Service]\n"
        "Type=simple\n"
        f"ExecStart={python} -m gemini_autoclean.cli watch\n"
        "Restart=always\n"
        "RestartSec=5\n\n"
        "[Install]\n"
        "WantedBy=default.target\n",
        encoding="utf-8",
    )
    return service_path


def install_macos_launch_agent() -> Path:
    agent_dir = Path.home() / "Library" / "LaunchAgents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    agent_path = agent_dir / "com.geminiautoclean.watcher.plist"
    python = ensure_python_invocation()
    payload = {
        "Label": "com.geminiautoclean.watcher",
        "ProgramArguments": [python, "-m", "gemini_autoclean.cli", "watch"],
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": str(app_config_dir() / "launchd.stdout.log"),
        "StandardErrorPath": str(app_config_dir() / "launchd.stderr.log"),
    }
    with agent_path.open("wb") as handle:
        plistlib.dump(payload, handle)
    return agent_path
