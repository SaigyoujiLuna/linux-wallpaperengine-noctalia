from __future__ import annotations

import shlex
from typing import Final

from dotenv import dotenv_values

from wallpaper_manager.config.constants import CONFIG_DIR, CONFIG_FILE
from wallpaper_manager.models import AppConfig

DEFAULT_CONFIG_VALUES: Final[dict[str, str]] = {
    "WE_INSTALL_DIR": "",
    "LAST_WALLPAPER_DIR": "",
    "LAST_MONITOR": "",
    "LAST_SCALING": "fill",
}


def load_config() -> AppConfig:
    """Return the persisted application configuration."""
    parsed_values = (
        {
            key: value
            for key, value in dotenv_values(CONFIG_FILE).items()
            if isinstance(value, str)
        }
        if CONFIG_FILE.is_file()
        else {}
    )
    values = {
        key: str(parsed_values.get(key) or default)
        for key, default in DEFAULT_CONFIG_VALUES.items()
    }
    return AppConfig.from_mapping(values)


def save_config(config: AppConfig) -> None:
    """Persist application configuration using the shell-compatible format."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as handle:
        for key, value in config.to_mapping().items():
            handle.write(f"{key}={shlex.quote(value)}\n")
