#!env python3

import wx
from main_frame import MainFrame

frame = None


class AnnotationToolApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None)
        self.SetTopWindow(self.frame)
        self.frame.Raise()
        self.frame.Show()
        self.frame.Maximize(True)
        # self.frame.after_init()
        return True


def main():
    wx.Log.SetLogLevel(5)
    app = AnnotationToolApp(0)
    app.MainLoop()


if __name__ == '__main__':
    main()
