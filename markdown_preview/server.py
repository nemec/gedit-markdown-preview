import BaseHTTPServer
from gi.repository import Gio
try:
  import markdown
except ImportError:
  markdown = None

class MarkdownHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_GET(self):
    if not markdown:
      self.wfile.write(
        "Python-Markdown not installed. Please install "
        "before using this plugin.")

    try:
      uri = None
      if self.path and self.path[0] == '/':
        uri = self.path[1:]

      tab = self.server.window.get_tab_from_location(Gio.File.new_for_uri(uri))
      if tab:
        buf = tab.get_view().get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        self.wfile.write(
          markdown.markdown(text, self.server.markdown_extensions))
      else:
        self.wfile.write("Could not match file {0}.".format(uri))
    except Exception as err:
      self.wfile.write("Exception occurred while rendering: " + str(err))

class GeditHTTPRequestServer(BaseHTTPServer.HTTPServer):
  def __init__(self, window,
                markdown_extensions=['fenced_code'],
                address=('', 8000),
                handler=MarkdownHTTPRequestHandler):
    BaseHTTPServer.HTTPServer.__init__(self, address, handler)
    self.window = window
    self.markdown_extensions = markdown_extensions


if __name__ == "__main__":
  server = GeditHTTPRequestServer(None)
  while True:
    server.handle_request()
