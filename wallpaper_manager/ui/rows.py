from __future__ import annotations

import threading
from pathlib import Path

from wallpaper_manager.config.constants import THUMB_H, THUMB_W
from wallpaper_manager.gtk import Gdk, GLib, Gtk, Pango
from wallpaper_manager.ui.view_models import WallpaperRowModel


class WallpaperListItemWidget(Gtk.Box):
    def __init__(self) -> None:
        super().__init__()
        self._load_generation = 0
        self._build()

    def _build(self) -> None:
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(12)
        self.set_margin_start(12)
        self.set_margin_end(12)
        self.set_margin_top(8)
        self.set_margin_bottom(8)

        self._thumb = Gtk.Picture()
        self._thumb.set_can_shrink(True)
        self._thumb.set_content_fit(Gtk.ContentFit.COVER)
        self._thumb.set_size_request(THUMB_W, THUMB_H)
        self.append(self._thumb)

        text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        text_box.set_valign(Gtk.Align.CENTER)
        text_box.set_hexpand(True)
        self.append(text_box)

        self._title_label = Gtk.Label(xalign=0)
        self._title_label.add_css_class("title-4")
        self._title_label.set_hexpand(True)
        self._title_label.set_ellipsize(Pango.EllipsizeMode.END)
        text_box.append(self._title_label)

        self._subtitle_label = Gtk.Label(xalign=0)
        self._subtitle_label.add_css_class("dim-label")
        self._subtitle_label.set_ellipsize(Pango.EllipsizeMode.END)
        text_box.append(self._subtitle_label)

    def bind(self, row_model: WallpaperRowModel) -> None:
        self._load_generation += 1
        self._title_label.set_label(row_model.title)
        self._subtitle_label.set_label(row_model.wallpaper_type_label)
        self._thumb.set_paintable(None)
        if row_model.preview is None:
            return

        generation = self._load_generation
        threading.Thread(
            target=self._load_thumb,
            args=(row_model.preview, generation),
            daemon=True,
        ).start()

    def clear(self) -> None:
        self._load_generation += 1
        self._title_label.set_label("")
        self._subtitle_label.set_label("")
        self._thumb.set_paintable(None)

    def _load_thumb(self, path: Path, generation: int) -> None:
        try:
            texture = Gdk.Texture.new_from_filename(str(path))
        except (GLib.Error, OSError):
            return
        GLib.idle_add(self._apply_thumb, texture, generation)

    def _apply_thumb(self, texture: Gdk.Texture, generation: int) -> bool:
        if generation == self._load_generation:
            self._thumb.set_paintable(texture)
        return False
