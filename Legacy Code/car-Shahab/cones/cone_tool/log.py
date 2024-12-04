import wx

def log(text):
    app = wx.GetApp()
    frame = app.frame
    if frame and frame.console:
        frame.console.write(text + '\n')
        try:
            wx.SafeYield(frame)
        except BaseException:
            pass
    else:
        print(str(text) + '\n')
