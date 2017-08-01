# -*- coding: utf-8 -*-
import os
import base64
import urllib
import urlparse
from Cheetah.Template import Template
from afpy.core import ldap
from afpy.core import config
from authkit.authenticate import middleware
from beaker.middleware import SessionMiddleware

openid_template = """\
<html>
<head><title>Login</title></head>
<body>
<div>

<h1>Veuillez vous identifier</h1>

<p>Pour acc&eacute;der &agrave; cette partie du site, vous devez d'abord vous identifier.</p>

<p>Si vous n'avez pas de compte ici, vous pouvez aller au <a href="http://www.afpy.org/join_form?came_from=">formulaire d'inscription</a> pour devenir membre.</p>

<script type="text/javascript">
// <![CDATA[
if (cookiesEnabled && !cookiesEnabled()) {
document.writeln('<div class="portalMessage"><img src="info.gif" />Cookies are not enabled. You can not log in if they are turned off. <a href="enabling_cookies">How to enable cookies<'+'/a>.<'+'/div>');
}
// ]]>
</script>



<form method="post" action="/logged_in">

<fieldset>

<legend>Informations sur le compte</legend>

<input type="hidden" value="" name="came_from"/>

<div class="field">

<label for="__ac_name">Nom d'utilisateur</label>

<div class="formHelp">Les noms d'utilisateur et les mots de passe doivent respecter la casse. Au besoin, v&eacute;rifiez la touche de verrouillage num&eacute;rique de votre clavier.</div>

<input type="text" id="__ac_name" value="gawel" name="__ac_name" tabindex="1" size="15"/>

</div>

<div class="field">

<label for="__ac_password">Mot de passe</label>

<div class="formHelp">Saisissez le mot de passe de votre choix (5 caract&egraveres minimum).</div>

<input type="password" id="__ac_password" name="__ac_password" tabindex="2" size="15"/>
</div>

<div class="field">

<input type="checkbox" name="__ac_persistent" tabindex="3" id="cb_remember" checked="checked" value="1" class="noborder formRememberName"/>

<label for="cb_remember">Se souvenir de mon nom</label>

<div class="formHelp">Cocher l'option "Se souvenir de mon nom"
cr&eacute;era un <em>cookie</em> avec votre nom d'utilisateur. Votre nom
apparaitra alors automatiquement dans ce formulaire lors de vos prochaines
visites.</div>

</div>

<div class="formControls">

<input type="submit" value="Connexion" name="submit" tabindex="4" class="context"/>

</div>

<p>N'oubliez pas de fermer votre session ou de quitter votre navigateur quand vous aurez termin&eacute;.</p>

</fieldset>

</form>

</div>
</body>
</html>
"""


def make_template():
    output = getattr(make_template, '_output', None)
    if output:
        return output

    template = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'skin.html')
    fd = open(template)
    template = fd.read()
    fd.close()

    options = dict(
        head='',
        body=openid_template,
        user=None,
        rightcolumn=True,
        css='', menu='')

    template = '%s' % Template(source=template, searchList=options)
    setattr(make_template, '_output', template)
    return template

def ldap_auth(environ, username, password):
    if ldap.isUser(username):
        user = ldap.getUser(username)
        if user.checkCredentials(password):
            return True
    return False

VALID_HOSTS = (
        'openid.afpy.org',
        )

def urltouser(environ, url):
    scheme, host, user = urlparse.urlparse(url)[:3]
    environ['openid.url'] = url
    username = user.split('/')[1]
    if ldap.isUser(username):
        user = ldap.getUser(username)
        if user.labeledURI == url:
            return username
    raise RuntimeError('User url does not match')


class AfpyAuth(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        user = None
        valid_user = None

        # get from authkit
        username = environ.get('REMOTE_USER')
        authenticate = environ.get('authkit.authenticate', False)

        if username and authenticate:
            valid_user = username

        # get from zope cookie
        if 'paste.cookies' in environ:
            for cookies in environ['paste.cookies']:
                if '__ac' in cookies:
                    try:
                        cookie = urllib.unquote(cookies['__ac'].value)
                    except TypeError:
                        pass
                    else:
                        try:
                            value = base64.decodestring(cookie.rstrip())
                        except:
                            pass
                        else:
                            if ':' in value:
                                valid_user, password = value.split(':')
                                break

        if valid_user:
            if ldap.isUser(valid_user):
                user = ldap.getUser(valid_user)

                if not authenticate:
                    if not user.checkCredentials(password):
                        valid_user = None

        if not valid_user:
            try:
                valid_user = config.get('ldap', 'test_user')
            except:
                pass
            else:
                user = ldap.getUser(valid_user)

        if valid_user is not None and user is not None:
            valid_user = valid_user.lower()
            environ['REMOTE_USER'] = valid_user
            environ['authkit.authenticate'] = True
            environ['afpy.user'] = user
            environ['afpy.user.id'] = valid_user
            environ['afpy.user.groups'] = user.groups

        return self.app(environ, start_response)

def factory(global_config, prefix='', **local_config):
    def filter_app(app):
        app = middleware(
            AfpyAuth(app),
            setup_method='openid,cookie',
            openid_path_signedin='/%smembres/signedin' % prefix,
            openid_path_verify='/verify',
            openid_path_process='/process',
            openid_store_type='file',
            openid_store_config='',
            openid_baseurl='http://www.afpy.org',
            openid_urltouser=urltouser,
            openid_template_obj='afpy.wsgi.auth:make_template',
            cookie_secret='secret encryption string',
            cookie_signoutpath = '/signout',
        )
        return SessionMiddleware(
             app,
             key='authkit_openid',
             secret='asdasd',
        )

    return filter_app
