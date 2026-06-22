from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict

from .config import ensure_config, load_config
from .installer import command_exists, ensure_tool_installed, setup_install
from .paths import current_os, user_bin_dir
from .service import install_autostart, start_watcher_now
from .watcher import run_watcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gemini-autoclean")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Install tool, write config, and install autostart")
    setup_parser.add_argument("--source", action="append", dest="sources")
    setup_parser.add_argument("--target")
    setup_parser.add_argument("--pattern", action="append", dest="patterns")
    setup_parser.add_argument("--no-service", action="store_true")

    tool_parser = subparsers.add_parser("install-tool", help="Download and install GeminiWatermarkTool")
    tool_parser.add_argument("--source", action="append", dest="sources")
    tool_parser.add_argument("--target")
    tool_parser.add_argument("--pattern", action="append", dest="patterns")

    subparsers.add_parser("install-service", help="Install autostart for the watcher")

    update_parser = subparsers.add_parser("update-config", help="Update source, target, or filename patterns")
    update_parser.add_argument("--source", action="append", dest="sources")
    update_parser.add_argument("--target")
    update_parser.add_argument("--pattern", action="append", dest="patterns")

    watch_parser = subparsers.add_parser("watch", help="Run the watcher")
    watch_parser.add_argument("--once", action="store_true")

    config_parser = subparsers.add_parser("print-config", help="Print current config")
    config_parser.add_argument("--json", action="store_true")

    return parser


def cmd_setup(args: argparse.Namespace) -> int:
    config = setup_install(args.sources, args.target, args.patterns)
    if not args.no_service:
        launcher = install_autostart()
        print(f"Autostart installed: {launcher}")
        maybe_enable_linux_service()
        maybe_load_macos_agent(launcher)
        start_watcher_now()
        print("Watcher started for the current session.")
    print(f"Tool path: {config.tool_path}")
    print(f"Watch sources: {', '.join(config.source_dirs)}")
    print(f"Clean target: {config.target_dir}")
    print(f"Patterns: {', '.join(config.patterns)}")
    if current_os() != "windows" and str(user_bin_dir()) not in subprocess.getoutput("echo $PATH"):
        print(f"Note: add {user_bin_dir()} to PATH if GeminiWatermarkTool is not directly callable.")
    return 0


def cmd_install_tool(args: argparse.Namespace) -> int:
    source_overrides = {}
    if args.sources:
        source_overrides["source_dir"] = args.sources[0]
        source_overrides["source_dirs"] = args.sources
    config = ensure_config(
        {
            **source_overrides,
            "target_dir": args.target,
            "patterns": args.patterns,
        }
    )
    tool_path = ensure_tool_installed(config)
    print(f"Installed: {tool_path}")
    return 0


def cmd_install_service(_: argparse.Namespace) -> int:
    launcher = install_autostart()
    print(f"Installed autostart: {launcher}")
    maybe_enable_linux_service()
    maybe_load_macos_agent(launcher)
    return 0


def cmd_update_config(args: argparse.Namespace) -> int:
    source_overrides = {}
    if args.sources:
        source_overrides["source_dir"] = args.sources[0]
        source_overrides["source_dirs"] = args.sources
    config = ensure_config(
        {
            **source_overrides,
            "target_dir": args.target,
            "patterns": args.patterns,
        }
    )
    print(f"Updated config: {', '.join(config.source_dirs)} -> {config.target_dir}")
    print(f"Patterns: {', '.join(config.patterns)}")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    ensure_tool_installed(load_config())
    run_watcher(once=args.once)
    return 0


def cmd_print_config(args: argparse.Namespace) -> int:
    config = load_config()
    data = asdict(config)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        for key, value in data.items():
            print(f"{key}: {value}")
    return 0


def maybe_enable_linux_service() -> None:
    if current_os() != "linux":
        return
    if not command_exists("systemctl"):
        return
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "--now", "gemini-autoclean.service"], check=False)


def maybe_load_macos_agent(launcher) -> None:
    if current_os() != "macos":
        return
    if command_exists("launchctl"):
        subprocess.run(["launchctl", "unload", str(launcher)], check=False)
        subprocess.run(["launchctl", "load", str(launcher)], check=False)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    command_map = {
        "setup": cmd_setup,
        "install-tool": cmd_install_tool,
        "install-service": cmd_install_service,
        "update-config": cmd_update_config,
        "watch": cmd_watch,
        "print-config": cmd_print_config,
    }
    return command_map[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
