import time

class Timer(object):
    def __init__(self, name=None):             #defining the timer counted in 'ms'
        self.name = name

    def __enter__(self):                        #defining initial timing of timer
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        pass
        if self.name:
            print('[%s]' % self.name)
        print('Elapsed: %.3f ms' % (1000.0 * (time.time() - self.tstart)))  #output the time taken converting from 'ms' to 's'
