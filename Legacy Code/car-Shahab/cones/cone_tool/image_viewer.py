import wx
from wx import glcanvas
from OpenGL.GLU import gluOrtho2D
from OpenGL.GL import glMatrixMode, glLoadIdentity, glViewport, GL_PROJECTION
# import config
# import cone_tool


class ImageViewer(glcanvas.GLCanvas):
    """Image viewer using OpenGL"""
    def __init__(self, parent, id=wx.ID_ANY,
                 attribList=(glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER,
                             glcanvas.WX_GL_DEPTH_SIZE, 24),
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='canvas'):
        super(ImageViewer, self).__init__(parent, id, attribList, pos, size, 0, name)

        self.init = False
        self.context = glcanvas.GLContext(self)
        self.parent = parent

        self.view_x = 0
        self.view_y = 0
        self.zoom = 1.0
        self.zoom_levels = [12.5, 25, 33, 50, 66, 100,
                            125, 150, 200, 250, 300, 350, 500, 750,
                            1000, 1500, 2000]
        self.zoom_level = 5

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)
        self.width, self.height = self.GetSize()
        self.zooming = False
        self.Resize()

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnResize(self, e):
        self.width, self.height = e.GetSize()
        self.Resize()

    def Resize(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, self.width, self.height)
        gluOrtho2D(0, self.width, self.height, 0)

        self.OnDraw()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        if not self.init:
            self.init = True
            self.InitGL()
        self.OnDraw()

    def auto_zoom(self):
        if not hasattr(self, 'image') or not self.image:
            return
        w = self.image.width
        h = self.image.height
        print(w, h, self.width, self.height)
        best_level = 0
        for z in self.zoom_levels:
            if (w * float(z) / 100.0 > self.width  * self.GetContentScaleFactor()) or (h * float(z) / 100.0 > self.height * self.GetContentScaleFactor()):
                break
            best_level += 1

        self.zoom_level = best_level


        # self.zoom = float(self.zoom_levels[self.zoom_level]) / 100.0
        self.zoom = min(float(self.width) / float(w), float(self.height) / float(h))

        wx.GetApp().frame.GetStatusBar().SetStatusText("Zoom %.0f%%" % (self.zoom * 100), 0)

        self.view_x = (float(self.width) - float(w) * self.zoom) / 2.0
        self.view_y = (float(self.height) - float(h) * self.zoom) / 2.0
        self.OnDraw()

    def OnWheel(self, event):
        # Horrible hack!
        if self.zooming:
            return
        self.zooming = True
        
        # print event
        # print event.IsButton()
        # print event.GetEventType()
        wheel = float(event.GetWheelRotation()) / event.GetWheelDelta()
        old_zoom = self.zoom
        if wheel > 0:
            self.zoom_level += 1
        else:
            self.zoom_level -= 1

        # cone_tool.log('Zoom level ' + str(self.zoom_level))

        self.zoom_level = max(0, min(len(self.zoom_levels) - 1, self.zoom_level))
        self.zoom = self.zoom_levels[self.zoom_level] * 0.01

        wx.GetApp().frame.GetStatusBar().SetStatusText("Zoom %.0f%%" % (self.zoom * 100), 0)

        # Translate the view in such a way that zooming is centered on the cursor
        x, y = event.GetPosition()
        self.view_x = x - (x - self.view_x) * self.zoom / old_zoom
        self.view_y = y - (y - self.view_y) * self.zoom / old_zoom


        self.OnDraw()
        self.zooming = False
