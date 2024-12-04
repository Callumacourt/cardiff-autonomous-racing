import scipy.io as sio

class Track:
    def __init__(self, fn):
        # log(f'Loading track {fn}')
        track = sio.loadmat(fn, squeeze_me=True)
        self.name = track['name']
        self.fx = track['fx']
        self.fy = track['fy']
        self.dist = track['dist']
        self.inner = track['inner']
        self.outer = track['outer']
