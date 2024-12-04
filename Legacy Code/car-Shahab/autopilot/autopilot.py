#!env python3
#%% import section
#Allows for platform specific data to be pulled, eg. windows unix x64 x84
import platform
#Closing event handelers, 
import atexit
#used for asychornous events
import signal

# Handle the case when we want to run without line profiler // idk what this one does specifically
import builtins
try:
    builtins.profile
except AttributeError:
    # No line profiler, provide a pass-through version
    def profile(func): return func
    builtins.profile = profile
# Used to import the basic multiprocessing functionality, very similar to import threading
from multiprocessing import Pipe

# GUI Builder
import wx

# OpenCV used with vision system
import cv2
# Cuda Libs
import pycuda
import libcudnn

# Internally developed package, used for mppi *** need to double check
import main_frame
# Simple logging library
from log import log
# Self made packages
from autopilot_thread import AutopilotThread
from detector_process import DetectorProcess
from video_process import VideoProcess
import detector_process
import video_process
from config import config
from simulator import Simulator

#%%Var decleration

detector_proc = None
detector_proc_conn = None
video_proc = None
video_proc_conn = None
sim = Simulator()
# sim = None

#%% class Definition
class ConeDetectorApp(wx.App):
    """Main application class."""

    def OnInit(self):
        self.init_detector()

        # When any of these settings change, the detector needs to be re-initialised
        # to allocate buffers etc.
        config.add_listener('CD_FILENAME', self.init_detector)
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

        self.autopilot_thread = AutopilotThread(
            notify_video, detector_proc_conn, sim)
        self.autopilot_thread.start()
        self.autopilot_thread.play()
        return True

    def init_detector(self):
        detector_proc_conn.send((detector_process.CMD_INIT_DETECTOR,
                                 {'cnn': config.CD_FILENAME,
                                  'initial_scale': config.CD_INITIAL_SCALE,
                                  'scale_factor': config.CD_SCALE_FACTOR,
                                  'num_levels': config.CD_PYRAMID_LEVELS}))

    def OnExit(self):
        self.autopilot_thread.abort()
        sim.disconnect()
        return 0  # Clean termination


def main():
    banner()

    global detector_proc, detector_proc_conn, video_proc, video_proc_conn

    # Start the detector process
    detector_proc_conn, detector_proc_conn_feedback = Pipe()           #unknown
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    detector_proc = DetectorProcess(detector_proc_conn_feedback)
    signal.signal(signal.SIGINT, original_sigint_handler)
    detector_proc.daemon = True
    detector_proc_conn.send(detector_process.CMD_INIT_CUDA)
    detector_proc.start()
    
    # Start the video process
    video_proc_conn, video_proc_conn_feedback = Pipe()                #unknown
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    video_proc = VideoProcess(video_proc_conn_feedback)
    signal.signal(signal.SIGINT, original_sigint_handler)
    video_proc.daemon = True
    video_proc.start()

    wx.Log.SetLogLevel(5)
    app = ConeDetectorApp(0)
    app.MainLoop()


def banner():
    log('CAR Autopilot. Copyright (c) Cardiff Autonomous Racing, 2019--2020.')
    log('')
    log('Running on:        ' + platform.platform())
    log('Python version:    ' + platform.python_version())
    log('wxWidgets version: ' + wx.version())
    log('OpenCV version:    ' + cv2.__version__)
    log('PyCUDA version:    ' + pycuda.VERSION_TEXT)
    log('cuDNN version:     ' + str(libcudnn.cudnnGetVersion()))
    log('NVCC version:      ' + pycuda.compiler.get_nvcc_version('nvcc'))
    log('')
    # log('USAGE:')
    # log('Space: play/pause')
    # log('C:     auto zoom and center the image.')
    # log('')


@atexit.register
def clean():
    sim.disconnect()
    print('Shutting down.')

#%% Main Script
if __name__ == '__main__':
    try:  # Make sure we terminate cleanly even after an exception
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
    finally:
        print('Shutting down the application.')
        sim.disconnect()

        # Stopping the detector process
        detector_proc_conn.send(detector_process.CMD_ABORT)
        print('Waiting for the detector process to join.')
        detector_proc.join()
        print('Terminating the detector process.')
        detector_proc.terminate()

        # Stopping the video process
        video_proc_conn.send(video_process.CMD_ABORT)
        print('Waiting for the video process to join.')
        video_proc.join()
        print('Terminating the video process.')
        video_proc.terminate()
