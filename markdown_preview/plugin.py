# -*- encoding:utf-8 -*-
# plugin.py
#
#
# Copyright 2012 Nemec
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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

import re
import logging
import threading
import subprocess
from gi.repository import GObject, Gtk, Gio, Gdk, Gedit, PeasGtk
import markdown_preview.server as server

# http://live.gnome.org/Gedit/PythonPluginHowTo#Adding_a_menu_item
# http://www.micahcarrick.com/writing-plugins-for-gedit-3-in-python.html
# http://www.freewisdom.org/projects/python-markdown/Using_as_a_Module
logging.basicConfig()
LOG_LEVEL = logging.WARN
APP_NAME = "MarkdownPreview"

ui_str = """<ui>
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

  def stop(self):
    self._stop.set()

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

  def __init__(self):
    GObject.Object.__init__(self)
    self.logger = logging.getLogger(APP_NAME)
    self.logger.setLevel(LOG_LEVEL)
    self._ui_id = None
    self.thread = None
    self.server = None
    self._action_group = None
    self.hostname = 'localhost'
    self.port = 8000

  def do_activate(self):
    self._insert_menu()
    self.server = server.GeditHTTPRequestServer(self.window)
    self.thread = StoppableServerThread(self.server)
    self.thread.start()

  def do_deactivate(self):
    if self.thread:
      self.thread.stop()
    if self.server:
      self.server.socket.close()
    self._remove_menu()

  def _insert_menu(self):
    manager = self.window.get_ui_manager()
    self._action_group = Gtk.ActionGroup("MarkdownPreviewActions")
    self._action_group.add_actions([("PreviewMarkdown", None, 
                                    "Preview Markdown", "<Control><Shift>D",
                                    "Preview Markdown in a Web Browser",
                                    self.on_preview_markdown)])
    manager.insert_action_group(self._action_group, -1)
    self._up_id = manager.add_ui_from_string(ui_str)

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
    subprocess.call(['xdg-open', 'http://{0}:{1}/{2}'.format(
      self.hostname, self.port,
      self.window.get_active_document().get_location().get_uri())])

  def do_create_configure_widget(self):
    return None
