# -*- coding: utf-8 -*-
import os
import shutil
import trac
import MoinMoin

wiki_static = os.path.split(os.path.dirname(MoinMoin.__file__))[0]
wiki_static = os.path.join(wiki_static, 'share', 'moin', 'htdocs')
trac_static = os.path.dirname(trac.__file__)
trac_static = os.path.join(trac_static, 'htdocs')
def apache_root():
    root = os.path.join(os.getcwd(), 'apache_root')
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    for name, src in (('moins', wiki_static), ('trac', trac_static)):
        os.symlink(src, os.path.join(root, name))
