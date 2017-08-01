import sys, os

def main():
    ini = os.path.abspath(sys.argv[0])
    path = sys.path
    print """
<Location />
    SetHandler python-program
    PythonHandler paste.modpython
    PythonPath "%(path)s"
    PythonOption paste.ini %(ini)s
</Location>
""" % locals()

