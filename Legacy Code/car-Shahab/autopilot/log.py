from multiprocessing import Lock
# import wx

log_lock = Lock()

def log(text):
    # app = wx.App.Get()
    # if app and hasattr(app, 'frame') and app.frame and app.frame.console:
    #     app.frame.console.write(text + '\n')
    #     try:
    #         wx.SafeYield(frame)
    #     except:
    #         pass
    # else:
    log_lock.acquire()
    print(str(text))
    log_lock.release()
