# 壁纸管理器 GTK (Wallpaper Manager GTK)

一个基于 `linux-wallpaperengine` 的 GTK4 + libadwaita 图形界面壁纸管理器。集成了 `noctalia-shell` 的莫奈（Monet）取色功能，可在设置壁纸后自动更新系统配色方案。

[简体中文](./README.zh.md) | [English](./README.md) | [日本語](./README.ja.md)

## 特性

- **Wallpaper Engine 图形界面**: 在 Linux 上轻松管理 Steam Workshop 下载的壁纸。
- **莫奈取色集成**: 设置壁纸时自动触发 `noctalia-shell` 的配色更新。
- **自动显示器检测**: 支持多显示器及多种缩放模式（填充、适应、拉伸等）。
- **会话持久化**: 登录时自动恢复上次使用的壁纸。
- **多语言支持**: 内置简体中文、英语、日语支持，随系统 locale 自动切换。

## 依赖

### 系统依赖

#### Arch Linux
```bash
# Arch Linux
sudo pacman -S python-gobject gtk4 libadwaita wlr-randr
```

#### Debian/Ubuntu
```bash
# Debian/Ubuntu
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 wlr-randr
```

### 核心引擎与集成
- [linux-wallpaperengine](https://github.com/Alsome-projects/linux-wallpaperengine): 核心播放引擎。
- [noctalia-shell](https://github.com/Noctalia/noctalia-shell): (可选) 用于配色提取与外壳集成。
- [wlr-randr](https://github.com/emersion/wlr-randr): 用于检测显示器信息。

## 安装

项目依赖由 `uv` 管理：

```bash
uv sync
```

开发时可额外同步类型检查依赖：

```bash
uv sync --dev
```

## 运行

### 运行应用

推荐直接使用 `uv` 暴露的脚本入口：

```bash
uv run wallpaper-manager-gtk
```

### 启动恢复

在登录会话启动时恢复上次壁纸（可加入 compositor 的自启动脚本）：

```bash
uv run wallpaper-manager-gtk --startup
```

### 桌面快捷方式

将桌面文件复制到本地应用目录以在启动器中显示：

```bash
cp wallpaper-manager-gtk.desktop ~/.local/share/applications/
```

## 配置文件

运行时配置保存在：`~/.config/wallpaper-manager/config`

应用会为每次切换生成新的截图文件路径，以确保 `noctalia-shell` 的概览页同步生效并触发配色更新。

## 类型检查

项目已配置 `mypy` 严格模式，可使用以下命令检查：

```bash
uv run mypy
```
