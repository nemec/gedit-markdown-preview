===================================
Markdown Preview Plugin for Gedit
===================================

Description
===========

Markdown is nice for writing READMEs, but the only way to make sure the
formatting is correct is to upload it somewhere (like Github) and test
it out. This plugin uses python-markdown to automatically convert the
current document to markdown HTML (using standard markdown) and display
a preview automatically in the browser.

This plugin sets up an HTTP server to serve requests for open Gedit
documents.

Usage
========

* Hit Ctrl+Shift+D to display the current Gedit document as Markdown in
  your default web browser.
* Connects to port 9019 by default (but can be configured)
* HTTP path is the file:// uri to the open file you wish to display (Markdown
  file must be open in Gedit to display it)
* In the configuration, you can set the code syntax highlighting theme
  as well.

Installation
============

1. Install Python-Markdown. The recommended source is
  [Github](https://github.com/waylan/Python-Markdown), but previous versions
  may be installed through apt (python-markdown) or easy_install (Markdown).
2. Run install.sh to install plugin files.
3. Restart Gedit, then go to Edit->Preferences->Plugins and check the box next
  to `Markdown Preview`.
