from __future__ import annotations

import threading
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path
from typing import Callable, TypeAlias

from wallpaper_manager.config import load_config, save_config
from wallpaper_manager.config.constants import ENGINE_BIN, SCALE_MODES, ScaleMode
from wallpaper_manager.gtk import GLib
from wallpaper_manager.i18n import tr
from wallpaper_manager.models import AppConfig, Wallpaper
from wallpaper_manager.services.system import (
    OperationResult,
    build_engine_command,
    get_monitors,
    launch_background_process,
    launch_wallpaper,
    notify_noctalia_shell,
    resolve_monitor,
    stop_engine_processes,
)
from wallpaper_manager.services.wallpapers import scan_wallpapers
from wallpaper_manager.ui.view_models import WallpaperRowModel


@dataclass(frozen=True, slots=True)
class WallpaperViewState:
    steam_dir_input: str = ""
    we_install_dir: str = ""
    monitors: tuple[str, ...] = ()
    selected_monitor: str | None = None
    scaling: ScaleMode = "fill"
    search_query: str = ""
    wallpaper_rows: tuple[WallpaperRowModel, ...] = ()
    selected_wallpaper_dir: Path | None = None
    status: str = tr("status.ready")


@dataclass(frozen=True, slots=True)
class ShowErrorEffect:
    message: str


@dataclass(frozen=True, slots=True)
class Initialize:
    ...


@dataclass(frozen=True, slots=True)
class SteamDirInputChanged:
    text: str


@dataclass(frozen=True, slots=True)
class SubmitSteamDir:
    ...


@dataclass(frozen=True, slots=True)
class RefreshMonitors:
    ...


@dataclass(frozen=True, slots=True)
class MonitorsLoaded:
    monitors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SearchChanged:
    query: str


@dataclass(frozen=True, slots=True)
class SelectMonitor:
    monitor: str | None


@dataclass(frozen=True, slots=True)
class SelectScaling:
    scaling: ScaleMode


@dataclass(frozen=True, slots=True)
class RefreshWallpapers:
    ...


@dataclass(frozen=True, slots=True)
class WallpapersLoaded:
    we_install_dir: str
    wallpapers: tuple[Wallpaper, ...]


@dataclass(frozen=True, slots=True)
class SelectWallpaper:
    directory: Path | None


@dataclass(frozen=True, slots=True)
class ApplySelectedWallpaper:
    ...


@dataclass(frozen=True, slots=True)
class ApplyWallpaper:
    directory: Path

@dataclass(frozen=True, slots=True)
class StopEngine:
    ...


@dataclass(frozen=True, slots=True)
class NoctaliaNotificationFinished:
    title: str
    result: OperationResult


Intent: TypeAlias = (
    Initialize
    | SteamDirInputChanged
    | SubmitSteamDir
    | RefreshMonitors
    | MonitorsLoaded
    | SearchChanged
    | SelectMonitor
    | SelectScaling
    | RefreshWallpapers
    | WallpapersLoaded
    | SelectWallpaper
    | ApplySelectedWallpaper
    | ApplyWallpaper
    | StopEngine
    | NoctaliaNotificationFinished
)
StateListener: TypeAlias = Callable[[WallpaperViewState], None]
EffectListener: TypeAlias = Callable[[ShowErrorEffect], None]


class WallpaperStore:
    def __init__(
        self,
        on_state: StateListener,
        on_effect: EffectListener,
    ) -> None:
        self._on_state = on_state
        self._on_effect = on_effect
        self._config = load_config()
        self._wallpapers_by_directory: dict[Path, Wallpaper] = {}
        scaling = (
            self._config.last_scaling
            if self._config.last_scaling in SCALE_MODES
            else SCALE_MODES[0]
        )
        self._state = WallpaperViewState(
            steam_dir_input=self._config.we_install_dir,
            we_install_dir=self._config.we_install_dir,
            selected_monitor=self._config.last_monitor or None,
            scaling=scaling,
        )

    @property
    def state(self) -> WallpaperViewState:
        return self._state

    def start(self) -> None:
        self._publish_state()
        self.dispatch(Initialize())

    def dispatch(
        self,
        intent: Intent,
    ) -> None:
        if isinstance(intent, Initialize):
            self.dispatch(RefreshMonitors())
            if self._state.we_install_dir:
                self.dispatch(RefreshWallpapers())
            return

        if isinstance(intent, SteamDirInputChanged):
            self._set_state(replace(self._state, steam_dir_input=intent.text))
            return

        if isinstance(intent, SubmitSteamDir):
            self._handle_submit_steam_dir()
            return

        if isinstance(intent, RefreshMonitors):
            self._run_async(self._load_monitors)
            return

        if isinstance(intent, MonitorsLoaded):
            selected_monitor = self._state.selected_monitor
            if selected_monitor not in intent.monitors:
                selected_monitor = intent.monitors[0] if intent.monitors else None
            self._set_state(
                replace(
                    self._state,
                    monitors=intent.monitors,
                    selected_monitor=selected_monitor,
                )
            )
            return

        if isinstance(intent, SearchChanged):
            self._set_state(replace(self._state, search_query=intent.query))
            return

        if isinstance(intent, SelectMonitor):
            self._set_state(replace(self._state, selected_monitor=intent.monitor))
            return

        if isinstance(intent, SelectScaling):
            self._set_state(replace(self._state, scaling=intent.scaling))
            return

        if isinstance(intent, RefreshWallpapers):
            if not self._state.we_install_dir:
                self._set_state(
                    replace(
                        self._state,
                        wallpaper_rows=(),
                        selected_wallpaper_dir=None,
                        status=tr("status.set_steam_dir_first"),
                    )
                )
                return
            self._set_state(
                replace(
                    self._state,
                    wallpaper_rows=(),
                    selected_wallpaper_dir=None,
                    status=tr("status.scanning_wallpapers"),
                )
            )
            self._run_async(partial(self._load_wallpapers, self._state.we_install_dir))
            return

        if isinstance(intent, WallpapersLoaded):
            if intent.we_install_dir != self._state.we_install_dir:
                return
            self._wallpapers_by_directory = {
                wallpaper.directory: wallpaper for wallpaper in intent.wallpapers
            }
            selected_wallpaper_dir = self._state.selected_wallpaper_dir
            available_directories = set(self._wallpapers_by_directory)
            if selected_wallpaper_dir not in available_directories:
                selected_wallpaper_dir = None
            self._set_state(
                replace(
                    self._state,
                    wallpaper_rows=tuple(
                        WallpaperRowModel.from_wallpaper(wallpaper)
                        for wallpaper in intent.wallpapers
                    ),
                    selected_wallpaper_dir=selected_wallpaper_dir,
                    status=tr("status.wallpaper_count", count=len(intent.wallpapers)),
                )
            )
            return

        if isinstance(intent, SelectWallpaper):
            self._set_state(
                replace(self._state, selected_wallpaper_dir=intent.directory)
            )
            return

        if isinstance(intent, ApplySelectedWallpaper):
            if self._state.selected_wallpaper_dir is None:
                self._set_state(
                    replace(self._state, status=tr("status.select_wallpaper_first"))
                )
                return
            self.dispatch(ApplyWallpaper(self._state.selected_wallpaper_dir))
            return

        if isinstance(intent, ApplyWallpaper):
            self._handle_apply_wallpaper(intent.directory)
            return

        if isinstance(intent, StopEngine):
            stopped = stop_engine_processes()
            self._set_state(
                replace(
                    self._state,
                    status=(
                        tr("status.engine_stopped")
                        if stopped
                        else tr("status.engine_not_running")
                    ),
                )
            )
            return

        if isinstance(intent, NoctaliaNotificationFinished):
            status = tr("status.applied_wallpaper", title=intent.title)
            if intent.result.success:
                status += tr("status.noctalia_updated")
            elif intent.result.error:
                status += tr("status.noctalia_not_updated", error=intent.result.error)
            self._set_state(replace(self._state, status=status))
            return

    def _handle_submit_steam_dir(self) -> None:
        path = self._state.steam_dir_input.strip()
        if not path:
            self._set_state(
                replace(self._state, status=tr("status.enter_steam_dir_first"))
            )
            return

        steam_dir = Path(path).expanduser()
        if not steam_dir.is_dir():
            self._emit_error(tr("error.dir_not_found", path=path))
            return

        resolved = str(steam_dir.resolve())
        self._save_config(replace(self._config, we_install_dir=resolved))
        self._set_state(
            replace(
                self._state,
                steam_dir_input=resolved,
                we_install_dir=resolved,
            )
        )
        self.dispatch(RefreshWallpapers())

    def _handle_apply_wallpaper(self, directory: Path) -> None:
        if not self._state.we_install_dir:
            self._emit_error(tr("status.set_steam_dir_first"))
            return

        wallpaper = self._wallpapers_by_directory.get(directory)
        if wallpaper is None:
            self._set_state(
                replace(self._state, status=tr("status.invalid_wallpaper_selected"))
            )
            return

        monitor = self._resolve_monitor()
        if not monitor:
            return

        self._save_config(
            replace(
                self._config,
                we_install_dir=self._state.we_install_dir,
                last_wallpaper_dir=str(wallpaper.directory.resolve()),
                last_monitor=monitor,
                last_scaling=self._state.scaling,
            )
        )
        try:
            screenshot_path = launch_wallpaper(
                self._state.we_install_dir,
                wallpaper.directory,
                monitor,
                self._state.scaling,
            )
        except FileNotFoundError:
            self._emit_error(tr("error.engine_not_found", engine_bin=ENGINE_BIN))
            return
        except OSError as exc:
            self._emit_error(tr("error.launch_failed", error=exc))
            return

        self._set_state(
            replace(
                self._state,
                selected_wallpaper_dir=wallpaper.directory,
                status=tr("status.applied_wallpaper", title=wallpaper.title),
            )
        )
        self._run_async(
            partial(
                self._notify_noctalia,
                wallpaper.title,
                monitor,
                screenshot_path,
            )
        )

    def _load_monitors(self) -> None:
        self._dispatch_on_main_thread(MonitorsLoaded(tuple(get_monitors())))

    def _load_wallpapers(self, we_install_dir: str) -> None:
        wallpapers = tuple(scan_wallpapers(we_install_dir))
        self._dispatch_on_main_thread(WallpapersLoaded(we_install_dir, wallpapers))

    def _notify_noctalia(
        self,
        title: str,
        monitor: str,
        screenshot_path: Path,
    ) -> None:
        result = notify_noctalia_shell(monitor, screenshot_path)
        self._dispatch_on_main_thread(NoctaliaNotificationFinished(title, result))

    def _dispatch_on_main_thread(self, intent: Intent) -> None:
        # Worker threads always bounce state changes back through GTK's main loop.
        GLib.idle_add(self._dispatch_from_idle, intent)

    def _dispatch_from_idle(self, intent: Intent) -> bool:
        self.dispatch(intent)
        return False

    def _run_async(self, target: Callable[[], None]) -> None:
        threading.Thread(target=target, daemon=True).start()

    def _save_config(self, config: AppConfig) -> None:
        self._config = config
        save_config(self._config)

    def _resolve_monitor(self) -> str | None:
        monitor = resolve_monitor(self._state.selected_monitor)
        if not monitor:
            self._emit_error(tr("error.monitor_detection_failed"))
        return monitor

    def _emit_error(self, message: str) -> None:
        self._set_state(replace(self._state, status=tr("status.error_prefix", message=message)))
        self._on_effect(ShowErrorEffect(message))

    def _set_state(self, state: WallpaperViewState) -> None:
        self._state = state
        self._publish_state()

    def _publish_state(self) -> None:
        self._on_state(self._state)
