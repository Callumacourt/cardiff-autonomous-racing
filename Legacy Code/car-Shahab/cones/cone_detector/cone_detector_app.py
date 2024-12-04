#!env python3

import platform
import atexit
import signal

# Handle the case when we want to run without line profiler
import builtins
try:
    builtins.profile
except AttributeError:
    # No line profiler, provide a pass-through version
    def profile(func): return func
    builtins.profile = profile
from multiprocessing import Pipe, RawArray

import wx
import cv2
import pycuda
import libcudnn

import main_frame
from log import log
from detector_thread import DetectorThread
from detector_process import DetectorProcess
import detector_process
from config import config

detector_proc = None
detector_proc_conn = None

# Buffers in shared memory large enough to hold the images and the detection results
# This is a horrible hack for the sake of performance
BUF_SIZE = 16 * 1024 * 1024
image_buffer = RawArray('B', BUF_SIZE)
result_buffer = RawArray('B', BUF_SIZE)


class ConeDetectorApp(wx.App):
    """Main application class."""

    def OnInit(self):
        self.init_detector()

        # When any of these settings change, the detector needs to be re-initialised
        # to allocate buffers etc.
        config.add_listener('CD_INITIAL_SCALE', self.init_detector)
        config.add_listener('CD_PYRAMID_LEVELS', self.init_detector)
        config.add_listener('CD_SCALE_FACTOR', self.init_detector)

        # Create the main application window
        self.frame = main_frame.MainFrame(None)
        self.SetTopWindow(self.frame)
        self.frame.Raise()
        self.frame.Show()
        # self.frame.Maximize(True)

        # The detector thread notifies the main window that it needs to update display
        def notify_video():
            evt = main_frame.VideoEvent(main_frame.EVT_VIDEO_ID, -1)
            wx.PostEvent(self.frame, evt)

        self.detector_thread = DetectorThread(notify_video, detector_proc_conn,
                                              image_buffer, result_buffer)
        self.detector_thread.start()
        self.detector_thread.play()
        # self.timer = wx.Timer(self)
        # self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        # self.timer.Start(1000)
        return True

    def init_detector(self):
        detector_proc_conn.send((detector_process.CMD_INIT_DETECTOR,
                                 # {'cnn': 'cnn/net-8-8-8-16-4.mat',
                                 # {'cnn': 'cnn/net-8-4-6-8-4-do00.mat',
                                  {'cnn': 'cnn/net-6-4-6-6-4-do00-bn.mat',
                                  'initial_scale': config.CD_INITIAL_SCALE,
                                  'scale_factor': config.CD_SCALE_FACTOR,
                                  'num_levels': config.CD_PYRAMID_LEVELS}))

    def OnExit(self):
        self.detector_thread.abort()
        return 0 # Clean termination


def main():
    banner()

    global detector_proc, detector_proc_conn
    detector_proc_conn, conn = Pipe()
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    detector_proc = DetectorProcess(conn, image_buffer, result_buffer)
    signal.signal(signal.SIGINT, original_sigint_handler)
    detector_proc.daemon = True
    detector_proc_conn.send(detector_process.CMD_INIT_CUDA)
    detector_proc.start()

    wx.Log.SetLogLevel(5)
    app = ConeDetectorApp(0)
    app.MainLoop()


def banner():
    log('Cone Detector. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2019--2020.')
    log('')
    log('Running on:        ' + platform.platform())
    log('Python version:    ' + platform.python_version())
    log('wxWidgets version: ' + wx.version())
    log('OpenCV version:    ' + cv2.__version__)
    log('PyCUDA version:    ' + pycuda.VERSION_TEXT)
    log('cuDNN version:     ' + str(libcudnn.cudnnGetVersion()))
    log('NVCC version:      ' + pycuda.compiler.get_nvcc_version('nvcc'))
    log('')
    log('USAGE:')
    log('Space: play/pause')
    log('C:     auto zoom and center the image.')
    log('')


@atexit.register
def clean():
    print('Shutting down.')


if __name__ == '__main__':
    try: # Make sure we terminate cleanly even after an exception
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    finally:
        print('Shutting down the application.')
        # Stopping the detector process
        detector_proc_conn.send(detector_process.CMD_ABORT)
        print('Waiting for the detector process to join.')
        detector_proc.join()
        print('Terminating the detector process.')
        detector_proc.terminate()
