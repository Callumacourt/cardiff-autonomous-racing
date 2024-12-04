"""Console window."""
# import StringIO
import wx
import platform
from log import log

class Console(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, id, pos, size, style)

        self.output = wx.TextCtrl(self, -1, '',
                                  wx.DefaultPosition, wx.Size(640, 200),
                                  wx.TE_MULTILINE |  wx.TE_READONLY | wx.TE_RICH)
        # self.input = wx.TextCtrl(self, -1, '',
        #                          wx.DefaultPosition, wx.DefaultSize,
        #                          wx.TE_PROCESS_ENTER)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.output, 1, wx.ALL | wx.EXPAND)
        # box.Add(self.input, 0, wx.ALL | wx.EXPAND)

        # self.input.Bind(wx.EVT_TEXT_ENTER, self.onEnter)

        if platform.node() == "excelsior":
            font = wx.Font(11, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'VL Gothic')
        else:
            font = wx.Font(11, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Ubuntu Mono')
            
        # self.input.SetFont(font)
        self.output.SetFont(font)
        self.default_foreground()
        self.output.SetBackgroundColour(wx.Colour(21, 21, 21))
        # self.input.SetFocus()
        self.SetSizerAndFit(box)

    # def onEnter(self, event):
    #     command = self.input.GetValue()
    #     self.write(command + '\n')
    #     self.input.SetValue('')

    #     out = StringIO.StringIO()
    #     err = StringIO.StringIO()
    #     try:
    #         eng.eval(command, nargout = 0, stdout = out, stderr = err)
    #         self.output.AppendText(str(out.getvalue()) + '\n')
    #     except:
    #         self.output.AppendText(str(err.getvalue()) + '\n')

    def default_foreground(self):
        self.output.SetForegroundColour(wx.Colour(198, 165, 123))


    def write(self, string):
        if string.startswith('INFO:'):
            self.output.SetForegroundColour(wx.Colour(184, 187, 38))
        if string.startswith('WARNING:'):
            self.output.SetForegroundColour(wx.Colour(186, 91, 52))
        if string.startswith('ERROR:'):
            self.output.SetForegroundColour(wx.Colour(149, 51, 49))

        self.output.AppendText(string)
        self.output.SetInsertionPointEnd()
        self.output.ShowPosition(self.output.GetLastPosition())
        # wx.SafeYield(cone_tool.frame)
        # self.Refresh()
