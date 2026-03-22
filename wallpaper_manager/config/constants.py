"""Global constants for the Wallpaper Manager GTK application."""

from pathlib import Path
from typing import Final, Literal, TypeAlias

from wallpaper_manager.i18n import tr

ScaleMode: TypeAlias = Literal["fill", "fit", "stretch", "default"]

APP_ID: Final = "io.github.wallpaper-manager-gtk"
APP_NAME: Final = tr("app.name")
ENGINE_SUBTITLE: Final = "linux-wallpaperengine"
AUTO_MONITOR_LABEL: Final = tr("ui.auto_monitor")
CONFIG_DIR: Final = Path("~/.config/wallpaper-manager").expanduser()
CONFIG_FILE: Final = CONFIG_DIR / "config"
CACHE_DIR: Final = Path("~/.cache/wallpaper-manager").expanduser()
WORKSHOP_SUBPATH: Final = Path("steamapps/workshop/content/431960")
ASSETS_SUBPATH: Final = Path("steamapps/common/wallpaper_engine/assets")
ENGINE_BIN: Final = "linux-wallpaperengine"
THUMB_W: Final = 128
THUMB_H: Final = 72
SCALE_MODES: Final[tuple[ScaleMode, ...]] = ("fill", "fit", "stretch", "default")
PREVIEW_NAMES: Final[tuple[str, ...]] = (
    "preview.gif",
    "preview.jpg",
    "preview.png",
    "preview.jpeg",
    "preview.webp",
)
