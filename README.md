# Wallpaper Manager GTK

A GTK4 + libadwaita graphical interface for `linux-wallpaperengine`, integrated with `noctalia-shell` for automatic color extraction and system theme updates.

[简体中文](./README.zh.md) | [English](./README.md) | [日本語](./README.ja.md)

## Features

- **GUI for Wallpaper Engine**: Easy management of your Steam Workshop wallpapers on Linux.
- **Monet Color Extraction**: Automatically updates `noctalia-shell` color schemes based on the current wallpaper.
- **Auto Monitor Detection**: Supports multiple monitors and different scaling modes (Fill, Fit, Stretch, etc.).
- **Session Persistence**: Restores your last-used wallpaper on login.
- **Multi-language**: Built-in support for English, Simplified Chinese, and Japanese.

## Prerequisites

### System Dependencies

#### Arch Linux
```bash
sudo pacman -S python-gobject gtk4 libadwaita wlr-randr
```

#### Debian/Ubuntu
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 wlr-randr
```

### Engines and Integrations
- [linux-wallpaperengine](https://github.com/Almamu/linux-wallpaperengine): Core engine to play wallpapers.
- [noctalia-shell](https://github.com/noctalia-dev/noctalia-shell): For Monet color extraction and theme updates.
- [wlr-randr](https://github.com/emersion/wlr-randr): For monitor information detection.

## Installation

This project uses `uv` for dependency management:

```bash
uv sync
```

For development with type-checking:

```bash
uv sync --dev
```

## Usage

### Run Application

Recommended way using `uv`:

```bash
uv run wallpaper-manager-gtk
```

### Session Restore

To restore the last used wallpaper on session startup (e.g., in your compositor's autostart):

```bash
uv run wallpaper-manager-gtk --startup
```

### Desktop Entry

Copy the desktop entry to your local applications directory for launcher support:

```bash
cp wallpaper-manager-gtk.desktop ~/.local/share/applications/
```

## Configuration

Configuration is stored at `~/.config/wallpaper-manager/config`. 

This application is designed to be compatible with `noctalia-shell`. It generates unique screenshot paths for each wallpaper switch to trigger `noctalia-shell`'s overview and color extraction updates.

## Development

The project uses `mypy` for strict type checking:

```bash
uv run mypy
```
