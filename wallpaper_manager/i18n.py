from __future__ import annotations

import os
from typing import Final, Literal, cast

SupportedLocale = Literal["zh", "en", "ja"]

DEFAULT_LOCALE: Final[SupportedLocale] = "zh"
SUPPORTED_LOCALES: Final[tuple[SupportedLocale, ...]] = ("zh", "en", "ja")
LOCALE_ENV_KEYS: Final[tuple[str, ...]] = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")

TRANSLATIONS: Final[dict[SupportedLocale, dict[str, str]]] = {
    "zh": {
        "app.name": "壁纸管理器",
        "ui.auto_monitor": "自动检测",
        "ui.monitor": "显示器",
        "ui.scale_mode": "缩放模式",
        "ui.refresh_monitors": "刷新显示器列表",
        "ui.status": "状态",
        "ui.refresh_wallpapers": "刷新壁纸列表",
        "ui.stop_engine": "停止壁纸引擎",
        "ui.apply_wallpaper": "应用选中的壁纸",
        "ui.search_placeholder": "搜索壁纸…",
        "ui.settings": "设置",
        "ui.steam_directory": "Steam 目录",
        "ui.browse_steam_directory": "浏览 Steam 目录",
        "ui.save_refresh_wallpapers": "保存并刷新壁纸目录",
        "ui.wallpaper_source": "壁纸来源",
        "ui.wallpaper_source_desc": "配置 Steam 安装目录以扫描已下载的 Wallpaper Engine 壁纸。",
        "ui.overview": "播放说明",
        "ui.overview_desc": "显示器与缩放模式已经保留在主页面，便于切换壁纸时快速调整。",
        "ui.niri_overview_background": "niri 概览背景",
        "ui.niri_overview_background_desc": "请在 niri 配置中单独设置该背景来源。",
        "ui.select_steam_directory": "选择 Steam 安装目录",
        "ui.empty.no_wallpapers_title": "还没有可显示的壁纸",
        "ui.empty.no_wallpapers_desc": "请先设置 Steam 安装目录，以加载已下载的壁纸列表。",
        "ui.empty.scanning_title": "正在扫描壁纸",
        "ui.empty.scanning_desc": "请稍候，应用正在读取 Wallpaper Engine 壁纸目录。",
        "ui.empty.not_found_title": "没有找到壁纸",
        "ui.empty.not_found_desc": "当前 Steam 目录下没有可用的 Wallpaper Engine 壁纸。",
        "ui.empty.no_match_title": "没有匹配结果",
        "ui.empty.no_match_desc": "没有找到与“{query}”匹配的壁纸。",
        "ui.error_heading": "操作出错",
        "ui.confirm": "确定",
        "scale.fill": "填充",
        "scale.fit": "适应",
        "scale.stretch": "拉伸",
        "scale.default": "默认",
        "wallpaper_type.unknown": "未知",
        "wallpaper_type.scene": "场景",
        "wallpaper_type.video": "视频",
        "wallpaper_type.web": "网页",
        "wallpaper_type.application": "应用",
        "wallpaper_type.preset": "预设",
        "status.ready": "就绪",
        "status.set_steam_dir_first": "请先设置 Steam 安装目录",
        "status.scanning_wallpapers": "正在扫描壁纸目录…",
        "status.wallpaper_count": "共找到 {count} 个壁纸",
        "status.select_wallpaper_first": "请先选择一个壁纸",
        "status.engine_stopped": "已停止 linux-wallpaperengine",
        "status.engine_not_running": "未发现运行中的 linux-wallpaperengine",
        "status.applied_wallpaper": "已应用：{title}",
        "status.noctalia_updated": "；已刷新 noctalia-shell 壁纸与配色",
        "status.noctalia_not_updated": "；noctalia-shell 未更新（{error}）",
        "status.enter_steam_dir_first": "请先输入 Steam 安装目录",
        "status.invalid_wallpaper_selected": "请先选择一个有效的壁纸",
        "status.error_prefix": "错误: {message}",
        "error.dir_not_found": "目录不存在：{path}",
        "error.engine_not_found": "未找到 {engine_bin}，请确认 linux-wallpaperengine 已正确安装",
        "error.launch_failed": "启动失败: {error}",
        "error.monitor_detection_failed": "无法获取显示器信息，请检查 wlr-randr 是否已安装",
        "service.qs_not_found": "未找到 qs",
        "service.noctalia_ipc_ready_timeout": "等待 noctalia-shell IPC 就绪超时",
        "service.noctalia_probe_failed": "探测 noctalia-shell 启动状态失败: {error}",
        "service.noctalia_target_not_registered": "noctalia-shell 已启动，但 wallpaper IPC target 尚未注册",
        "service.noctalia_ipc_not_ready": "noctalia-shell IPC 尚未就绪",
        "service.noctalia_startup_timeout": "等待 noctalia-shell 启动超时",
        "service.screenshot_read_failed": "读取壁纸截图失败: {error}",
        "service.screenshot_timeout": "等待壁纸截图生成超时",
        "service.noctalia_response_timeout": "等待 noctalia-shell 响应超时",
        "service.noctalia_notify_failed": "通知 noctalia-shell 失败: {error}",
        "service.noctalia_ipc_call_failed": "noctalia-shell IPC 调用失败",
        "startup.no_wallpaper_configured": "未配置壁纸，请先运行图形界面。",
        "startup.wallpaper_dir_not_found": "壁纸目录不存在：{path}",
        "startup.no_monitors_detected": "未检测到显示器（是否已安装 wlr-randr？）",
        "startup.engine_not_found": "未找到 {engine_bin}，请确认 linux-wallpaperengine 已正确安装。",
        "startup.engine_launch_failed": "启动 {engine_bin} 失败：{error}",
    },
    "en": {
        "app.name": "Wallpaper Manager",
        "ui.auto_monitor": "Auto detect",
        "ui.monitor": "Monitor",
        "ui.scale_mode": "Scaling mode",
        "ui.refresh_monitors": "Refresh monitor list",
        "ui.status": "Status",
        "ui.refresh_wallpapers": "Refresh wallpaper list",
        "ui.stop_engine": "Stop wallpaper engine",
        "ui.apply_wallpaper": "Apply selected wallpaper",
        "ui.search_placeholder": "Search wallpapers…",
        "ui.settings": "Settings",
        "ui.steam_directory": "Steam directory",
        "ui.browse_steam_directory": "Browse Steam directory",
        "ui.save_refresh_wallpapers": "Save and refresh wallpapers",
        "ui.wallpaper_source": "Wallpaper source",
        "ui.wallpaper_source_desc": "Set the Steam install directory to scan downloaded Wallpaper Engine wallpapers.",
        "ui.overview": "Playback notes",
        "ui.overview_desc": "Monitor and scaling controls stay on the main page for quick adjustments while switching wallpapers.",
        "ui.niri_overview_background": "niri overview background",
        "ui.niri_overview_background_desc": "Configure that background source separately in your niri config.",
        "ui.select_steam_directory": "Select Steam install directory",
        "ui.empty.no_wallpapers_title": "No wallpapers to show yet",
        "ui.empty.no_wallpapers_desc": "Set the Steam install directory first to load downloaded wallpapers.",
        "ui.empty.scanning_title": "Scanning wallpapers",
        "ui.empty.scanning_desc": "Please wait while the app reads the Wallpaper Engine wallpaper directory.",
        "ui.empty.not_found_title": "No wallpapers found",
        "ui.empty.not_found_desc": "No usable Wallpaper Engine wallpapers were found in the current Steam directory.",
        "ui.empty.no_match_title": "No matches found",
        "ui.empty.no_match_desc": "No wallpapers matched “{query}”.",
        "ui.error_heading": "Operation failed",
        "ui.confirm": "OK",
        "scale.fill": "Fill",
        "scale.fit": "Fit",
        "scale.stretch": "Stretch",
        "scale.default": "Default",
        "wallpaper_type.unknown": "Unknown",
        "wallpaper_type.scene": "Scene",
        "wallpaper_type.video": "Video",
        "wallpaper_type.web": "Web",
        "wallpaper_type.application": "Application",
        "wallpaper_type.preset": "Preset",
        "status.ready": "Ready",
        "status.set_steam_dir_first": "Set the Steam install directory first",
        "status.scanning_wallpapers": "Scanning wallpaper directories…",
        "status.wallpaper_count": "Found {count} wallpapers",
        "status.select_wallpaper_first": "Select a wallpaper first",
        "status.engine_stopped": "Stopped linux-wallpaperengine",
        "status.engine_not_running": "No running linux-wallpaperengine process found",
        "status.applied_wallpaper": "Applied: {title}",
        "status.noctalia_updated": "; refreshed noctalia-shell wallpaper and colors",
        "status.noctalia_not_updated": "; noctalia-shell was not updated ({error})",
        "status.enter_steam_dir_first": "Enter the Steam install directory first",
        "status.invalid_wallpaper_selected": "Select a valid wallpaper first",
        "status.error_prefix": "Error: {message}",
        "error.dir_not_found": "Directory does not exist: {path}",
        "error.engine_not_found": "{engine_bin} was not found. Make sure linux-wallpaperengine is installed",
        "error.launch_failed": "Launch failed: {error}",
        "error.monitor_detection_failed": "Could not detect monitors. Is wlr-randr installed?",
        "service.qs_not_found": "qs was not found",
        "service.noctalia_ipc_ready_timeout": "Timed out waiting for noctalia-shell IPC to become ready",
        "service.noctalia_probe_failed": "Failed to probe noctalia-shell startup state: {error}",
        "service.noctalia_target_not_registered": "noctalia-shell is running, but the wallpaper IPC target is not registered yet",
        "service.noctalia_ipc_not_ready": "noctalia-shell IPC is not ready yet",
        "service.noctalia_startup_timeout": "Timed out waiting for noctalia-shell startup",
        "service.screenshot_read_failed": "Failed to read wallpaper screenshot: {error}",
        "service.screenshot_timeout": "Timed out waiting for the wallpaper screenshot to be generated",
        "service.noctalia_response_timeout": "Timed out waiting for noctalia-shell to respond",
        "service.noctalia_notify_failed": "Failed to notify noctalia-shell: {error}",
        "service.noctalia_ipc_call_failed": "noctalia-shell IPC call failed",
        "startup.no_wallpaper_configured": "No wallpaper is configured. Run the GUI first.",
        "startup.wallpaper_dir_not_found": "Wallpaper directory not found: {path}",
        "startup.no_monitors_detected": "No monitors were detected (is wlr-randr installed?)",
        "startup.engine_not_found": "{engine_bin} was not found. Make sure linux-wallpaperengine is installed.",
        "startup.engine_launch_failed": "Failed to launch {engine_bin}: {error}",
    },
    "ja": {
        "app.name": "壁紙マネージャー",
        "ui.auto_monitor": "自動検出",
        "ui.monitor": "モニター",
        "ui.scale_mode": "拡大縮小モード",
        "ui.refresh_monitors": "モニター一覧を更新",
        "ui.status": "状態",
        "ui.refresh_wallpapers": "壁紙一覧を更新",
        "ui.stop_engine": "壁紙エンジンを停止",
        "ui.apply_wallpaper": "選択した壁紙を適用",
        "ui.search_placeholder": "壁紙を検索…",
        "ui.settings": "設定",
        "ui.steam_directory": "Steam ディレクトリ",
        "ui.browse_steam_directory": "Steam ディレクトリを参照",
        "ui.save_refresh_wallpapers": "保存して壁紙を再読み込み",
        "ui.wallpaper_source": "壁紙ソース",
        "ui.wallpaper_source_desc": "ダウンロード済みの Wallpaper Engine 壁紙を走査するために Steam のインストール先を設定します。",
        "ui.overview": "再生メモ",
        "ui.overview_desc": "モニターと拡大縮小モードは、壁紙切り替え時にすばやく調整できるようメイン画面に残しています。",
        "ui.niri_overview_background": "niri 概要背景",
        "ui.niri_overview_background_desc": "この背景ソースは niri の設定で個別に指定してください。",
        "ui.select_steam_directory": "Steam のインストール先を選択",
        "ui.empty.no_wallpapers_title": "表示できる壁紙がまだありません",
        "ui.empty.no_wallpapers_desc": "ダウンロード済み壁紙を読み込むには、先に Steam のインストール先を設定してください。",
        "ui.empty.scanning_title": "壁紙を走査しています",
        "ui.empty.scanning_desc": "Wallpaper Engine の壁紙ディレクトリを読み込んでいます。しばらくお待ちください。",
        "ui.empty.not_found_title": "壁紙が見つかりません",
        "ui.empty.not_found_desc": "現在の Steam ディレクトリに利用可能な Wallpaper Engine 壁紙が見つかりませんでした。",
        "ui.empty.no_match_title": "一致する結果がありません",
        "ui.empty.no_match_desc": "“{query}” に一致する壁紙は見つかりませんでした。",
        "ui.error_heading": "操作エラー",
        "ui.confirm": "OK",
        "scale.fill": "塗りつぶし",
        "scale.fit": "フィット",
        "scale.stretch": "引き伸ばし",
        "scale.default": "既定",
        "wallpaper_type.unknown": "不明",
        "wallpaper_type.scene": "シーン",
        "wallpaper_type.video": "動画",
        "wallpaper_type.web": "Web",
        "wallpaper_type.application": "アプリ",
        "wallpaper_type.preset": "プリセット",
        "status.ready": "準備完了",
        "status.set_steam_dir_first": "先に Steam のインストール先を設定してください",
        "status.scanning_wallpapers": "壁紙ディレクトリを走査しています…",
        "status.wallpaper_count": "{count} 個の壁紙が見つかりました",
        "status.select_wallpaper_first": "先に壁紙を選択してください",
        "status.engine_stopped": "linux-wallpaperengine を停止しました",
        "status.engine_not_running": "実行中の linux-wallpaperengine は見つかりませんでした",
        "status.applied_wallpaper": "適用しました: {title}",
        "status.noctalia_updated": "；noctalia-shell の壁紙と配色を更新しました",
        "status.noctalia_not_updated": "；noctalia-shell は更新されませんでした（{error}）",
        "status.enter_steam_dir_first": "先に Steam のインストール先を入力してください",
        "status.invalid_wallpaper_selected": "有効な壁紙を選択してください",
        "status.error_prefix": "エラー: {message}",
        "error.dir_not_found": "ディレクトリが存在しません: {path}",
        "error.engine_not_found": "{engine_bin} が見つかりません。linux-wallpaperengine がインストールされているか確認してください",
        "error.launch_failed": "起動に失敗しました: {error}",
        "error.monitor_detection_failed": "モニター情報を取得できません。wlr-randr がインストールされているか確認してください",
        "service.qs_not_found": "qs が見つかりません",
        "service.noctalia_ipc_ready_timeout": "noctalia-shell IPC の準備完了待ちがタイムアウトしました",
        "service.noctalia_probe_failed": "noctalia-shell の起動状態確認に失敗しました: {error}",
        "service.noctalia_target_not_registered": "noctalia-shell は起動していますが、wallpaper IPC ターゲットがまだ登録されていません",
        "service.noctalia_ipc_not_ready": "noctalia-shell IPC はまだ準備できていません",
        "service.noctalia_startup_timeout": "noctalia-shell の起動待ちがタイムアウトしました",
        "service.screenshot_read_failed": "壁紙スクリーンショットの読み取りに失敗しました: {error}",
        "service.screenshot_timeout": "壁紙スクリーンショットの生成待ちがタイムアウトしました",
        "service.noctalia_response_timeout": "noctalia-shell の応答待ちがタイムアウトしました",
        "service.noctalia_notify_failed": "noctalia-shell への通知に失敗しました: {error}",
        "service.noctalia_ipc_call_failed": "noctalia-shell IPC 呼び出しに失敗しました",
        "startup.no_wallpaper_configured": "壁紙が設定されていません。先に GUI を起動してください。",
        "startup.wallpaper_dir_not_found": "壁紙ディレクトリが見つかりません: {path}",
        "startup.no_monitors_detected": "モニターが見つかりませんでした（wlr-randr はインストールされていますか？）",
        "startup.engine_not_found": "{engine_bin} が見つかりません。linux-wallpaperengine がインストールされているか確認してください。",
        "startup.engine_launch_failed": "{engine_bin} の起動に失敗しました: {error}",
    },
}


def _normalize_locale(value: str) -> SupportedLocale | None:
    candidate = value.strip()
    if not candidate:
        return None
    candidate = candidate.split(":", 1)[0]
    candidate = candidate.split(".", 1)[0]
    candidate = candidate.split("@", 1)[0]
    candidate = candidate.replace("-", "_")
    language = candidate.split("_", 1)[0].casefold()
    if language in SUPPORTED_LOCALES:
        return cast(SupportedLocale, language)
    return None


def get_locale() -> SupportedLocale:
    for key in LOCALE_ENV_KEYS:
        raw_value = os.environ.get(key)
        if raw_value is None:
            continue
        locale_code = _normalize_locale(raw_value)
        if locale_code is not None:
            return locale_code
    return DEFAULT_LOCALE


ACTIVE_LOCALE: Final[SupportedLocale] = get_locale()


def tr(key: str, **kwargs: object) -> str:
    template = TRANSLATIONS[ACTIVE_LOCALE].get(key, TRANSLATIONS[DEFAULT_LOCALE].get(key, key))
    return template.format(**kwargs)


def translate_scale_mode(mode: str) -> str:
    return tr(f"scale.{mode}")


def translate_wallpaper_type(wallpaper_type: str) -> str:
    normalized = wallpaper_type.strip().casefold() or "unknown"
    key = f"wallpaper_type.{normalized}"
    if key in TRANSLATIONS[ACTIVE_LOCALE] or key in TRANSLATIONS[DEFAULT_LOCALE]:
        return tr(key)
    return wallpaper_type.capitalize() if wallpaper_type else tr("wallpaper_type.unknown")
