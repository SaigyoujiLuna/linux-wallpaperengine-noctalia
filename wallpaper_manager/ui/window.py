from __future__ import annotations

from pathlib import Path
from typing import Callable, TypeAlias

from wallpaper_manager.config.constants import AUTO_MONITOR_LABEL, SCALE_MODES
from wallpaper_manager.gtk import Adw, Gio, GLib, Gtk
from wallpaper_manager.i18n import tr, translate_scale_mode
from wallpaper_manager.ui.mvi import (
    ApplySelectedWallpaper,
    ApplyWallpaper,
    Intent,
    RefreshMonitors,
    RefreshWallpapers,
    SearchChanged,
    SelectMonitor,
    SelectScaling,
    SelectWallpaper,
    ShowErrorEffect,
    SteamDirInputChanged,
    StopEngine,
    SubmitSteamDir,
    WallpaperStore,
    WallpaperViewState,
)
from wallpaper_manager.ui.rows import WallpaperListItemWidget
from wallpaper_manager.ui.view_models import WallpaperListItem, WallpaperRowModel

GtkCallbackArg: TypeAlias = object
ButtonHandler: TypeAlias = Callable[[Gtk.Button], None]
RowWidget: TypeAlias = Gtk.Widget


class WallpaperManagerWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application) -> None:
        super().__init__(application=app)
        self.set_title(tr("app.name"))
        self._state = WallpaperViewState()
        self._rendered_wallpapers: tuple[WallpaperRowModel, ...] = ()
        self._suppress_selection_signal = False
        self._monitor_model = Gtk.StringList.new([AUTO_MONITOR_LABEL])
        self._scale_model = Gtk.StringList.new(
            [translate_scale_mode(mode) for mode in SCALE_MODES]
        )
        self._string_expression = Gtk.PropertyExpression.new(
            Gtk.StringObject,
            None,
            "string",
        )
        self._wallpaper_store = Gio.ListStore.new(WallpaperListItem)
        self._wallpaper_filter = Gtk.CustomFilter.new(self._filter_item)
        self._filtered_wallpapers = Gtk.FilterListModel.new(
            self._wallpaper_store,
            self._wallpaper_filter,
        )
        self._selection = Gtk.SingleSelection.new(self._filtered_wallpapers)
        self._selection.set_autoselect(False)
        self._selection.set_can_unselect(True)
        self._selection.connect("notify::selected-item", self._on_row_selected)

        self._list_factory = Gtk.SignalListItemFactory()
        self._list_factory.connect("setup", self._on_factory_setup)
        self._list_factory.connect("bind", self._on_factory_bind)
        self._list_factory.connect("unbind", self._on_factory_unbind)

        self._build_ui()
        self._store = WallpaperStore(self._render, self._handle_effect)
        self._store.start()

    def _build_ui(self) -> None:
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        toolbar_view.add_top_bar(self._build_header())

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_start(12)
        root.set_margin_end(12)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        clamp = Adw.Clamp()
        clamp.set_maximum_size(1100)
        clamp.set_tightening_threshold(800)
        clamp.set_child(root)
        toolbar_view.set_content(clamp)
        self._settings_dialog = self._build_settings_dialog()

        self._monitor_row = Adw.ComboRow(title=tr("ui.monitor"))
        self._monitor_row.set_model(
            self._monitor_model,
        )
        self._monitor_row.set_expression(self._string_expression)
        self._monitor_row.connect("notify::selected", self._on_monitor_changed)
        self._monitor_row.add_suffix(
            self._create_icon_button(
                "view-refresh-symbolic",
                tr("ui.refresh_monitors"),
                self._on_refresh_monitors,
            )
        )

        self._scale_row = Adw.ComboRow(title=tr("ui.scale_mode"))
        self._scale_row.set_model(
            self._scale_model,
        )
        self._scale_row.set_expression(self._string_expression)
        self._scale_row.connect("notify::selected", self._on_scale_changed)

        root.append(self._create_group(self._monitor_row, self._scale_row))

        self._list_stack = Gtk.Stack()
        self._list_stack.set_vexpand(True)
        root.append(self._list_stack)

        scroll = Gtk.ScrolledWindow()
        scroll.set_overlay_scrolling(False)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._list_view = Gtk.ListView.new(self._selection, self._list_factory)
        self._list_view.set_single_click_activate(False)
        self._list_view.add_css_class("boxed-list")
        self._list_view.connect("activate", self._on_row_activated)
        scroll.set_child(self._list_view)
        self._list_stack.add_named(scroll, "list")

        self._placeholder = Adw.StatusPage()
        self._placeholder.set_icon_name("preferences-desktop-wallpaper-symbolic")
        self._placeholder.set_vexpand(True)
        self._list_stack.add_named(self._placeholder, "placeholder")

        self._status_row = Adw.ActionRow(title=tr("ui.status"))
        self._status_row.set_subtitle(tr("status.ready"))
        self._status_row.set_activatable(False)

        self._status_row.add_prefix(
            self._create_icon_button(
                "view-refresh-symbolic",
                tr("ui.refresh_wallpapers"),
                self._on_refresh_wallpapers,
            )
        )
        self._status_row.add_suffix(
            self._create_icon_button(
                "media-playback-stop-symbolic",
                tr("ui.stop_engine"),
                self._on_stop_engine,
            )
        )
        self._status_row.add_suffix(
            self._create_icon_button(
                "object-select-symbolic",
                tr("ui.apply_wallpaper"),
                self._on_apply_clicked,
            )
        )

        root.append(self._create_group(self._status_row, title=tr("ui.status")))
        self._update_list_state()

    def _build_header(self) -> Adw.HeaderBar:
        header = Adw.HeaderBar()
        header.set_show_title(False)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text(tr("ui.search_placeholder"))
        self._search_entry.set_hexpand(True)
        self._search_entry.connect("search-changed", self._on_search_changed)
        header.pack_start(self._search_entry)

        settings_button = Gtk.Button(icon_name="emblem-system-symbolic")
        settings_button.set_tooltip_text(tr("ui.settings"))
        settings_button.connect("clicked", self._on_open_settings)
        header.pack_end(settings_button)
        return header

    def _build_settings_dialog(self) -> Adw.PreferencesDialog:
        dialog = Adw.PreferencesDialog()
        dialog.set_title(tr("ui.settings"))
        dialog.set_content_width(720)
        dialog.set_content_height(520)

        settings_page = Adw.PreferencesPage()
        dialog.add(settings_page)

        self._dir_entry = Adw.EntryRow(title=tr("ui.steam_directory"))
        self._dir_entry.set_hexpand(True)
        self._dir_entry.connect("notify::text", self._on_dir_changed)
        self._dir_entry.add_suffix(
            self._create_icon_button(
                "document-open-symbolic",
                tr("ui.browse_steam_directory"),
                self._on_browse,
            )
        )
        self._dir_entry.add_suffix(
            self._create_icon_button(
                "object-select-symbolic",
                tr("ui.save_refresh_wallpapers"),
                self._on_set_dir,
            )
        )
        settings_page.add(
            self._create_group(
                self._dir_entry,
                title=tr("ui.wallpaper_source"),
                description=tr("ui.wallpaper_source_desc"),
            )
        )

        overview_row = Adw.ActionRow(
            title=tr("ui.niri_overview_background"),
            subtitle=tr("ui.niri_overview_background_desc"),
        )
        overview_row.set_activatable(False)
        settings_page.add(
            self._create_group(
                overview_row,
                title=tr("ui.overview"),
                description=tr("ui.overview_desc"),
            )
        )

        return dialog

    def _create_group(
        self,
        *rows: RowWidget,
        title: str | None = None,
        description: str | None = None,
    ) -> Adw.PreferencesGroup:
        group = Adw.PreferencesGroup()
        if title is not None:
            group.set_title(title)
        if description is not None:
            group.set_description(description)
        for row in rows:
            group.add(row)
        return group

    def _create_icon_button(
        self,
        icon_name: str,
        tooltip: str,
        callback: ButtonHandler,
    ) -> Gtk.Button:
        button = Gtk.Button(icon_name=icon_name)
        button.set_valign(Gtk.Align.CENTER)
        button.connect("clicked", callback)
        button.set_tooltip_text(tooltip)
        return button

    def _on_browse(self, _widget: GtkCallbackArg) -> None:
        dialog = Gtk.FileDialog(title=tr("ui.select_steam_directory"), modal=True)
        current_dir = Path(self._state.steam_dir_input).expanduser()
        if self._state.steam_dir_input and current_dir.is_dir():
            dialog.set_initial_folder(Gio.File.new_for_path(str(current_dir)))
        dialog.select_folder(self, None, self._on_browse_selected)

    def _on_browse_selected(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
    ) -> None:
        try:
            selected_file = dialog.select_folder_finish(result)
        except GLib.Error:
            return
        selected = selected_file.get_path() if selected_file is not None else None
        if selected is not None:
            self._store.dispatch(SteamDirInputChanged(selected))
            self._store.dispatch(SubmitSteamDir())

    def _on_dir_changed(
        self,
        _widget: GtkCallbackArg,
        _pspec: GtkCallbackArg | None = None,
    ) -> None:
        self._dispatch_intent(SteamDirInputChanged(self._dir_entry.get_text()))

    def _on_set_dir(self, _widget: GtkCallbackArg) -> None:
        self._dispatch_intent(SubmitSteamDir())

    def _on_open_settings(self, _widget: GtkCallbackArg) -> None:
        self._settings_dialog.present(self)

    def _on_refresh_monitors(self, _widget: GtkCallbackArg) -> None:
        self._dispatch_intent(RefreshMonitors())

    def _on_monitor_changed(
        self,
        _widget: GtkCallbackArg,
        _pspec: GtkCallbackArg,
    ) -> None:
        selected_index = self._monitor_row.get_selected()
        self._dispatch_intent(
            SelectMonitor(
                None
                if selected_index == 0
                else self._monitor_model.get_string(selected_index)
            )
        )

    def _on_scale_changed(
        self,
        _widget: GtkCallbackArg,
        _pspec: GtkCallbackArg,
    ) -> None:
        selected_index = self._scale_row.get_selected()
        if 0 <= selected_index < len(SCALE_MODES):
            self._dispatch_intent(SelectScaling(SCALE_MODES[selected_index]))

    def _on_search_changed(self, _widget: GtkCallbackArg) -> None:
        self._dispatch_intent(
            SearchChanged(self._search_entry.get_text().strip()),
            invalidate_filter=True,
        )

    def _filter_item(self, item: GtkCallbackArg | None) -> bool:
        query = self._state.search_query
        if not query or not isinstance(item, WallpaperListItem):
            return True
        return item.matches(query)

    def _on_row_selected(
        self,
        _selection: GtkCallbackArg,
        _pspec: GtkCallbackArg,
    ) -> None:
        if self._suppress_selection_signal:
            return
        selected_item = self._selection.get_selected_item()
        directory = (
            selected_item.directory
            if isinstance(selected_item, WallpaperListItem)
            else None
        )
        self._dispatch_intent(SelectWallpaper(directory))

    def _on_row_activated(
        self,
        _list_view: Gtk.ListView,
        position: int,
    ) -> None:
        item = self._filtered_wallpapers.get_item(position)
        if isinstance(item, WallpaperListItem):
            self._dispatch_intent(ApplyWallpaper(item.directory))

    def _on_factory_setup(
        self,
        _factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        list_item.set_child(WallpaperListItemWidget())

    def _on_factory_bind(
        self,
        _factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        child = list_item.get_child()
        item = list_item.get_item()
        if isinstance(child, WallpaperListItemWidget) and isinstance(
            item,
            WallpaperListItem,
        ):
            child.bind(item.row_model)

    def _on_factory_unbind(
        self,
        _factory: Gtk.SignalListItemFactory,
        list_item: Gtk.ListItem,
    ) -> None:
        child = list_item.get_child()
        if isinstance(child, WallpaperListItemWidget):
            child.clear()

    def _on_apply_clicked(self, _widget: GtkCallbackArg) -> None:
        self._dispatch_intent(ApplySelectedWallpaper())

    def _on_stop_engine(self, _widget: GtkCallbackArg) -> None:
        self._dispatch_intent(StopEngine())

    def _on_refresh_wallpapers(self, _widget: GtkCallbackArg) -> None:
        self._dispatch_intent(RefreshWallpapers())

    def _render(self, state: WallpaperViewState) -> None:
        self._state = state
        if self._dir_entry.get_text() != state.steam_dir_input:
            self._dir_entry.set_text(state.steam_dir_input)
        if self._search_entry.get_text() != state.search_query:
            self._search_entry.set_text(state.search_query)

        self._set_monitor_options(state.monitors, state.selected_monitor)

        if state.scaling in SCALE_MODES:
            self._scale_row.set_selected(SCALE_MODES.index(state.scaling))

        self._suppress_selection_signal = True
        try:
            if state.wallpaper_rows != self._rendered_wallpapers:
                self._render_wallpaper_rows(state.wallpaper_rows)
            self._invalidate_filter()
            self._sync_selected_row(state.selected_wallpaper_dir)
        finally:
            self._suppress_selection_signal = False

        self._update_list_state()
        self._status_row.set_subtitle(state.status)

    def _render_wallpaper_rows(
        self,
        row_models: tuple[WallpaperRowModel, ...],
    ) -> None:
        self._rendered_wallpapers = row_models
        self._wallpaper_store.remove_all()
        for row_model in row_models:
            self._wallpaper_store.append(WallpaperListItem(row_model))

    def _sync_selected_row(self, selected_directory: Path | None) -> None:
        selected_position = self._selection.get_selected()
        target_position = (
            Gtk.INVALID_LIST_POSITION
            if selected_directory is None
            else self._find_filtered_position(selected_directory)
        )
        if target_position is None:
            target_position = Gtk.INVALID_LIST_POSITION
        if selected_position != target_position:
            self._selection.set_selected(target_position)

    def _find_filtered_position(self, directory: Path) -> int | None:
        for index in range(self._filtered_wallpapers.get_n_items()):
            item = self._filtered_wallpapers.get_item(index)
            if isinstance(item, WallpaperListItem) and item.directory == directory:
                return index
        return None

    def _invalidate_filter(self) -> None:
        self._wallpaper_filter.changed(Gtk.FilterChange.DIFFERENT)
        self._update_list_state()

    def _update_list_state(self) -> None:
        total_count = self._wallpaper_store.get_n_items()
        visible_count = self._filtered_wallpapers.get_n_items()
        if visible_count > 0:
            self._list_stack.set_visible_child_name("list")
            return

        if total_count == 0:
            if not self._state.we_install_dir:
                title = tr("ui.empty.no_wallpapers_title")
                description = tr("ui.empty.no_wallpapers_desc")
            elif self._state.status == tr("status.scanning_wallpapers"):
                title = tr("ui.empty.scanning_title")
                description = tr("ui.empty.scanning_desc")
            else:
                title = tr("ui.empty.not_found_title")
                description = tr("ui.empty.not_found_desc")
        else:
            title = tr("ui.empty.no_match_title")
            description = tr("ui.empty.no_match_desc", query=self._state.search_query)

        self._placeholder.set_title(title)
        self._placeholder.set_description(description)
        self._list_stack.set_visible_child_name("placeholder")

    def _handle_effect(self, effect: ShowErrorEffect) -> None:
        dialog = Adw.AlertDialog(heading=tr("ui.error_heading"), body=effect.message)
        dialog.add_response("ok", tr("ui.confirm"))
        dialog.set_default_response("ok")
        dialog.present(self)

    def _dispatch_intent(
        self,
        intent: Intent,
        *,
        invalidate_filter: bool = False,
    ) -> None:
        self._store.dispatch(intent)
        if invalidate_filter:
            self._invalidate_filter()

    def _set_monitor_options(
        self,
        monitors: tuple[str, ...],
        selected_monitor: str | None,
    ) -> None:
        values = (AUTO_MONITOR_LABEL, *monitors)
        current_size = self._monitor_model.get_n_items()
        if current_size != len(values):
            self._monitor_model.splice(0, current_size, list(values))
        else:
            for index, value in enumerate(values):
                if self._monitor_model.get_string(index) != value:
                    self._monitor_model.splice(index, 1, [value])

        active_index = 0
        for index, monitor in enumerate(monitors, start=1):
            if monitor == selected_monitor:
                active_index = index
                break
        self._monitor_row.set_selected(active_index)
