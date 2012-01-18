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

Usage
========

* Hit Ctrl+Shift+D to display the current Gedit document as Markdown in
  your default web browser.
* Connects to port 8000 by default (configuration is a planned feature)
* HTTP path is the file:// uri to the open file you wish to display (Markdown
  file must be open in Gedit to display it)

Installation
============

1. Run install.sh to install plugin files.
2. Restart Gedit, then go to Edit->Preferences->Plugins and check the box next
  to `Markdown Preview`.


```

  print "hello"

```
