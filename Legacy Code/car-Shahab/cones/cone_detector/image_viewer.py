# coding: utf-8

import time
import wx
from wx import glcanvas
# from OpenGL.GLUT import *
from OpenGL.GLU import gluOrtho2D
from OpenGL.GL import (shaders, glMatrixMode, glLoadIdentity, glViewport, glClear, glClearColor,
                       glEnable, glDisable, glActiveTexture, glPushMatrix, glPopMatrix,
                       glColor4f, glLineWidth, glLineStipple, glBlendFunc, glTranslatef,
                       glPushAttrib, glPopAttrib, glRotatef, glScalef, glGetIntegerv, glReadPixels,
                       glPointSize, glAlphaFunc, glHint, 
                       GL_BLEND, GL_LIGHTING, GL_TEXTURE0, GL_TEXTURE1, GL_VIEWPORT, GL_ALPHA_TEST,
                       GL_COLOR_BUFFER_BIT,  GL_DEPTH_BUFFER_BIT, GL_PROJECTION, GL_NOTEQUAL,
                       GL_LINE_STIPPLE, GL_LINES, GL_ALL_ATTRIB_BITS, GL_ENABLE_BIT, GL_POINT_SMOOTH,
                       GL_POINT_SMOOTH_HINT, GL_NICEST, GL_POINTS,
                       GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_COLOR_LOGIC_OP, GL_XOR, GL_UNSIGNED_BYTE, GL_RGB
                       )
from image import *
from util import *
from log import log
import FTGL
from config import config
import numpy as np
from timer import Timer
import detector

class ImageViewer(glcanvas.GLCanvas):
    """Image viewer using OpenGL"""

    def __init__(self, parent, id=wx.ID_ANY,
                 attribList=(glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER,
                             glcanvas.WX_GL_DEPTH_SIZE, 24),
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='canvas'):
        super(ImageViewer, self).__init__(
            parent, id, attribList, pos, size, 0, name)

        self.image = None
        self.detection = None
        self.init = False
        self.context = glcanvas.GLContext(self)
        self.parent = parent

        self.view_x = 0
        self.view_y = 0
        self.old_x = 0
        self.old_y = 0
        self.left_down = False
        self.right_down = False
        self.zoom = 1.0
        self.zoom_levels = [12.5, 25, 33, 50, 66, 100,
                            125, 150, 200, 250, 300, 350, 500, 750,
                            1000, 1250, 1500, 1750, 2000]
        self.zoom_level = 5
        self.hidpi_scale = 2 if config.HIDPI else 1


        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnWheel)

        self.width, self.height = self.GetSize()
        self.zooming = time.time()
        self.frame = 0

        # self.Resize()
        # wx.CallAfter(self.after_init)

    def after_init(self):
        self.Refresh()
        self.Resize()
        self.SetCurrent(self.context)
        self.font = FTGL.TextureFont('VL-Gothic-Regular.ttf')
        self.font.FaceSize(13 * self.hidpi_scale)

    # def load_image(self):
        # self.set_image(Image('../../data/cones/amz/every10/000005.png'))

    def set_image(self, image):
        if not (self.image is None) and self.image:
            del self.image
            first = False
        else:
            first = True

        self.image = image
        
        if first:
            self.auto_zoom()
        else:
            self.OnDraw()
        # self.screenshot('out/%06d.jpg' % self.frame)
        self.frame += 1

    def set_detection(self, detection):
        if not (self.detection is None) and self.detection:
            del self.detection
        self.detection = detection

    def OnEraseBackground(self, event):
        pass  # Do nothing, to avoid flashing on MSW.

    def OnResize(self, e):
        self.width, self.height = e.GetSize()
        if config.HIDPI:
            self.width *= 2
            self.height *= 2
        self.Resize()
        self.auto_zoom()
        self.OnDraw()

    def Resize(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glViewport(0, 0, self.width, self.height)
        gluOrtho2D(0, self.width, self.height, 0)

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent(self.context)
        self.Resize()
        self.OnDraw()
        if not self.init:
            self.init = True

    def OnDraw(self):
        if (not self.parent.IsShown()) or (not self.init):
            return

        # Clear color and depth buffers
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if not self.image:
            self.SwapBuffers()
            return

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)
        glActiveTexture(GL_TEXTURE0)
        glEnable(GL_TEXTURE_2D)

        glActiveTexture(GL_TEXTURE0)
        select_texture(GL_TEXTURE0, self.image.id)
        draw_quad(self.view_x, self.view_y,
                  self.view_x + self.image.width * self.zoom,
                  self.view_y + self.image.height * self.zoom)
        glDisable(GL_TEXTURE_2D)

        if config.CD_USE_ROI:
            self.draw_roi()

        # for b in detector.detector.bboxes:
        #     self.draw_bbox(b, config.LABEL_COLOURS[0], 0.3, 1, True)

        # for b in detector.detector.bboxesf:
        #     # print(b[4] + 1)
        #     self.draw_bbox(b, config.LABEL_COLOURS[b[4] + 1], 0.5, 1.5, False, True)

        # if config.SHOW_CENTRES:
            # self.show_centres()

        glColor4f(1.0, 0.686, 0.0, 1.0)
        if wx.GetApp().detector_thread.paused:
            self.text(10, 20, "PAUSED")
        else:
            self.text(10, 20, "FPS: %.1f" % wx.GetApp().detector_thread.FPS)

        if self.zoom >= 5.0:
            self.draw_grid()

        self.SwapBuffers()

    def show_centres(self):
        glPointSize(8.0)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_NOTEQUAL, 0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glBegin(GL_POINTS)

        for b in detector.detector.bboxesf:
            cx, cy = self.im2screen(b[0] + (b[2] - 1) * 0.5, b[1] + (b[3] - 1) * 0.5)
            glVertex2f(cx, cy)

        glEnd()

        glDisable(GL_POINT_SMOOTH)
        # glBlendFunc(GL_NONE, GL_NONE)
        glDisable(GL_BLEND)
        

    def text(self, x, y, string):
        if not hasattr(self, 'font'):
            return
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        x, y = self.im2screen(x, y)
        glTranslatef(x, y, 0.0)
        glScalef(1.0 * self.zoom, -1.0 * self.zoom, 1.0)
        self.font.Render(string)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

    def draw_roi(self):
        # Display the ROI with shaded bands
        glEnable(GL_BLEND)
        glColor4f(0.0, 0.0, 0.0, 0.5)
        draw_quad_solid(self.view_x, self.view_y,
                        self.view_x + self.image.width * self.zoom,
                        self.view_y + self.image.height * self.zoom * (config.CD_ROI_TOP * 0.01))
        draw_quad_solid(self.view_x, self.view_y + self.image.height * self.zoom * (1.0 - config.CD_ROI_BOTTOM * 0.01),
                        self.view_x + self.image.width * self.zoom,
                        self.view_y + self.image.height * self.zoom)
        glDisable(GL_BLEND)

    def draw_grid(self):
        glColor4f(0.3, 0.3, 0.3, 0.3)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glLineWidth(1)

        glBegin(GL_LINES)
        for ix in range(1, self.image.width):
            sx = self.view_x + ix * self.zoom
            if sx >= 0.0 and sx <= self.width:
                glVertex2f(sx, self.view_y)
                glVertex2f(sx, self.view_y + self.image.height * self.zoom)
        for iy in range(1, self.image.height):
            sy = self.view_y + iy * self.zoom
            if sy >= 0.0 and sy <= self.height:
                glVertex2f(self.view_x, sy)
                glVertex2f(self.view_x + self.image.width * self.zoom, sy)
        glEnd()
        glDisable(GL_BLEND)

    def screen2im(self, x, y):
        return float(x - self.view_x) / self.zoom, float(y - self.view_y) / self.zoom

    def im2screen(self, im_x, im_y):
        return (float(self.view_x) + im_x * self.zoom, float(self.view_y) + im_y * self.zoom)

    # def bbox_im2screen(self, b):
    #     sx1, sy1 = self.im2screen(b[0], b[1])
    #     sx2, sy2 = self.im2screen(b[0] + b[2], b[1] + b[3])
    #     return [sx1, sy1, sx2 - sx1, sy2 - sy1, b[4]]

    def auto_zoom(self):
        if not hasattr(self, 'image') or not self.image:
            return

        w = self.image.width
        h = self.image.height
        best_level = 0
        for z in self.zoom_levels:
            if (w * float(z) / 100.0 > self.width) or (h * float(z) / 100.0 > self.height):
                break
            best_level += 1

        self.zoom_level = best_level
        self.zoom = min(float(self.width) / float(w),
                        float(self.height) / float(h))

        wx.App.Get().frame.GetStatusBar().SetStatusText(
            "Zoom %.0f%%" % (self.zoom * 100), 0)

        self.view_x = (float(self.width) - float(w) * self.zoom) / 2.0
        self.view_y = (float(self.height) - float(h) * self.zoom) / 2.0
        self.OnDraw()

    def OnWheel(self, event):
        # Horrible hack!
        if time.time() - self.zooming < 0.03:
            return
        self.zooming = time.time()

        wheel = float(event.GetWheelRotation()) / event.GetWheelDelta()
        old_zoom = self.zoom
        if wheel > 0:
            self.zoom_level += 1
        else:
            self.zoom_level -= 1

        self.zoom_level = max(
            0, min(len(self.zoom_levels) - 1, self.zoom_level))
        self.zoom = self.zoom_levels[self.zoom_level] * 0.01

        wx.App.Get().frame.GetStatusBar().SetStatusText(
            "Zoom %.0f%%" % (self.zoom * 100), 0)

        # Translate the view in such a way that zooming is centered on the cursor
        x, y = event.GetPosition()
        self.view_x = x - (x - self.view_x) * self.zoom / old_zoom
        self.view_y = y - (y - self.view_y) * self.zoom / old_zoom

        self.OnDraw()

    def OnLeftDown(self, event):
        self.old_x, self.old_y = event.GetPosition()
        self.left_down = True

    def OnRightDown(self, event):
        self.old_x, self.old_y = event.GetPosition()
        self.right_down = True

    def OnLeftUp(self, event):
        self.left_down = False

    def OnRightUp(self, event):
        self.right_down = False

    def OnMotion(self, event):
        self.SetFocus()
        x, y = event.GetPosition()
        im_x, im_y = self.screen2im(x, y)
        if self.left_down:
            old_im_x, old_im_y = self.screen2im(self.old_x, self.old_y)
            self.old_x, self.old_y = x, y
            self.OnDraw()
            return
        else:
            self.OnDraw()

        if self.right_down:
            self.view_x += (x - self.old_x)
            self.view_y += (y - self.old_y)
            self.old_x, self.old_y = x, y
            self.OnDraw()
            return

        wx.App.Get().frame.GetStatusBar().SetStatusText("(%d, %d)" % (im_x, im_y), 1)

    def draw_bbox(self, bbox, colour, a=1.0, w=2.0, dashed=False, shaded=False):
        sx1, sy1 = self.im2screen(bbox[0], bbox[1])
        sx2, sy2 = self.im2screen(bbox[0] + bbox[2], bbox[1] + bbox[3])
        glColor4f(colour[0], colour[1], colour[2], a)
        glEnable(GL_BLEND)
        glLineWidth(w)
        glPushAttrib(GL_ENABLE_BIT)
        glLineStipple(1, 0x00FF)
        if dashed:
            glEnable(GL_LINE_STIPPLE)
        else:
            glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(sx1, sy1)
        glVertex2f(sx2, sy1)
        glVertex2f(sx1, sy1)
        glVertex2f(sx1, sy2)
        glVertex2f(sx1, sy2)
        glVertex2f(sx2, sy2)
        glVertex2f(sx2, sy1)
        glVertex2f(sx2, sy2)
        glEnd()
        glPopAttrib()
        if shaded:
            glColor4f(colour[0], colour[1], colour[2], 0.5)
            draw_quad_solid(sx1, sy1, sx2, sy2)

    def screenshot(self, fn='screenshot.jpg'):
        _, _, width, height = glGetIntegerv(GL_VIEWPORT)
        buffer = glReadPixels(0, 0, width, height, GL_RGB,
                              GL_UNSIGNED_BYTE)
        im = np.fromstring(buffer, "uint8", count=width * height * 3).reshape(height, width, 3)
        cv2.flip(im, 0, im)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        cv2.imwrite(fn, im)

    def save_video(self):
        pass


