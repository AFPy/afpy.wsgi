# -*- coding: utf-8 -*-
from zope.interface import implements
from repoze.who.interfaces import IAuthenticator
from repoze.who.interfaces import IMetadataProvider
from repoze.what.adapters import BaseSourceAdapter, SourceError
from afpy.ldap import custom as ldap
from afpy.ldap import auth

def AuthenticationMiddleware(app, config):
    from repoze.who.plugins.auth_tkt import AuthTktCookiePlugin
    from repoze.who.plugins.basicauth import BasicAuthPlugin
    from repoze.who.plugins.friendlyform import FriendlyFormPlugin
    from repoze.who.plugins.cookie import InsecureCookiePlugin
    from repoze.what.plugins.ini import INIPermissionsAdapter
    from repoze.what.middleware import setup_auth

    conn = ldap.get_conn()

    cookie = InsecureCookiePlugin('__ac')
    loginform=FriendlyFormPlugin(login_form_url="/login",
                                 login_handler_path="/do_login",
                                 post_login_url="/login",
                                 logout_handler_path="/logout",
                                 post_logout_url="/login",
                                 rememberer_name="_ac")

    authenticator=auth.Authenticator(conn)

    groups = auth.GroupAdapter(conn)
    groups = {'all_groups': groups}

    basicauth = BasicAuthPlugin('Private web site')
    if 'auth.basic' in config:
        identifiers=[("basicauth", basicauth)]
        challengers=[("basicauth", basicauth)]
    else:
        identifiers=[("loginform", loginform), ("_ac", cookie), ("basicauth", basicauth)]
        challengers=[("loginform", loginform)]

    authenticators=[("accounts", authenticator)]
    mdproviders=[("accounts", auth.MDPlugin(conn))]

    permissions = {'all_perms': INIPermissionsAdapter(config['auth.permissions'])}

    return setup_auth(app,
                      groups,
                      permissions,
                      identifiers=identifiers,
                      authenticators=authenticators,
                      challengers=challengers,
                      mdproviders=mdproviders)

def make_auth(global_config, **local_config):
    config = global_config.copy()
    config.update(local_config)
    def filter_app(app):
        return AuthenticationMiddleware(app, config)
    return filter_app

