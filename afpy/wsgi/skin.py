# -*- coding: utf-8 -*-
from Cheetah.Template import Template
from BeautifulSoup import BeautifulSoup
from paste.fileapp import _FileIter
import re
import os

TEMPLATE_MENU = """
<div class="portlet">
    <h5>%s</h5>
    <div class="portletBody">
        <div class="portletContent odd">
            <div>%s</div>
        </div>
    </div>
</div>
"""

def menu(title, items):
    items = ['<div class="nav1"><a href="%s" %s>%s</a></div>' % i for i in items]
    return TEMPLATE_MENU % (title, ''.join(items))

class SkinFilter(object):

    def __init__(self, app, template):
        self.app = app
        if not template:
            template = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'skin.html')
        fd = open(template)
        self.template = fd.read()
        fd.close()

    def __call__(self, environ, start_response):

        def fake_start_response(status, headers, *args, **kwargs):
            for k, v in headers:
                if k.lower() == 'content-type' and v.startswith('text/html'):
                    environ['afpy.skin.is_html'] = True
            environ['afpy.skin.status'] = status
            environ['afpy.skin.headers'] = headers

        iterable = self.app(environ, fake_start_response)

        status = environ['afpy.skin.status']
        headers = environ['afpy.skin.headers']

        if 'afpy.skin.is_html' not in environ:
            start_response(status, headers)
            return iterable

        if isinstance(iterable, _FileIter):
            start_response(status, headers)
            return iterable

        if 'afpy.skin.none' in environ:
            # explicite skip skin
            start_response(status, self.new_headers(headers, iterable))
            return iterable

        if hasattr(iterable, 'close'):
            iterable = ''.join([e for e in iterable.app_iterable])
        elif isinstance(iterable, list) or isinstance(iterable, tuple):
            iterable = ''.join([e for e in iterable])
        else:
            iterable = iterable.app_iterable

        if isinstance(iterable, unicode):
            iterable = iterable.encode('utf-8')

        if '<body' not in iterable:
            # we only have an html parts
            # probably ajax stuff
            start_response(status, self.new_headers(headers, iterable))
            return [iterable]

        soup = BeautifulSoup(iterable,
                             fromEncoding='utf-8')

        head = soup.head and soup.head.contents or []
        body = soup.body and soup.body.contents or []

        if 'planet' in environ['SCRIPT_NAME']:
            environ['afpy.skin.rightcolumn'] = False
            environ['afpy.skin.css'] = """
                #header,
                #content {
                    border:0;
                    width:98%;
                }
            """

        options = dict(
            head=''.join([str(t) for t in head]),
            body=''.join([str(t) for t in body]),
            user=environ.get('afpy.user', None),
            rightcolumn=environ.get('afpy.skin.rightcolumn', True),
            css=environ.get('afpy.skin.css', False),
            menu=environ.get('afpy.skin.menu', ''),
            )
        new_iterable = '%s' % Template(source=self.template,
                            searchList=options)
        iterable = [new_iterable]
        if hasattr(iterable, 'close'):
            iterable.app_iterable = iterable
            iterable.app_iter = iter(iterable.app_iterable)

        start_response(status, self.new_headers(headers, new_iterable))

        return iterable

    def new_headers(self, headers, iterable):
        has_length = False
        new_headers = []
        for k, v in headers:
            if k.lower() == 'content-length':
                v = str(len(iterable))
                has_length = True
            new_headers.append((k, v))
        if not has_length:
            try:
                new_headers.append(('Content-Length', str(len(iterable))))
            except TypeError:
                # iterable is unsized
                pass
        return new_headers

def factory(global_config, **local_config):
    template = local_config.get('template')
    def filter(app):
        return SkinFilter(app, template)
    return filter

