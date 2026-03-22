from __future__ import annotations

import sys
from pathlib import Path

from wallpaper_manager.config import load_config
from wallpaper_manager.config.constants import ENGINE_BIN
from wallpaper_manager.i18n import tr
from wallpaper_manager.services.system import (
    launch_wallpaper,
    resolve_monitor,
)


def _print_error(message: str) -> None:
    print(f"wallpaper-manager: {message}", file=sys.stderr)


def startup_apply() -> int:
    """Apply the last used wallpaper for desktop-session startup."""
    config = load_config()
    wallpaper_dir = Path(config.last_wallpaper_dir).expanduser()

    if not config.we_install_dir or not config.last_wallpaper_dir:
        _print_error(tr("startup.no_wallpaper_configured"))
        return 1

    if not wallpaper_dir.is_dir():
        _print_error(tr("startup.wallpaper_dir_not_found", path=wallpaper_dir))
        return 1

    monitor = resolve_monitor(config.last_monitor)
    if not monitor:
        _print_error(tr("startup.no_monitors_detected"))
        return 1
    try:
        screenshot_path = launch_wallpaper(
            config.we_install_dir,
            wallpaper_dir,
            monitor,
            config.last_scaling,
        )
    except FileNotFoundError:
        _print_error(tr("startup.engine_not_found", engine_bin=ENGINE_BIN))
        return 1
    except OSError as exc:
        _print_error(
            tr("startup.engine_launch_failed", engine_bin=ENGINE_BIN, error=exc)
        )
        return 1

    return 0
