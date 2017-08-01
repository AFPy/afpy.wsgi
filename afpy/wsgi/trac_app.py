# -*- coding: utf-8 -*-
from paste.deploy.config import ConfigMiddleware
from paste.deploy import CONFIG
import trac.web.main

def application(environ, start_response):
    environ['trac.env_path'] = CONFIG['trac-env']
    #environ['PYTHON_EGG_CACHE'] = '/usr/local/trac/mysite/eggs'
    return trac.web.main.dispatch_request(environ, start_response)

def factory(global_config, **local_config):
    app = application
    conf = global_config.copy()
    conf.update(**local_config)
    return ConfigMiddleware(app, conf)
