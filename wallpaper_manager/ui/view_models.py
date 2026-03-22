from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wallpaper_manager.gtk import GObject
from wallpaper_manager.i18n import translate_wallpaper_type
from wallpaper_manager.models import Wallpaper


@dataclass(frozen=True, slots=True)
class WallpaperRowModel:
    directory: Path
    title: str
    wallpaper_type: str
    preview: Path | None = None

    @property
    def wallpaper_type_label(self) -> str:
        return translate_wallpaper_type(self.wallpaper_type)

    def matches(self, query: str) -> bool:
        query_casefold = query.casefold()
        return query_casefold in self.title.casefold() or query_casefold in (
            self.wallpaper_type or ""
        ).casefold()

    @classmethod
    def from_wallpaper(cls, wallpaper: Wallpaper) -> "WallpaperRowModel":
        return cls(
            directory=wallpaper.directory,
            title=wallpaper.title,
            wallpaper_type=wallpaper.wallpaper_type,
            preview=wallpaper.preview,
        )


class WallpaperListItem(GObject.Object):
    def __init__(self, row_model: WallpaperRowModel) -> None:
        super().__init__()
        self.row_model = row_model

    @property
    def directory(self) -> Path:
        return self.row_model.directory

    def matches(self, query: str) -> bool:
        return self.row_model.matches(query)
