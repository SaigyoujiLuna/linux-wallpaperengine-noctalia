from __future__ import annotations

import sys
from collections.abc import Sequence

from wallpaper_manager.services.system import wait_for_noctalia_shell_startup
from wallpaper_manager.startup import startup_apply
from wallpaper_manager.ui.app import WallpaperManagerApp


def main(argv: Sequence[str] | None = None) -> int:
    program_argv = list(sys.argv if argv is None else [sys.argv[0], *argv])
    if "--startup" in program_argv[1:]:
        if wait_for_noctalia_shell_startup().success:
            return startup_apply()
        else:
            return -1
    application = WallpaperManagerApp()
    return int(application.run(program_argv))
