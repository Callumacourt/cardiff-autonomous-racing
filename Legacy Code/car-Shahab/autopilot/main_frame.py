import wx
import wx.lib.agw.aui as aui
# from console import Console
from image_viewer import *
from plan_view import PlanView
from world_view import WorldView
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
    def __init__(self, parent, id=-1, title='CAR Autopilot',
                 pos=(0, 0), size=(2250, 512),
                 style=wx.DEFAULT_FRAME_STYLE | wx.NO_FULL_REPAINT_ON_RESIZE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        # self.Show()
        self.CreateStatusBar(2)
        # frame.SetIcon(wx.Icon("path/to/app.ico"))

        self.manager = aui.AuiManager(
            self, agwFlags=aui.AUI_MGR_ALLOW_FLOATING | aui.AUI_MGR_LIVE_RESIZE)
        self.manager.SetManagedWindow(self)
        # self.console = Console(self)
        self.plan_view = PlanView(self, size=(512, 512))
        # self.world_view = WorldView(self, size=(512, 512))
        self.viewer = ImageViewer(self)
        # self.settings = Settings(self)

        self.manager.AddPane(self.viewer, aui.AuiPaneInfo().CenterPane().Name("Stereo"))
        # self.manager.AddPane(self.settings, aui.AuiPaneInfo().Left().BestSize(
            # 300, 600).Name('Settings').Caption('Settings').CloseButton(False).Layer(1))
        self.manager.AddPane(self.plan_view, aui.AuiPaneInfo().Left().MinSize(
            512, 512).Name('PlanView').Caption('Plan View').CloseButton(True).Layer(0))
        # self.manager.AddPane(self.world_view, aui.AuiPaneInfo().Left().MinSize(
        #     512, 512).Name('WorldView').Caption('World View').CloseButton(True).Layer(0))

        # self.manager.AddPane(self.console, aui.AuiPaneInfo().Bottom().Name(
        #     'Console').Caption('Console').CloseButton(True).Layer(0))
        self.timer = wx.Timer(self)

        self.manager.GetPane("PlanView").dock_proportion = 50
        self.manager.GetPane("Stereo").dock_proportion = 50
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(EVT_VIDEO, self.OnVideo)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(20)
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
        if wx.GetApp().autopilot_thread.im_result is not None:
            self.viewer.set_image(Image(wx.GetApp().autopilot_thread.im_result))
        # self.plan_view.Update()
        self.plan_view.canvas.draw()
        # self.world_view.canvas.draw()

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
            if app.autopilot_thread.paused:
                app.autopilot_thread.play()
            else:
                app.autopilot_thread.pause()

        else:
            event.Skip()

    def OnTimer(self, event):
        throttle = 0
        brakes = 0
        steering = 0
        # print('OnTimer')
        if wx.GetKeyState(wx.WXK_UP):
            throttle = 1
        if wx.GetKeyState(wx.WXK_DOWN):
            brakes = 1
            throttle = -1
        if wx.GetKeyState(wx.WXK_LEFT):
            steering = -1
        if wx.GetKeyState(wx.WXK_RIGHT):
            steering = 1
        
        wx.GetApp().autopilot_thread.set_kbd_control(steering, throttle)


    def OnQuit(self, event):
        self.Close()

    def OnClose(self, event):
        # Deinitialize the frame manager
        self.manager.UnInit()
        # Delete the frame
        self.Destroy()
