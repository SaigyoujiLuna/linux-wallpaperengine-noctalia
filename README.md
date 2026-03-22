# Linux-WallpaperEngine Noctalia shell Adapter

基于 `linux-wallpaperengine` + noctalia-shell wallpaper manager

## 依赖

系统依赖：

```bash
# Arch Linux
sudo pacman -S python-gobject gtk4 libadwaita

# Debian/Ubuntu
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
```

Python 依赖与虚拟环境由 `uv` 管理：

```bash
uv sync
```

开发时可额外同步类型检查依赖：

```bash
uv sync --dev
```

## 运行

推荐直接使用 `uv` 暴露的脚本入口：

```bash
uv run wallpaper-manager-gtk
```

也可以使用模块入口：

```bash
uv run python -m wallpaper_manager
```

旧的顶层脚本仍可用：

```bash
uv run wallpaper-manager-gtk.py
```

应用会根据系统 locale 自动选择界面语言；当前内置支持简体中文、English、Japanese。

## 类型检查

项目已配置 `mypy` 严格模式，可使用以下命令检查：

```bash
uv run mypy
```

## 启动恢复

登录会话启动时恢复上次壁纸：

```bash
uv run wallpaper-manager-gtk --startup
```


## 桌面快捷方式

将桌面文件复制到本地应用目录：

```bash
cp wallpaper-manager-gtk.desktop ~/.local/share/applications/
```

## 配置文件

运行时配置与 shell 版本兼容，统一保存在：

```text
~/.config/wallpaper-manager/config
```

由于 `noctalia-shell` 的壁纸服务按“路径变化”触发切换，应用会为每次切换生成新的截图文件路径，确保概览页同步生效。
