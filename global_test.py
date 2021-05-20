
from flask import g
def get_mode():
    mode = getattr(g, '_mode', 'default')
    return g._mode

def change_mode(mode):
    setattr(g, '_mode', mode)

g.setdefault('_mode')
get_mode()
change_mode('test')
get_mode()
change_mode('asdaf')
get_mode()