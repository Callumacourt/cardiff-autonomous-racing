#!env python3

import platform
import argparse
import wx
import cv2
import main_frame
from log import log


class SimulatorApp(wx.App):
    def OnInit(self):
        parser = argparse.ArgumentParser(description='Play racing simulation.')
        parser.add_argument('--agent', help='Load agent', metavar=('AGENT'))
        self.args = parser.parse_args()

        self.frame = main_frame.MainFrame(None)
        self.SetTopWindow(self.frame)
        self.frame.Raise()
        self.frame.Show()
        self.frame.Maximize(True)
        return True


def main():
    wx.Log.SetLogLevel(5)
    app = SimulatorApp(0)
    app.frame.display_help()
    log('')
    log('OpenCV version:    ' + cv2.__version__)
    log('wxWidgets version: ' + wx.version())
    log('Python version:    ' + platform.python_version())
    log('Running on:        ' + platform.platform())
    app.MainLoop()


if __name__ == '__main__':
    main()
