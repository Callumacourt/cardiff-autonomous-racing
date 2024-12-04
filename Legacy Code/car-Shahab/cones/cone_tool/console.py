"""Console window."""
# import StringIO
import wx

class Console(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY,
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent, id, pos, size, style)

        self.output = wx.TextCtrl(self, -1, '',
                                  wx.DefaultPosition, wx.Size(0, 640),
                                  wx.TE_MULTILINE |  wx.TE_READONLY)
        self.input = wx.TextCtrl(self, -1, '',
                                 wx.DefaultPosition, wx.DefaultSize,
                                 wx.TE_PROCESS_ENTER)
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(self.output, 1, wx.ALL | wx.EXPAND)
        # box.Add(self.input, 0, wx.ALL | wx.EXPAND)

        # self.input.Bind(wx.EVT_TEXT_ENTER, self.onEnter)

        font = wx.Font(12, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Ubuntu Mono')
        self.output.SetFont(font)
        # self.input.SetFont(font)

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

    def write(self, string):
        self.output.AppendText(string)
        # self.output.SetInsertionPointEnd()
        # self.output.ShowPosition(self.output.GetLastPosition())
        # wx.SafeYield(cone_tool.frame)
        # self.Refresh()
