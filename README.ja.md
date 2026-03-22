# 壁紙マネージャー GTK (Wallpaper Manager GTK)

`linux-wallpaperengine` 用の GTK4 + libadwaita グラフィカルインターフェースです。`noctalia-shell` と統合されており、モネ（Monet）アルゴリズムによる自動配色抽出とシステムテーマの更新をサポートしています。

[简体中文](./README.zh.md) | [English](./README.md) | [日本語](./README.ja.md)

## 特徴

- **Wallpaper Engine GUI**: Linux 上で Steam Workshop の壁紙を簡単に管理できます。
- **配色抽出 (Monet)**: 壁紙を適用すると、`noctalia-shell` の配色を自動的に更新します。
- **自動モニター検出**: 複数モニターに対応し、拡大縮小モード（Fill, Fit, Stretch など）をサポート。
- **セッションの永続化**: ログイン時に最後に使用した壁紙を自動的に復元します。
- **多言語対応**: 日本語、簡体字中国語、英語を内蔵サポート。

## 動作要件

### システムの依存関係

#### Arch Linux
```bash
sudo pacman -S python-gobject gtk4 libadwaita wlr-randr
```

#### Debian/Ubuntu
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 wlr-randr
```

### エンジンと統合
- [linux-wallpaperengine](https://github.com/Al some-projects/linux-wallpaperengine): 壁紙を再生するコアエンジン。
- [noctalia-shell](https://github.com/Noctalia/noctalia-shell): (任意) 配色の抽出とテーマの更新用。
- [wlr-randr](https://github.com/emersion/wlr-randr): モニター情報の検出用。

## インストール

このプロジェクトは `uv` を使用して依存関係を管理しています：

```bash
uv sync
```

開発用に型チェックも行う場合：

```bash
uv sync --dev
```

## 使い方

### アプリケーションの起動

`uv` を使用した推奨の起動方法：

```bash
uv run wallpaper-manager-gtk
```

### セッションの復元

セッション開始時（compositor の自動起動設定など）に前回の壁紙を復元する場合：

```bash
uv run wallpaper-manager-gtk --startup
```

### デスクトップファイル

ランチャーから起動できるようにデスクトップファイルをコピーします：

```bash
cp wallpaper-manager-gtk.desktop ~/.local/share/applications/
```

## 設定

設定は `~/.config/wallpaper-manager/config` に保存されます。

このアプリは `noctalia-shell` との互換性を考慮して設計されています。壁紙が切り替わるたびに独自のスクリーンショットパスを生成し、`noctalia-shell` の配色抽出をトリガーします。

## 開発

このプロジェクトは `mypy` による厳格な型チェックを行っています：

```bash
uv run mypy
```
