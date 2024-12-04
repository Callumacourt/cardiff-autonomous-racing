import time

class Timer(object):
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        pass
        if self.name:
            print('[%s]' % self.name)
        print('Elapsed: %.3f ms' % (1000.0 * (time.time() - self.tstart)))
