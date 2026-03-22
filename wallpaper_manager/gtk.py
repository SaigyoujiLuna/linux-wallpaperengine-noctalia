"""Centralized GTK imports and GI version declarations."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, Gdk, Gio, GLib, GObject, Gtk, Pango

__all__ = ["Adw", "Gdk", "Gio", "GLib", "GObject", "Gtk", "Pango"]
