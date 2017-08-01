# -*- coding: utf-8 -*-
from MoinMoin.server.server_wsgi import moinmoinApp
from paste.cgiapp import CGIApplication
from paste.util import converters
import sys

afpy_skin_css = """
#header {
    background:white;
}
.documentContent,
#region-content,
#content {
    margin:0 !important;
    padding:0 !important;
}
.documentContent #logo {
    display:none;
}
"""

def wiki_factory(global_conf, path):
    if path not in sys.path:
        sys.path.append(path)
    def wikiapp(environ, start_response):
        environ['afpy.skin.rightcolumn'] = False
        environ['afpy.skin.css'] = afpy_skin_css
        return moinmoinApp(environ, start_response)
    return wikiapp

