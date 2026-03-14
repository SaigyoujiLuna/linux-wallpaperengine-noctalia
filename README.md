# 壁纸管理器 GTK

基于 `wallpaper-manager.sh` 逻辑的 GTK3 图形界面壁纸选择器。

## 功能

| 功能 | 说明 |
|------|------|
| 配置持久化 | 与 shell 脚本共享同一配置文件 `~/.config/wallpaper-manager/config` |
| 壁纸列表 | 自动扫描 Workshop 目录，显示缩略图与标题 |
| 搜索过滤 | 实时按名称/类型搜索壁纸 |
| 显示器选择 | 通过 `wlr-randr` 自动检测，支持多显示器 |
| 缩放模式 | fill / fit / stretch / default |
| 一键应用 | 单击选中后点"应用壁纸"，或双击直接应用 |
| 启动/停止引擎 | 对应 `--start` 和 `pkill linux-wallpaperengine` |

## 依赖

```
python3
python3-gi          (PyGObject)
gir1.2-gtk-3.0
linux-wallpaperengine
wlr-randr           (Wayland 显示器信息)
```

安装 Python 依赖（Arch Linux）：
```bash
sudo pacman -S python-gobject gtk3
```

安装 Python 依赖（Debian/Ubuntu）：
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

## 运行

```bash
python3 wallpaper-manager-gtk.py
```

或安装桌面快捷方式：
```bash
cp wallpaper-manager-gtk.desktop ~/.local/share/applications/
```

## 界面说明

```
┌─────────────────────────────────────────────────────┐
│ [搜索壁纸…]          壁纸管理器       [启动引擎]    │
├─────────────────────────────────────────────────────┤
│ Steam 目录: [/path/to/steam/…        ] [浏览…][确定]│
│ 显示器: [DP-1 ▾] [↺]  缩放模式: [fill ▾]           │
├─────────────────────────────────────────────────────┤
│ [缩略图] My Wallpaper 1                             │
│          Scene                                      │
├─────────────────────────────────────────────────────│
│ [缩略图] My Wallpaper 2   ← 选中/双击即应用         │
│          Video                                      │
├─────────────────────────────────────────────────────┤
│ 就绪   [刷新列表]            [停止引擎] [应用壁纸]  │
└─────────────────────────────────────────────────────┘
```

## 配置文件格式

与 `wallpaper-manager.sh` 完全兼容：

```
# ~/.config/wallpaper-manager/config
WE_INSTALL_DIR=/home/user/.local/share/Steam
```
