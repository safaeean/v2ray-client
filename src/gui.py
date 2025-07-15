from gi.repository import Gtk, GObject


class MainWindow(Gtk.Window):
    def __init__(self, app):
        super().__init__(title="V2Ray Client")
        self.app = app
        self.set_default_size(600, 400)

        self.connect("destroy", Gtk.main_quit)

        # Main layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.box)

        # Add server button
        self.add_button = Gtk.Button(label="Add Server")
        self.add_button.connect("clicked", self.on_add_server)
        self.box.pack_start(self.add_button, False, False, 0)

        # Server list
        self.scrolled_window = Gtk.ScrolledWindow()
        self.server_list = Gtk.ListBox()
        self.server_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.server_list.connect("row-activated", self.on_server_activated)
        self.scrolled_window.add(self.server_list)
        self.box.pack_start(self.scrolled_window, True, True, 0)

        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.box.pack_end(self.status_bar, False, False, 0)

        # Load servers
        self.refresh_server_list()

    def refresh_server_list(self):
        """Refresh the list of servers from config"""
        # Clear existing rows
        for row in self.server_list.get_children():
            self.server_list.remove(row)

        # Add servers
        servers = self.app.config_manager.get_servers()
        for server in servers:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            # Server info with protocol
            protocol = server.get('protocol', 'vmess').upper()
            server_name = server.get('title', server.get('ps', 'Unnamed'))
            address = f"{server.get('add')}:{server.get('port')}"

            label = Gtk.Label(label=f"[{protocol}] {server_name} - {address}")
            label.set_xalign(0)
            box.pack_start(label, True, True, 0)

            # Connect button
            connect_btn = Gtk.Button(label="Connect")
            connect_btn.connect("clicked", self.on_connect_clicked, server)
            box.pack_start(connect_btn, False, False, 0)

            row.add(box)
            self.server_list.add(row)

        self.server_list.show_all()

    def on_add_server(self, button):
        """Show dialog to add new server"""

        dialog = Gtk.Dialog(title="Add V2Ray Server", parent=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                           Gtk.STOCK_OK, Gtk.ResponseType.OK)

        dialog.set_default_size(450, 200)

        content_area = dialog.get_content_area()
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_area.add(vbox)

        title_label = Gtk.Label(label="Title:")
        title_label.set_xalign(0)
        vbox.add(title_label)

        title_entry = Gtk.Entry()
        title_entry.set_placeholder_text("Server Name (Optional)")
        vbox.add(title_entry)

        vmess_label = Gtk.Label(label="VMess URL:")
        vmess_label.set_xalign(0)
        vbox.add(vmess_label)

        vmess_entry = Gtk.Entry()
        vmess_entry.set_placeholder_text("vmess://...")
        vbox.add(vmess_entry)

        dialog.show_all()

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            title = title_entry.get_text()
            vmess_url = vmess_entry.get_text()

            if vmess_url:
                if self.app.config_manager.add_server(vmess_url, title=title if title else None):
                    self.refresh_server_list()
                    self.show_status("Server added successfully")
                else:
                    self.show_status("Failed to add server")
            else:
                self.show_status("VMess URL cannot be empty")

        dialog.destroy()

    def on_server_activated(self, listbox, row):
        """Handle server selection"""
        server = self.app.config_manager.get_servers()[row.get_index()]
        self.connect_to_server(server)

    def on_connect_clicked(self, button, server):
        """Handle connect button click"""
        self.connect_to_server(server)

    def connect_to_server(self, server):
        """Connect to selected server"""
        try:
            self.app.v2ray_controller.start(server)
            self.show_status(f"Connected to {server.get('ps', 'Unnamed')}")
        except Exception as e:
            self.show_status(f"Connection failed: {str(e)}")

    def show_status(self, message):
        """Show status message"""
        context_id = self.status_bar.get_context_id("status")
        self.status_bar.push(context_id, message)
