#!/usr/bin/env python3
import sys
import os
import gi
import signal

gi.require_version('Gtk', '3.0')  # Specify GTK 3.0 version
from gi.repository import Gtk, GLib

from gui import MainWindow
from config_manager import ConfigManager
from v2ray_controller import V2RayController


class V2RayClientApp:
    def __init__(self):
        self.config_manager = ConfigManager()
        # Get the absolute path to the Xray binary
        script_dir = os.path.dirname(os.path.abspath(__file__))
        xray_path = os.path.join(script_dir, '../bin/xray')

        self.v2ray_controller = V2RayController(
            xray_binary=xray_path
        )
        self.window = MainWindow(self)

    def run(self):
        self.window.show_all()
        Gtk.main()


def handle_exit(signum, frame):
    app.stop()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    app = V2RayClientApp()
    app.run()
