from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .config import AppConfig, load_config
from .installer import ensure_tool_installed


class Watcher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._seen: dict[str, str] = {}
        self.source_dirs = [Path(source) for source in config.source_dirs]
        self.target_dir = Path(config.target_dir)
        self.log_path = Path(config.log_path)
        self.tool_path = Path(config.tool_path)

    def log(self, message: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

    def is_candidate(self, path: Path) -> bool:
        if not path.is_file():
            return False
        if path.suffix.lower() not in {ext.lower() for ext in self.config.extensions}:
            return False
        return any(path.match(pattern) for pattern in self.config.patterns)

    def is_stable(self, path: Path) -> bool:
        previous_size = -1
        for _ in range(self.config.settle_checks):
            if not path.exists():
                return False
            size = path.stat().st_size
            if size <= 0:
                return False
            if previous_size >= 0 and size != previous_size:
                previous_size = size
                time.sleep(self.config.settle_delay_ms / 1000)
                continue
            previous_size = size
            time.sleep(self.config.settle_delay_ms / 1000)
        return True

    def fingerprint(self, path: Path) -> str:
        stat = path.stat()
        return f"{path}:{stat.st_size}:{int(stat.st_mtime_ns)}"

    def process_file(self, path: Path) -> None:
        fingerprint = self.fingerprint(path)
        if fingerprint in self._seen:
            return

        if not self.is_stable(path):
            self.log(f"Not stable yet: {path}")
            return

        self.target_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.target_dir / path.name
        args = [str(self.tool_path), "--no-banner"]
        if self.config.force_mode:
            args.append("--force")
        args.extend(["--input", str(path), "--output", str(output_path)])

        self.log(f"Processing: {path}")
        result = subprocess.run(args, check=False)
        self._seen[fingerprint] = f"exit:{result.returncode}"

        if result.returncode == 0 and output_path.exists():
            if self.config.remove_original:
                path.unlink(missing_ok=True)
            self.log(f"Cleaned: {path} -> {output_path}")
            return

        self.log(f"Skipped or failed ({result.returncode}): {path}")

    def scan_once(self) -> None:
        for source_dir in self.source_dirs:
            source_dir.mkdir(parents=True, exist_ok=True)
            for candidate in source_dir.iterdir():
                if self.is_candidate(candidate):
                    self.process_file(candidate)

    def watch_forever(self) -> None:
        self.log("Watcher started")
        while True:
            try:
                self.scan_once()
            except Exception as exc:  # noqa: BLE001
                self.log(f"Loop error: {exc}")
            time.sleep(self.config.poll_seconds)


def run_watcher(once: bool = False) -> None:
    config = load_config()
    watcher = Watcher(config)
    try:
        ensure_tool_installed(config, allow_update_check=True)
    except Exception as exc:  # noqa: BLE001
        if Path(config.tool_path).exists():
            watcher.log(f"Tool update check failed, continuing with installed version: {exc}")
        else:
            raise
    watcher = Watcher(load_config())
    if once:
        watcher.scan_once()
        return
    watcher.watch_forever()
