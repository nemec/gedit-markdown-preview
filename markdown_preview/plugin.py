# -*- encoding:utf-8 -*-
# plugin.py
#
#
# Copyright 2012 Nemec
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#

import socket
import random
import logging
import threading
import webbrowser
from gi.repository import GObject, Gtk, Gio, Gedit, PeasGtk
import markdown_preview.server as server

# http://live.gnome.org/Gedit/PythonPluginHowTo#Adding_a_menu_item
# http://www.micahcarrick.com/writing-plugins-for-gedit-3-in-python.html
# http://www.freewisdom.org/projects/python-markdown/Using_as_a_Module
logging.basicConfig()
LOG_LEVEL = logging.DEBUG
APP_NAME = "MarkdownPreview"

menu_xml = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="Preview Markdown" action="PreviewMarkdown"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class StoppableServerThread(threading.Thread):
  """Thread class with a stop() method. The thread itself has to check
  regularly for the stopped() condition."""

  def __init__(self, server=None):
    super(StoppableServerThread, self).__init__()
    self.logger = logging.getLogger(APP_NAME)
    self._stop = threading.Event()
    self.server = server
    self.running_port = None

  def stop(self):
    self._stop.set()
    self.server.socket.close()

  def stopped(self):
    return self._stop.isSet()

  def run(self):
    try:
      while not self.stopped():
        self.server.handle_request()
    except Exception as err:
      self.logger.exception("Exception in thread.")
      self.stop()


class MarkdownPreviewPlugin(
    GObject.Object, Gedit.WindowActivatable, PeasGtk.Configurable):
  __gtype_name__ = "MarkdownPreviewPlugin"
  window = GObject.property(type=Gedit.Window)
  SCHEMA_KEY = 'org.gnome.gedit.plugins.markdown-preview'

  def __init__(self):
    GObject.Object.__init__(self)
    self.logger = logging.getLogger(APP_NAME)
    self.logger.setLevel(LOG_LEVEL)
    self._ui_id = None  # Used for Menu Item
    self._action_group = None  # Used for Menu Item
    self.thread = None
    self.hostname = "localhost"
    self.default_port = 9019

    self.settings = None
    if self.SCHEMA_KEY in Gio.Settings.list_schemas():
      self.settings = Gio.Settings.new(self.SCHEMA_KEY)
    else:
      self.logger.warn("Settings schema not installed. "
                        "Plugin will not be configurable.")

  def do_activate(self):
    self._insert_menu()
    port = self.default_port
    if self.settings:
      port = self.settings.get_int('local-port')
    while True:
      self.logger.debug("Starting server on port {0}".format(port))
      try:
        md_server = server.GeditHTTPRequestServer(
          self.window, self.settings, address=('', port))
        self.running_port = port
        self.thread = StoppableServerThread(md_server)
        self.thread.start()
        break
      except socket.error as err:
        if err.errno == 98:
          if not self.settings or self.settings.get_bool('randomize-port'):
            port = random.randrange(10000, 20000)
          else:
            self.logger.exception("Markdown Preview server port in use.")
            break
        else:
          self.logger.exception(
            "Unknown server error in Markdown Preview plugin.")
          break

  def do_deactivate(self):
    if self.thread:
      self.thread.stop()
    self._remove_menu()

  def _insert_menu(self):
    manager = self.window.get_ui_manager()
    self._action_group = Gtk.ActionGroup("MarkdownPreviewActions")
    self._action_group.add_actions([("PreviewMarkdown", None, 
                                    "Preview as Markdown", "<Ctl><Shift>D",
                                    "Preview Markdown in a Web Browser",
                                    self.on_preview_markdown)])
    manager.insert_action_group(self._action_group, -1)
    self._ui_id = manager.add_ui_from_string(menu_xml)

  def _remove_menu(self):
    manager = self.window.get_ui_manager()
    if self._ui_id:
      manager.remove_ui(self._ui_id)
      self._ui_id = None
    if self._action_group:
      manager.remove_action_group(self._action_group)
      self._action_group = None
    manager.ensure_update()

  def on_preview_markdown(self, action):
    webbrowser.open_new_tab('http://{0}:{1}/{2}'.format(
      self.hostname, self.running_port,
      self.window.get_active_document().get_location().get_uri()))

  def do_create_configure_widget(self):
    container = Gtk.VBox()
    code_model = Gtk.ListStore(str)
    code_theme = Gtk.ComboBox(model=code_model)
    cell = Gtk.CellRendererText()
    code_theme.pack_start(cell, True)
    code_theme.add_attribute(cell, 'text', 0)
    container.pack_start(code_theme, True, True, 0)
    port_entry = Gtk.Entry()
    port_entry.set_max_length(5)
    container.pack_start(port_entry, True, True, 0)
    randomize_port = Gtk.CheckButton("Randomize port if default in use.")
    container.pack_start(randomize_port, True, True, 0)
    
    if self.settings:
      choices = self.settings.get_range("code-theme")
      choices = choices.get_child_value(1).unpack()
      active_code_theme = self.settings.get_string("code-theme")
      for idx, item in enumerate(choices):
        itr = code_model.append([item])
        if item == active_code_theme:
          code_theme.set_active(idx)

      port_entry.set_text(str(self.settings.get_int("local-port")))
      randomize_port.set_active(self.settings.get_boolean("randomize-port"))
      
      code_theme.connect("changed", self.on_code_theme_changed)
      port_entry.connect("focus-out-event", self.on_port_changed)
    else:
      container.set_sensitive(False)
    return container

  def on_code_theme_changed(self, combobox):
    if self.settings:
      self.logger.debug("Setting current theme to " + 
        combobox.get_model()[combobox.get_active()][0])
      self.settings.set_string('code-theme',
        combobox.get_model()[combobox.get_active()][0])

  def on_port_changed(self, entry, event):
    if self.settings:
      try:
        port = int(entry.get_text())
        if 0 < port < 65535:
          self.settings.set_int('local-port', port)
          entry.set_progress_fraction(0)
          self.logger.debug("Port changed to {0}".format(port))
        else:
          entry.set_progress_fraction(1)
      except ValueError:
        entry.set_progress_fraction(1)

  def on_randomize_port_changed(self, button):
    self.settings.set_boolean('randomize-port', button.get_active())
