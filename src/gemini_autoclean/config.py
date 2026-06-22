from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .paths import app_config_dir, app_data_dir, default_downloads_dir


@dataclass
class AppConfig:
    source_dir: str
    target_dir: str = ""
    source_dirs: list[str] = field(default_factory=list)
    patterns: list[str] = field(default_factory=lambda: ["Gemini_Generated_Image_*"])
    extensions: list[str] = field(default_factory=lambda: [".png", ".jpg", ".jpeg", ".webp"])
    poll_seconds: int = 4
    settle_checks: int = 3
    settle_delay_ms: int = 1500
    remove_original: bool = False
    force_mode: bool = True
    tool_path: str = ""
    log_path: str = ""
    auto_update_tool: bool = True
    update_check_interval_hours: int = 24
    last_tool_update_check: str = ""
    installed_tool_version: str = ""


def config_path() -> Path:
    return app_config_dir() / "config.json"


def default_config() -> AppConfig:
    downloads = default_downloads_dir()
    data_dir = app_data_dir()
    return AppConfig(
        source_dir=str(downloads),
        source_dirs=[str(downloads)],
        target_dir=str(downloads / "Gemini"),
        tool_path=str(data_dir / "bin" / tool_binary_name()),
        log_path=str(data_dir / "gemini-autoclean.log"),
    )


def tool_binary_name() -> str:
    from .paths import current_os

    return "GeminiWatermarkTool.exe" if current_os() == "windows" else "GeminiWatermarkTool"


def ensure_config(overrides: dict | None = None) -> AppConfig:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    config = load_config() if path.exists() else default_config()
    if overrides:
        for key, value in overrides.items():
            if value is not None:
                setattr(config, key, value)
    normalize_sources(config)
    save_config(config)
    return config


def load_config() -> AppConfig:
    path = config_path()
    if not path.exists():
        return ensure_config()
    data = json.loads(path.read_text(encoding="utf-8"))
    config = AppConfig(**data)
    normalize_sources(config)
    return config


def save_config(config: AppConfig) -> None:
    normalize_sources(config)
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


def normalize_sources(config: AppConfig) -> None:
    normalized = [source for source in config.source_dirs if source]
    if not normalized and config.source_dir:
        normalized = [config.source_dir]
    if normalized:
        config.source_dirs = list(dict.fromkeys(normalized))
        config.source_dir = config.source_dirs[0]
