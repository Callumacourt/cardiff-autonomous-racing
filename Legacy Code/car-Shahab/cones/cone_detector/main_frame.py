import wx
import wx.lib.agw.aui as aui
# from console import Console
from image_viewer import *
from settings import Settings
import detector

EVT_VIDEO_ID = wx.NewEventType()
EVT_VIDEO = wx.PyEventBinder(EVT_VIDEO_ID, 1)


class VideoEvent(wx.PyCommandEvent):
    """Event to signal that a new video frame is ready for display"""

    def __init__(self, etype, eid, value=None):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

    def GetValue(self):
        """Returns the value from the event.
        @return: the value of this event

        """
        return self._value


class MainFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='Cone Detector',
                 pos=wx.DefaultPosition, size=(1024, 768),
                 style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # self.Show()
        self.CreateStatusBar(2)

        self.manager = aui.AuiManager(
            self, agwFlags=aui.AUI_MGR_ALLOW_FLOATING | aui.AUI_MGR_LIVE_RESIZE)
        self.manager.SetManagedWindow(self)
        # self.console = Console(self)
        self.viewer = ImageViewer(self)
        self.settings = Settings(self)

        self.manager.AddPane(self.viewer, aui.AuiPaneInfo().CenterPane())
        self.manager.AddPane(self.settings, aui.AuiPaneInfo().Left().BestSize(
            300, 600).Name('Settings').Caption('Settings').CloseButton(False).Layer(1))
        # self.manager.AddPane(self.console, aui.AuiPaneInfo().Bottom().Name(
        #     'Console').Caption('Console').CloseButton(True).Layer(0))
        # self.manager.GetPane("Console").dock_proportion = 40
        # self.manager.GetPane("Settings").dock_proportion = 60
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(EVT_VIDEO, self.OnVideo)

        wx.CallAfter(self.after_init)

    def after_init(self):
        wx.SafeYield()
        self.manager.Update()
        self.Refresh()
        self.SetFocus()
        # wx.CallAfter(self.viewer.load_image)
        self.viewer.auto_zoom()
        self.viewer.after_init()

    def OnVideo(self, value):
        if wx.GetApp().detector_thread.im_result is not None:
            self.viewer.set_image(Image(wx.GetApp().detector_thread.im_result))

    def OnKey(self, event):
        # focused = wx.Window.FindFocus()
        # if isinstance(focused, wx.TextCtrl):
        #     event.Skip()
        #     return
        code = event.GetKeyCode()
        if code == ord('Q'):
            if wx.GetKeyState(wx.WXK_CONTROL):
                self.Close()
        elif code == ord('C'):
            self.viewer.auto_zoom()
        elif code == wx.WXK_F10:
            self.viewer.screenshot()
        elif code == ord(' '):
            app = wx.GetApp()
            if app.detector_thread.paused:
                app.detector_thread.play()
            else:
                app.detector_thread.pause()

        else:
            event.Skip()

    def OnQuit(self, event):
        self.Close()

    def OnClose(self, event):
        # Deinitialize the frame manager
        self.manager.UnInit()
        # Delete the frame
        self.Destroy()
