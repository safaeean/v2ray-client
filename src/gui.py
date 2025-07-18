from gi.repository import Gtk, GObject, GLib


class MainWindow(Gtk.Window):
    def __init__(self, app):
        super().__init__(title="V2Ray Client")
        self.app = app
        self.set_default_size(600, 400)

        self.connect("destroy", Gtk.main_quit)

        # Main layout
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.box)

        menubar = Gtk.MenuBar()

        menu = Gtk.Menu()
        add_item = Gtk.MenuItem(label="Add Server")
        add_item.connect("activate", self.on_add_server)
        menu.append(add_item)

        root_menu = Gtk.MenuItem(label="Servers")
        root_menu.set_submenu(menu)
        menubar.append(root_menu)

        about_menu = Gtk.Menu()
        add_item = Gtk.MenuItem(label="About")
        add_item.connect("activate", self.on_about_clicked)
        about_menu.append(add_item)


        help_menu = Gtk.MenuItem(label="Help")
        help_menu.set_submenu(about_menu)
        menubar.append(help_menu)




        self.box.pack_start(menubar, False, False, 0)


        # Server list
        self.scrolled_window = Gtk.ScrolledWindow()
        self.server_list = Gtk.ListBox()
        self.server_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.scrolled_window.add(self.server_list)
        self.box.pack_start(self.scrolled_window, True, True, 0)

        self.server_list.connect("row-selected", self.on_row_selected)

        # Status bar
        self.status_bar = Gtk.Statusbar()
        self.box.pack_end(self.status_bar, False, False, 0)

        # Status bar buttons
        self.connect_button = Gtk.Button(label="Connect")
        self.connect_button.set_no_show_all(True)
        self.connect_button.connect("clicked", self.on_connect_button_clicked)

        self.disconnect_button = Gtk.Button(label="Disconnect")
        self.disconnect_button.set_no_show_all(True)
        self.disconnect_button.connect("clicked", self.on_disconnect_button_clicked)

        self.redirect_button = Gtk.Button(label="Redirect Traffic")
        self.redirect_button.set_no_show_all(True)
        self.redirect_button.connect("clicked", self.on_redirect_button_clicked)

        # Add to status bar
        self.status_bar.pack_start(self.connect_button, False, False, 5)
        self.status_bar.pack_start(self.disconnect_button, False, False, 5)
        self.status_bar.pack_start(self.redirect_button, False, False, 5)

        # Initial state
        self.connect_button.hide()
        self.disconnect_button.hide()
        self.redirect_button.hide()


        # Load servers
        self.refresh_server_list()

    def on_row_selected(self, listbox, row):
        if row:
            self.connect_button.show()
        else:
            self.connect_button.hide()

    def on_connect_button_clicked(self, button):
        row = self.server_list.get_selected_row()
        if row:
            index = row.get_index()
            server = self.app.config_manager.get_servers()[index]
            self.connect_to_server(server)

            # تغییر وضعیت دکمه‌ها
            self.connect_button.hide()
            self.disconnect_button.show()
            self.redirect_button.show()

    def on_disconnect_button_clicked(self, button):
        self.app.v2ray_controller.stop()
        self.show_status("Disconnected")

        # بازگرداندن وضعیت دکمه‌ها
        self.disconnect_button.hide()
        self.redirect_button.hide()

        # اگر هنوز سروری انتخابه، connect نشون داده بشه
        if self.server_list.get_selected_row():
            self.connect_button.show()

    def on_redirect_button_clicked(self, button):
        success = self.app.v2ray_controller.redirect_all_traffic_through_socks()
        print(success)
        if success:
            self.show_status("System traffic redirected to proxy")
        else:
            self.show_status("Failed to redirect traffic")


    def on_about_clicked(self, widget):
        about_dialog = Gtk.AboutDialog(
            transient_for=self,
            modal=True
        )
        about_dialog.set_program_name("V2Ray Client")
        about_dialog.set_version("1.0.0")
        about_dialog.set_comments("A simple GTK-based V2Ray client for Linux.")
        about_dialog.set_website("https://mndco.ir")
        about_dialog.set_website_label("Project Website")
        about_dialog.set_authors(["Hossein", "MNDCo"])
        about_dialog.set_license("MIT License")

        about_dialog.present()

        if hasattr(about_dialog, "run"):
            about_dialog.run()
            about_dialog.destroy()


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
            label.set_margin_top(10)
            label.set_margin_bottom(10)
            box.pack_start(label, True, True, 0)

            row.add(box)
            self.server_list.add(row)

        self.server_list.show_all()

        def _defer_unselect():
            self.server_list.unselect_all()
            self.status_bar.grab_focus()
            return False

        GLib.idle_add(_defer_unselect)


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
