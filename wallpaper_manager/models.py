from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, cast

from wallpaper_manager.config.constants import SCALE_MODES, ScaleMode


def normalize_scale_mode(value: str) -> ScaleMode:
    return cast(ScaleMode, value) if value in SCALE_MODES else "fill"


@dataclass(slots=True)
class AppConfig:
    we_install_dir: str = ""
    last_wallpaper_dir: str = ""
    last_monitor: str = ""
    last_scaling: ScaleMode = "fill"

    @classmethod
    def from_mapping(cls, values: Mapping[str, str]) -> AppConfig:
        return cls(
            we_install_dir=values.get("WE_INSTALL_DIR", ""),
            last_wallpaper_dir=values.get("LAST_WALLPAPER_DIR", ""),
            last_monitor=values.get("LAST_MONITOR", ""),
            last_scaling=normalize_scale_mode(values.get("LAST_SCALING", "fill") or "fill"),
        )

    def to_mapping(self) -> dict[str, str]:
        return {
            "WE_INSTALL_DIR": self.we_install_dir,
            "LAST_WALLPAPER_DIR": self.last_wallpaper_dir,
            "LAST_MONITOR": self.last_monitor,
            "LAST_SCALING": self.last_scaling,
        }


@dataclass(frozen=True, slots=True)
class Wallpaper:
    title: str
    wallpaper_type: str
    directory: Path
    preview: Path | None = None
