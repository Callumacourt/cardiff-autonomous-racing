import wx
import wx.lib.agw.aui as aui
from console import Console
from simulator_viewer import *
from util import read_text, write_text
from log import log
from settings import *
from simulator_thread import *
# from training import *

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
        self.console = Console(self)
        self.viewer = SimulatorViewer(self)
        self.sim = Simulator(track_fn=None, agent_fn=wx.App.Get().args.agent)
        self.settings = Settings(self)
        self.timer = wx.Timer(self)

        # Panes
        self.manager.AddPane(self.viewer, aui.AuiPaneInfo().CenterPane())
        self.manager.AddPane(self.settings, aui.AuiPaneInfo().Left().BestSize(
            300, 600).Name('Settings').Caption('Settings').CloseButton(False).Layer(1))
        # self.manager.AddPane(self.console, aui.AuiPaneInfo().Bottom().Name(
        #     'Console').Caption('Console').CloseButton(True).Layer(0))
        # self.manager.GetPane("Console").dock_proportion = 40
        # self.manager.GetPane("Settings").dock_proportion = 60

        # Events
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKey)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.sim_thread = SimulatorThread(self.OnTick, self.sim)
        self.timer.Start(20)
        wx.CallAfter(self.after_init)

    def after_init(self):
        wx.SafeYield()
        self.manager.Update()
        self.Refresh()
        self.SetFocus()

        self.sim_thread.start()
        self.viewer.set_simulator(self.sim)
        # self.sim_thread.train()
        self.viewer.after_init()

    def OnTick(self):
        # print('OnTick')
        self.sim.step_agent()
        self.viewer.OnDraw()

    def OnTimer(self, event):
        throttle = 0
        brakes = 0
        steering = 0
        # print('OnTimer')
        if wx.GetKeyState(wx.WXK_UP):
            throttle = 1
        if wx.GetKeyState(wx.WXK_DOWN):
            brakes = 1
        if wx.GetKeyState(wx.WXK_LEFT):
            steering = -1
        if wx.GetKeyState(wx.WXK_RIGHT):
            steering = 1

        if self.sim.agent is None:
            self.sim.control(throttle, steering, brakes)

    def OnKey(self, event):
        # focused = wx.Window.FindFocus()
        # if isinstance(focused, wx.TextCtrl):
        #     event.Skip()
        #     return
        print('OnKey')
        code = event.GetKeyCode()
        if code == ord('Q'):
            if wx.GetKeyState(wx.WXK_CONTROL):
                self.Close()
        elif code == ord('C'):
            self.viewer.auto_zoom()
        elif code == wx.WXK_F10:
            self.viewer.screenshot()
        elif code == wx.WXK_ESCAPE:
            self.sim.reset()
        elif code == ord(' '):
            if self.sim_thread.paused:
                self.sim_thread.play()
            else:
                self.sim_thread.pause()
        # elif code == wx.WXK_UP:
        #     self.sim.control(1, 0)
        # elif code == wx.WXK_DOWN:
        #     self.sim.control(-1, 0)
        # elif code == wx.WXK_LEFT:
        #     self.sim.control(0, -1)
        # elif code == wx.WXK_RIGHT:
        #     self.sim.control(0, 1)

        else:
            event.Skip()

    def OnQuit(self, event):
        self.Close()

    def OnClose(self, event):
        # Stop the sssimulator thread
        self.sim_thread.abort()
        # Deinitialize the frame manager
        self.manager.UnInit()
        # Delete the frame
        self.Destroy()

    def display_help(self):
        log('Racing Simulator. Copyright (c) Kirill Sidorov and Cardiff Racing Driverless, 2019.')
        log('')
        log('USAGE:')
        log('Space: play/pause')
        log('C: Auto zoom and center the image.')
