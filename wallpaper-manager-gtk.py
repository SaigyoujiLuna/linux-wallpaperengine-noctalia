#!/usr/bin/env python3
"""
Wallpaper Manager GTK
=====================
GTK3 图形界面壁纸选择器，基于 wallpaper-manager.sh 的逻辑实现。
功能：
  - 设置并保存 Steam 安装目录（与 shell 脚本共享同一配置文件）
  - 扫描 Workshop 壁纸列表，显示缩略图与标题
  - 搜索过滤壁纸
  - 选择显示器与缩放模式
  - 一键应用 / 双击应用壁纸
  - 启动 / 停止 linux-wallpaperengine
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GdkPixbuf, Gio, Pango  # noqa: E402

import os
import json
import shutil
import subprocess
import threading

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_ID = "io.github.wallpaper-manager-gtk"
CONFIG_DIR = os.path.expanduser("~/.config/wallpaper-manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")
WORKSHOP_SUBPATH = "steamapps/workshop/content/431960"
ASSETS_SUBPATH = "steamapps/common/wallpaper_engine/assets"
ENGINE_BIN = "linux-wallpaperengine"
THUMB_W, THUMB_H = 128, 72
PREVIEW_NAMES = ("preview.gif", "preview.jpg", "preview.png",
                 "preview.jpeg", "preview.webp")

# ---------------------------------------------------------------------------
# Config helpers  (same file format as wallpaper-manager.sh)
# ---------------------------------------------------------------------------

def load_config():
    """Return config dict with WE_INSTALL_DIR and OVERVIEW_BLUR."""
    cfg = {"WE_INSTALL_DIR": "", "OVERVIEW_BLUR": "0"}
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, encoding="utf-8") as fh:
            for line in fh:
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    cfg[key.strip()] = val.strip()
    return cfg


def save_config(we_install_dir, overview_blur=0,
                last_wallpaper_dir="", last_monitor="", last_scaling="fill"):
    """Persist config to file (compatible with wallpaper-manager.sh)."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"WE_INSTALL_DIR={we_install_dir}\n")
        fh.write(f"OVERVIEW_BLUR={overview_blur}\n")
        fh.write(f"LAST_WALLPAPER_DIR={last_wallpaper_dir}\n")
        fh.write(f"LAST_MONITOR={last_monitor}\n")
        fh.write(f"LAST_SCALING={last_scaling}\n")

# ---------------------------------------------------------------------------
# Engine / system helpers
# ---------------------------------------------------------------------------

def get_monitors():
    """Return list of monitor names reported by wlr-randr, or []."""
    try:
        result = subprocess.run(
            ["wlr-randr", "--json"],
            capture_output=True, text=True, timeout=5
        )
        return [m["name"] for m in json.loads(result.stdout)]
    except Exception:
        return []


def scan_wallpapers(we_install_dir):
    """
    Walk the Workshop directory and collect wallpaper metadata.
    Returns a list of dicts: {title, type, dir, preview}.
    Sorted alphabetically by title (case-insensitive).
    """
    workshop_dir = os.path.join(we_install_dir, WORKSHOP_SUBPATH)
    wallpapers = []
    if not os.path.isdir(workshop_dir):
        return wallpapers
    try:
        entries = sorted(os.scandir(workshop_dir), key=lambda e: e.name)
    except PermissionError:
        return wallpapers

    for entry in entries:
        if not entry.is_dir():
            continue
        project_file = os.path.join(entry.path, "project.json")
        if not os.path.isfile(project_file):
            continue
        try:
            with open(project_file, encoding="utf-8", errors="replace") as fh:
                data = json.load(fh)
            title = data.get("title") or entry.name
            wp_type = data.get("type", "unknown")
            preview = next(
                (os.path.join(entry.path, n) for n in PREVIEW_NAMES
                 if os.path.isfile(os.path.join(entry.path, n))),
                None
            )
            wallpapers.append({
                "title": title,
                "type": wp_type,
                "dir": entry.path,
                "preview": preview,
            })
        except Exception:
            continue

    wallpapers.sort(key=lambda x: x["title"].casefold())
    return wallpapers


def notify_noctalia_shell(monitor, wallpaper_path):
    """
    Ask noctalia-shell to refresh wallpaper-driven colors by syncing the
    rendered wallpaper frame through its wallpaper IPC endpoint.
    """
    if shutil.which("qs") is None:
        return False, "未找到 qs"

    try:
        result = subprocess.run(
            [
                "qs", "ipc", "-c", "noctalia-shell",
                "call", "wallpaper", "set", wallpaper_path, monitor,
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except FileNotFoundError:
        return False, "未找到 qs"
    except subprocess.TimeoutExpired:
        return False, "通知 noctalia-shell 超时"

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        return False, detail or "noctalia-shell IPC 调用失败"

    return True, None


def notify_niri_overview(monitor, screenshot_path, blur_radius):
    """
    Wait for linux-wallpaperengine to write its screenshot, optionally apply
    Gaussian blur via ImageMagick, set the result as the swaybg background,
    notify noctalia-shell to regenerate wallpaper-based colors, then trigger a
    niri screen transition.

    Designed to run in a background thread or blocking CLI context.
    Returns a result dict describing which notifications succeeded.
    """
    import time

    deadline = time.time() + 20
    while time.time() < deadline:
        if os.path.isfile(screenshot_path):
            time.sleep(0.2)
            break
        time.sleep(0.5)
    else:
        return {
            "overview_updated": False,
            "noctalia_notified": False,
            "noctalia_error": None,
        }

    display_path = screenshot_path
    if blur_radius > 0:
        blurred_path = screenshot_path.replace(".png", "-blurred.png")
        try:
            result = subprocess.run(
                ["convert", screenshot_path,
                 "-blur", f"0x{blur_radius}",
                 blurred_path],
                capture_output=True,
                timeout=15,
            )
            if result.returncode == 0 and os.path.isfile(blurred_path):
                display_path = blurred_path
        except Exception:
            pass

    try:
        subprocess.run(["pkill", "-f", "swaybg"], capture_output=True)
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["swaybg", "-o", monitor, "-i", display_path, "-m", "fill"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass

    noctalia_ok, noctalia_error = notify_noctalia_shell(monitor, screenshot_path)

    try:
        subprocess.run(
            ["niri", "msg", "action", "do-screen-transition", "--delay-ms", "300"],
            capture_output=True,
            timeout=5,
        )
    except Exception:
        pass

    return {
        "overview_updated": True,
        "noctalia_notified": noctalia_ok,
        "noctalia_error": noctalia_error,
    }


def startup_apply():
    """
    Apply the last-used wallpaper from config and notify niri's overview.
    Intended for niri's spawn-at-startup:

        spawn-at-startup "python3 /path/to/wallpaper-manager-gtk.py" "--startup"
    """
    import sys
    import time

    cfg = load_config()
    we_install_dir     = cfg.get("WE_INSTALL_DIR", "")
    wallpaper_dir      = cfg.get("LAST_WALLPAPER_DIR", "")
    monitor            = cfg.get("LAST_MONITOR", "")
    scaling            = cfg.get("LAST_SCALING", "fill") or "fill"
    blur_radius        = int(cfg.get("OVERVIEW_BLUR", "0") or "0")

    if not we_install_dir or not wallpaper_dir:
        print("wallpaper-manager: no wallpaper configured — run the GUI first.",
              file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(wallpaper_dir):
        print(f"wallpaper-manager: wallpaper directory not found: {wallpaper_dir}",
              file=sys.stderr)
        sys.exit(1)

    if not monitor:
        monitors = get_monitors()
        if not monitors:
            print("wallpaper-manager: no monitors detected (is wlr-randr installed?)",
                  file=sys.stderr)
            sys.exit(1)
        monitor = monitors[0]

    # Kill any leftover engine from a previous session
    try:
        subprocess.run(["pkill", "-f", ENGINE_BIN], capture_output=True)
    except Exception:
        pass

    screenshot_dir  = os.path.expanduser("~/.cache/wallpaper-manager")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "current-wallpaper.png")
    try:
        os.remove(screenshot_path)
    except FileNotFoundError:
        pass

    cmd = [
        ENGINE_BIN,
        "--assets-dir", os.path.join(we_install_dir, ASSETS_SUBPATH),
        wallpaper_dir,
        "--silent",
        "--screen-root", monitor,
        "--scaling", scaling,
        "--screenshot", screenshot_path,
        "--screenshot-delay", "10",
    ]

    try:
        subprocess.Popen(
            cmd,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print(f"wallpaper-manager: {ENGINE_BIN} not found.", file=sys.stderr)
        sys.exit(1)

    result = notify_niri_overview(monitor, screenshot_path, blur_radius)
    if not result["overview_updated"]:
        print("wallpaper-manager: screenshot timeout; niri overview not updated.",
              file=sys.stderr)
    elif result["noctalia_error"]:
        print(
            "wallpaper-manager: noctalia-shell not updated: "
            f"{result['noctalia_error']}",
            file=sys.stderr,
        )



class WallpaperRow(Gtk.ListBoxRow):
    def __init__(self, wallpaper):
        super().__init__()
        self.wallpaper = wallpaper
        self._build()
        if wallpaper["preview"]:
            threading.Thread(
                target=self._load_thumb,
                args=(wallpaper["preview"],),
                daemon=True
            ).start()

    def _build(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        hbox.set_margin_start(8)
        hbox.set_margin_end(8)
        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        self.add(hbox)

        # Thumbnail placeholder
        self._thumb = Gtk.Image.new_from_icon_name(
            "image-x-generic-symbolic", Gtk.IconSize.DND
        )
        self._thumb.set_size_request(THUMB_W, THUMB_H)
        hbox.pack_start(self._thumb, False, False, 0)

        # Text info
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        vbox.set_valign(Gtk.Align.CENTER)
        hbox.pack_start(vbox, True, True, 0)

        title_lbl = Gtk.Label(label=self.wallpaper["title"])
        title_lbl.set_halign(Gtk.Align.START)
        title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        title_lbl.set_max_width_chars(60)
        vbox.pack_start(title_lbl, False, False, 0)

        type_text = (self.wallpaper["type"] or "unknown").capitalize()
        type_lbl = Gtk.Label(label=type_text)
        type_lbl.set_halign(Gtk.Align.START)
        type_lbl.get_style_context().add_class("dim-label")
        vbox.pack_start(type_lbl, False, False, 0)

    def _load_thumb(self, path):
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                path, THUMB_W, THUMB_H, True
            )
            GLib.idle_add(self._thumb.set_from_pixbuf, pixbuf)
        except Exception:
            pass

    def matches(self, query):
        """Return True if the wallpaper matches the search query."""
        q = query.casefold()
        return (q in self.wallpaper["title"].casefold() or
                q in (self.wallpaper["type"] or "").casefold())

# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class WallpaperManagerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="壁纸管理器")
        self.set_default_size(800, 600)
        cfg = load_config()
        self._we_install_dir = cfg["WE_INSTALL_DIR"]
        self._build_ui()
        if self._we_install_dir:
            self._dir_entry.set_text(self._we_install_dir)
            self._blur_spin.set_value(int(cfg.get("OVERVIEW_BLUR", 0)))
            self._refresh_wallpapers()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        # Header bar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "壁纸管理器"
        header.props.subtitle = "linux-wallpaperengine"
        self.set_titlebar(header)

        # Search entry in header
        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text("搜索壁纸…")
        self._search_entry.connect("search-changed", self._on_search_changed)
        header.pack_start(self._search_entry)

        # Start engine button
        self._start_btn = Gtk.Button(label="启动引擎")
        self._start_btn.get_style_context().add_class("suggested-action")
        self._start_btn.connect("clicked", self._on_start_engine)
        header.pack_end(self._start_btn)

        # Root container
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root)

        # ---- Steam directory row ----
        dir_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dir_bar.set_margin_start(12)
        dir_bar.set_margin_end(12)
        dir_bar.set_margin_top(10)
        dir_bar.set_margin_bottom(10)
        root.pack_start(dir_bar, False, False, 0)

        dir_bar.pack_start(Gtk.Label(label="Steam 目录:"), False, False, 0)

        self._dir_entry = Gtk.Entry()
        self._dir_entry.set_placeholder_text("请选择 Steam 安装目录…")
        self._dir_entry.set_hexpand(True)
        self._dir_entry.connect("activate", self._on_set_dir)
        dir_bar.pack_start(self._dir_entry, True, True, 0)

        browse_btn = Gtk.Button(label="浏览…")
        browse_btn.connect("clicked", self._on_browse)
        dir_bar.pack_start(browse_btn, False, False, 0)

        confirm_btn = Gtk.Button(label="确定")
        confirm_btn.connect("clicked", self._on_set_dir)
        dir_bar.pack_start(confirm_btn, False, False, 0)

        # ---- Monitor / scaling row ----
        opt_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        opt_bar.set_margin_start(12)
        opt_bar.set_margin_end(12)
        opt_bar.set_margin_bottom(10)
        root.pack_start(opt_bar, False, False, 0)

        opt_bar.pack_start(Gtk.Label(label="显示器:"), False, False, 0)

        self._monitor_combo = Gtk.ComboBoxText()
        self._monitor_combo.append_text("自动检测")
        self._monitor_combo.set_active(0)
        opt_bar.pack_start(self._monitor_combo, False, False, 0)

        refresh_mon_btn = Gtk.Button(label="↺")
        refresh_mon_btn.set_tooltip_text("刷新显示器列表")
        refresh_mon_btn.connect("clicked", self._on_refresh_monitors)
        opt_bar.pack_start(refresh_mon_btn, False, False, 0)

        opt_bar.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4
        )
        opt_bar.pack_start(Gtk.Label(label="缩放模式:"), False, False, 0)

        self._scale_combo = Gtk.ComboBoxText()
        for mode in ("fill", "fit", "stretch", "default"):
            self._scale_combo.append_text(mode)
        self._scale_combo.set_active(0)
        opt_bar.pack_start(self._scale_combo, False, False, 0)

        opt_bar.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 4
        )
        opt_bar.pack_start(Gtk.Label(label="概览模糊:"), False, False, 0)

        blur_adj = Gtk.Adjustment(value=0, lower=0, upper=50,
                                  step_increment=1, page_increment=5)
        self._blur_spin = Gtk.SpinButton(adjustment=blur_adj, climb_rate=1, digits=0)
        self._blur_spin.set_tooltip_text("niri 概览背景高斯模糊半径（0 = 不模糊）")
        self._blur_spin.connect("value-changed", self._on_blur_changed)
        opt_bar.pack_start(self._blur_spin, False, False, 0)

        self._on_refresh_monitors(None)

        root.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0
        )

        # ---- Wallpaper list ----
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        root.pack_start(scroll, True, True, 0)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.set_activate_on_single_click(False)
        self._listbox.set_filter_func(self._filter_func)
        self._listbox.connect("row-activated", self._on_row_activated)
        scroll.add(self._listbox)

        placeholder = Gtk.Label(
            label="请先设置 Steam 安装目录\n"
                  "以加载已下载的壁纸列表"
        )
        placeholder.set_justify(Gtk.Justification.CENTER)
        placeholder.get_style_context().add_class("dim-label")
        placeholder.set_margin_top(80)
        placeholder.show()
        self._listbox.set_placeholder(placeholder)

        root.pack_start(
            Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0
        )

        # ---- Action bar ----
        action_bar = Gtk.ActionBar()
        root.pack_start(action_bar, False, False, 0)

        self._status_lbl = Gtk.Label(label="就绪")
        self._status_lbl.get_style_context().add_class("dim-label")
        action_bar.pack_start(self._status_lbl)

        refresh_btn = Gtk.Button(label="刷新列表")
        refresh_btn.connect("clicked", lambda _: self._refresh_wallpapers())
        action_bar.pack_start(refresh_btn)

        stop_btn = Gtk.Button(label="停止引擎")
        stop_btn.get_style_context().add_class("destructive-action")
        stop_btn.connect("clicked", self._on_stop_engine)
        action_bar.pack_end(stop_btn)

        apply_btn = Gtk.Button(label="应用壁纸")
        apply_btn.get_style_context().add_class("suggested-action")
        apply_btn.connect("clicked", self._on_apply_clicked)
        action_bar.pack_end(apply_btn)

    # ---------------------------------------------------------- Handlers --

    def _on_browse(self, _widget):
        dialog = Gtk.FileChooserDialog(
            title="选择 Steam 安装目录",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons("取消", Gtk.ResponseType.CANCEL,
                           "选择", Gtk.ResponseType.OK)
        if self._we_install_dir and os.path.isdir(self._we_install_dir):
            dialog.set_filename(self._we_install_dir)
        if dialog.run() == Gtk.ResponseType.OK:
            self._dir_entry.set_text(dialog.get_filename())
            self._on_set_dir(None)
        dialog.destroy()

    def _on_set_dir(self, _widget):
        path = self._dir_entry.get_text().strip()
        if not path:
            return
        if not os.path.isdir(path):
            self._show_error(f"目录不存在：{path}")
            return
        self._we_install_dir = os.path.realpath(path)
        self._dir_entry.set_text(self._we_install_dir)
        save_config(self._we_install_dir, self._blur_spin.get_value_as_int())
        self._refresh_wallpapers()

    def _on_blur_changed(self, _widget):
        save_config(self._we_install_dir, self._blur_spin.get_value_as_int())

    def _on_refresh_monitors(self, _widget):
        self._monitor_combo.remove_all()
        self._monitor_combo.append_text("自动检测")
        for name in get_monitors():
            self._monitor_combo.append_text(name)
        # Select first real monitor if available, else "自动检测"
        self._monitor_combo.set_active(
            1 if self._monitor_combo.get_model().__len__() > 1 else 0
        )

    def _on_search_changed(self, _widget):
        self._listbox.invalidate_filter()

    def _filter_func(self, row):
        query = self._search_entry.get_text().strip()
        if not query or not isinstance(row, WallpaperRow):
            return True
        return row.matches(query)

    def _on_row_activated(self, _listbox, row):
        """Double-click a row to apply immediately."""
        if isinstance(row, WallpaperRow):
            self._apply_wallpaper(row.wallpaper)

    def _on_apply_clicked(self, _widget):
        row = self._listbox.get_selected_row()
        if row is None:
            self._set_status("请先选择一个壁纸")
            return
        self._apply_wallpaper(row.wallpaper)

    def _on_start_engine(self, _widget):
        """Start engine with the first available wallpaper (mirrors --start)."""
        if not self._we_install_dir:
            self._show_error("请先设置 Steam 安装目录")
            return
        workshop_dir = os.path.join(self._we_install_dir, WORKSHOP_SUBPATH)
        first_wp = None
        try:
            dirs = sorted(e.path for e in os.scandir(workshop_dir) if e.is_dir())
            if dirs:
                first_wp = dirs[0]
        except Exception:
            pass

        monitor = self._selected_monitor()
        if not monitor:
            self._show_error("无法获取显示器信息，请检查 wlr-randr 是否已安装")
            return

        cmd = [ENGINE_BIN]
        if first_wp:
            cmd += [
                "--assets-dir", os.path.join(self._we_install_dir, ASSETS_SUBPATH),
                first_wp,
                "--silent",
                "--screen-root", monitor,
                "--scaling", self._scale_combo.get_active_text() or "fill",
            ]
        self._launch(cmd, "Wallpaper Engine 已启动")

    def _on_stop_engine(self, _widget):
        try:
            subprocess.run(["pkill", "-f", ENGINE_BIN], capture_output=True)
            self._set_status("已停止 linux-wallpaperengine")
        except Exception as exc:
            self._set_status(f"停止失败: {exc}")

    # -------------------------------------------------------- Core logic --

    def _refresh_wallpapers(self):
        if not self._we_install_dir:
            return
        self._set_status("正在扫描壁纸目录…")
        for row in self._listbox.get_children():
            self._listbox.remove(row)

        def _scan():
            wallpapers = scan_wallpapers(self._we_install_dir)
            GLib.idle_add(self._populate_list, wallpapers)

        threading.Thread(target=_scan, daemon=True).start()

    def _populate_list(self, wallpapers):
        for wp in wallpapers:
            self._listbox.add(WallpaperRow(wp))
        self._listbox.show_all()
        self._set_status(f"共找到 {len(wallpapers)} 个壁纸")

    def _apply_wallpaper(self, wallpaper):
        """Kill existing engine instance and launch with selected wallpaper."""
        if not self._we_install_dir:
            self._show_error("请先设置 Steam 安装目录")
            return
        monitor = self._selected_monitor()
        if not monitor:
            self._show_error("无法获取显示器信息，请检查 wlr-randr 是否已安装")
            return

        # Kill existing instance before applying a new one (mirrors --change)
        try:
            subprocess.run(["pkill", "-f", ENGINE_BIN], capture_output=True)
        except Exception:
            pass

        screenshot_dir = os.path.expanduser("~/.cache/wallpaper-manager")
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, "current-wallpaper.png")
        # Remove stale screenshot so _notify_niri_overview can detect the new one
        try:
            os.remove(screenshot_path)
        except FileNotFoundError:
            pass

        scaling = self._scale_combo.get_active_text() or "fill"
        cmd = [
            ENGINE_BIN,
            "--assets-dir", os.path.join(self._we_install_dir, ASSETS_SUBPATH),
            wallpaper["dir"],
            "--silent",
            "--screen-root", monitor,
            "--scaling", scaling,
            "--screenshot", screenshot_path,
            "--screenshot-delay", "10",
        ]
        # Persist last-used settings for --startup
        save_config(self._we_install_dir, self._blur_spin.get_value_as_int(),
                    wallpaper["dir"], monitor, scaling)
        self._launch(cmd, f"已应用：{wallpaper['title']}")
        blur = self._blur_spin.get_value_as_int()
        threading.Thread(
            target=self._notify_niri_overview,
            args=(wallpaper["title"], monitor, screenshot_path, blur),
            daemon=True,
        ).start()

    def _notify_niri_overview(self, title, monitor, screenshot_path, blur_radius):
        result = notify_niri_overview(monitor, screenshot_path, blur_radius)
        if result["overview_updated"]:
            status = f"已应用并通知 niri：{title}"
            if result["noctalia_notified"]:
                status += "；已刷新 noctalia-shell 配色"
            elif result["noctalia_error"]:
                status += f"；noctalia-shell 未更新（{result['noctalia_error']}）"
            GLib.idle_add(self._set_status, status)
        else:
            GLib.idle_add(self._set_status, f"已应用：{title}；但 niri 概览未更新")

    def _launch(self, cmd, success_msg):
        try:
            subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._set_status(success_msg)
        except FileNotFoundError:
            self._show_error(
                f"未找到 {ENGINE_BIN}，请确认 linux-wallpaperengine 已正确安装"
            )
        except Exception as exc:
            self._show_error(f"启动失败: {exc}")

    def _selected_monitor(self):
        text = self._monitor_combo.get_active_text()
        if text and text != "自动检测":
            return text
        monitors = get_monitors()
        return monitors[0] if monitors else None

    # ------------------------------------------------------- Helpers -----

    def _set_status(self, msg):
        GLib.idle_add(self._status_lbl.set_text, msg)

    def _show_error(self, msg):
        self._set_status(f"错误: {msg}")
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="操作出错",
            secondary_text=msg,
        )
        dialog.run()
        dialog.destroy()

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class WallpaperManagerApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_activate(self):
        windows = self.get_windows()
        if windows:
            windows[0].present()
            return
        win = WallpaperManagerWindow(self)
        win.show_all()


def main():
    import sys
    if "--startup" in sys.argv:
        startup_apply()
        return
    app = WallpaperManagerApp()
    sys.exit(app.run(sys.argv))


if __name__ == "__main__":
    main()
