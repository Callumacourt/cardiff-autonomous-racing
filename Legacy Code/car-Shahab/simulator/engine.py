import matlab.engine
import os

_eng = None

@property
def eng(engine):
    global _eng
    if _eng:
        return _eng
    _eng = matlab.engine.connect_matlab()
    path = os.path.dirname(os.path.abspath(__file__))
    _eng.cd(path)
    return _eng

import mprop; mprop.init()
