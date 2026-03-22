from typing import override
from wallpaper_manager.config.constants import APP_ID
from wallpaper_manager.gtk import Adw
from wallpaper_manager.ui.window import WallpaperManagerWindow


class WallpaperManagerApp(Adw.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id = APP_ID,
        )
    @override
    def do_activate(self) -> None:
        window = WallpaperManagerWindow(self)
        window.present()
