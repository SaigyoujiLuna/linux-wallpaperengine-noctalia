from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wallpaper_manager.config.constants import PREVIEW_NAMES, WORKSHOP_SUBPATH
from wallpaper_manager.models import Wallpaper


def scan_wallpapers(we_install_dir: str) -> list[Wallpaper]:
    """Scan the Steam workshop directory and return wallpaper metadata."""
    workshop_dir = Path(we_install_dir).expanduser() / WORKSHOP_SUBPATH
    if not workshop_dir.is_dir():
        return []

    try:
        entries = workshop_dir.iterdir()
    except PermissionError:
        return []

    wallpapers: list[Wallpaper] = []
    for entry in entries:
        if not entry.is_dir():
            continue

        project_file = entry / "project.json"
        if not project_file.is_file():
            continue

        try:
            with project_file.open(encoding="utf-8", errors="replace") as handle:
                raw_data: Any = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw_data, dict):
            continue

        preview: Path | None = None
        for preview_name in PREVIEW_NAMES:
            candidate = entry / preview_name
            if candidate.is_file():
                preview = candidate
                break

        wallpapers.append(
            Wallpaper(
                title=str(raw_data.get("title") or entry.name),
                wallpaper_type=str(raw_data.get("type") or "unknown"),
                directory=entry,
                preview=preview,
            )
        )

    return sorted(wallpapers, key=lambda wallpaper: wallpaper.title.casefold())
