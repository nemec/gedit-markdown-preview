import urlparse
import BaseHTTPServer
from gi.repository import Gio
try:
  import markdown
except ImportError:
  pass  # User will be alerted when they preview a file.


def get_style(path):
  """
  Open a css stylesheet from the local drive and return the contents as
  a <style> tag.
  """
  try:
    with open(path, 'r') as css_file:
      return '<style type="text/css">\n{0}\n"</style>'.format(css_file.read())
  except (IOError, TypeError) as err:
    pass
  return ''

class MarkdownHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  """Apply Markdown to the given page and display its rendered html."""
  css_path = "style/{0}.css"
  general_css = "markdown"
  default_highlight_css = "github"
  def do_GET(self):
    """
    Handle incoming GET Requests. The path is the full URI of the open
    Gedit file to apply Markdown to. Retrieve the contents from the given
    file, style it, and return the html rendering to the user. If a `style`
    query paramater is given, try to use it as the name of the code highlight
    css style to use.

    """

    try:
      uri = None
      query_string = None
      if self.path and self.path[0] == '/':
        uri, sep, query_string = self.path[1:].partition('?')
      
      tab = self.server.window.get_tab_from_location(Gio.File.new_for_uri(uri))
      if tab:
        buf = tab.get_view().get_buffer()
        md_text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        try:
          md_html = markdown.markdown(md_text, self.server.markdown_extensions)
        except NameError:
          self.wfile.write(
            "Python-Markdown not installed. Please install "
            "before using this plugin. For up-to-date code, "
            "install from https://github.com/waylan/Python-Markdown")
          return
        self.wfile.write("<head>")
        self.wfile.write(get_style(self.css_path.format(self.general_css)))
        highlight_css = None
        if self.server.settings:
          highlight_css = get_style(self.css_path.format(
                                self.server.settings.get_string('code-theme')))
        if not highlight_css:
          highlight_css = get_style(
            self.css_path.format(self.default_highlight_css))
        if query_string:  # Override code-theme if provided in query
          params = urlparse.parse_qs(query_string)
          for css_name in params.get('style', []):
            highlight_css = get_style(self.css_path.format(css_name))
            if highlight_css:
              break
        self.wfile.write(highlight_css)
        self.wfile.write("</head>")
        self.wfile.write(md_html)
      else:
        self.wfile.write("Could not match file {0}.".format(uri))
    except Exception as err:
      self.wfile.write("Exception occurred while rendering: " + str(err))


class GeditHTTPRequestServer(BaseHTTPServer.HTTPServer):
  """Server that handles requests for the Gedit Markdown plugin."""
  def __init__(self, window, settings=None,
                markdown_extensions=['codehilite', 'fenced_code'],
                address=('', 8000),
                handler=MarkdownHTTPRequestHandler):
    BaseHTTPServer.HTTPServer.__init__(self, address, handler)
    self.window = window
    self.settings = settings
    self.markdown_extensions = markdown_extensions
