# coding: utf-8

import time
import math
from math import sin, cos, sqrt, atan2
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
                       GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_COLOR_LOGIC_OP, GL_XOR, GL_UNSIGNED_BYTE, GL_RGB, glEnableClientState, glEnableClientState, glVertexPointer, GL_VERTEX_ARRAY, glDrawArrays, GL_FLOAT
                       )
import OpenGL.arrays.vbo as glvbo
# from OpenGL.GL import *
# import config
# import training_tool
from image import *
from util import *
from log import log
import FTGL
from config import config
import numpy as np
from timer import Timer
from simgeom import car_bbox as rotated_box
from simulator import RESOLUTION

SCALE = 4
SIZE = 256


class SimulatorViewer(glcanvas.GLCanvas):
    """Image viewer using OpenGL"""

    def __init__(self, parent, id=wx.ID_ANY,
                 attribList=(glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER,
                             glcanvas.WX_GL_DEPTH_SIZE, 24),
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='canvas'):
        super(SimulatorViewer, self).__init__(
            parent, id, attribList, pos, size, 0, name)

        self.sim = None
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
        self.wheel = None
        self.hidpi_scale = 2 if config.HIDPI else 1

        self.landmarks = None
        self.vbo_landmarks = None

        # self.Resize()
        # wx.CallAfter(self.after_init)

    def after_init(self):
        self.Refresh()
        self.Resize()
        self.SetCurrent(self.context)
        self.font = FTGL.TextureFont('VL-Gothic-Regular.ttf')
        self.font.FaceSize(13 * self.hidpi_scale)
        self.wheel = Image('wheel.png')

    def set_simulator(self, simulator):
        if not (self.sim is None) and self.sim:
            del self.sim

        self.sim = simulator
        self.OnDraw()

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

    def draw_poly(self, poly):
        glBegin(GL_LINES)
        for seg in range(poly.shape[1]):
            ax = poly[0][seg]
            ay = poly[1][seg]
            bx = poly[0][(seg + 1) % poly.shape[1]]
            by = poly[1][(seg + 1) % poly.shape[1]]
            sax, say = self.sim2screen(ax, ay)
            sbx, sby = self.sim2screen(bx, by)
            glVertex2f(sax, say)
            glVertex2f(sbx, sby)

        glEnd()

    def OnDraw(self):
        if (not self.parent.IsShown()) or (not self.init):
            return

        # Clear color and depth buffers
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.wheel is None:
            self.SwapBuffers()
            return

        if not self.sim:
            self.SwapBuffers()
            return

        self.draw_grid()
        self.draw_track()
        self.draw_boundaries()
        # self.draw_sensors()

        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)
        glActiveTexture(GL_TEXTURE0)
        glEnable(GL_TEXTURE_2D)
        select_texture(GL_TEXTURE0, self.wheel.id)

        alpha = self.sim.car.steering_angle * 10.0

        sa = sin(alpha)
        ca = cos(alpha)
        w = self.wheel.width * 0.5
        h = self.wheel.height * 0.5

        cx = 256
        cy = 96
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0)
        glVertex2f(-w*ca - h*sa + cx, -w*sa + h*ca + cy)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-w*ca + h*sa + cx, -w*sa - h*ca + cy)
        glTexCoord2f(1.0, 0.0)
        glVertex2f(+w*ca + h*sa + cx, +w*sa - h*ca + cy)
        glTexCoord2f(1.0, 1.0)
        glVertex2f(+w*ca - h*sa + cx, +w*sa + h*ca + cy)
        glEnd()
        glDisable(GL_TEXTURE_2D)

        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glLineWidth(1)

        # glColor4f(0.0, 0.686, 1.0, 0.5)
        # self.draw_distance_sensors(self.sim.track.inner)
        # glColor4f(1.0, 0.8, 0.0, 0.5)
        # self.draw_distance_sensors(self.sim.track.outer)

        self.draw_car()

        # reward = self.sim.reward()
        # glColor4f(0.5, 1.0, 0.2, 1.0)
        # self.text(16, 16, 'REWARD: %.2f' % (reward))
        # self.text(16, 32, 'TOTAL:  %.2f' % (self.sim.total_reward))

        glColor4f(1.0, 1.0, 0.2, 1.0)
        self.text(220, 16, '% .2f' % (math.degrees(self.sim.car.steering_angle)))

        self.draw_polar_sensors()
        self.draw_slam()
        self.SwapBuffers()

        # self.screenshot('out/%06d.jpg' % self.frame)
        # self.frame += 1

    # def draw_distance_sensors(self, poly):
    #     angle = self.sim.car.heading - self.sim.fov * 0.5
    #     step = self.sim.fov / RESOLUTION
    #     cx, cy = self.sim2screen(self.sim.car.position[0], self.sim.car.position[1])
    #     x0 = self.sim.car.position[0]
    #     y0 = self.sim.car.position[1]
    #     glBegin(GL_LINES)
    #     for i in range(RESOLUTION + 1):
    #         dx = cos(angle)
    #         dy = sin(angle)
    #         d, xi, yi = self.sim.beam_poly(x0, y0, dx, dy, poly)
    #         if not (d is None):
    #             sxi, syi = self.sim2screen(xi, yi)
    #             glVertex2f(cx, cy)
    #             glVertex2f(sxi, syi)
    #             angle += step

    #     glEnd()

    # @profile
    def draw_slam(self):
        slam = self.sim.slam
        particles = slam.particles
        num_landmarks = particles[0].lm.shape[0]
        if self.landmarks is None:
            self.landmarks = np.ndarray(shape=(num_landmarks * len(particles), 2),
                                        dtype=np.float32)

        pos = 0
        shift = np.array([[float(self.view_x), float(self.view_y)]]).astype(np.float32)
        for i in range(len(particles)):
            self.landmarks[pos:pos + num_landmarks, :] = particles[i].lm
            pos += num_landmarks
        self.landmarks = self.landmarks * float(self.zoom) * SCALE + shift

        if self.vbo_landmarks is None:
            self.vbo_landmarks = glvbo.VBO(self.landmarks)
        else:
            self.vbo_landmarks.set_array(self.landmarks)

        
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glPointSize(2.0 * self.zoom)

        glColor4f(1.0, 0.0, 1.0, 0.25)
        self.vbo_landmarks.bind()
        glEnableClientState(GL_VERTEX_ARRAY)
        # these vertices contain 2 single precision coordinates
        glVertexPointer(2, GL_FLOAT, 0, self.vbo_landmarks)
        # draw "count" points from the VBO
        glDrawArrays(GL_POINTS, 0, self.landmarks.shape[0])
        self.vbo_landmarks.unbind()

        
        glBegin(GL_POINTS)

        for i in range(len(particles)):
            glColor4f(1.0, 0.0, 0.0, 0.2)
            cx, cy = self.sim2screen(particles[i].x, particles[i].y)
            glVertex2f(cx, cy)
            # glColor4f(1.0, 1.0, 1.0, 1.0)
            # for j in range(particles[i].lm.shape[0]):
            #     cx, cy = self.sim2screen(particles[i].lm[j, 0], particles[i].lm[j, 1])
            #     glVertex2f(cx, cy)
        HIST_LEN = 100
        
        glColor4f(0.5, 0.5, 0.5, 1.0)
        for i in range(max(0, slam.hxTrue.shape[1] - HIST_LEN), slam.hxTrue.shape[1]):
            cx, cy = self.sim2screen(slam.hxTrue[0, i], slam.hxTrue[1, i])
            glVertex2f(cx, cy)

        # glPointSize(1.0 * self.zoom) 
        glColor4f(0.2, 0.2, 1.0, 1.0)
        for i in range(max(0, slam.hxDR.shape[1] - HIST_LEN), slam.hxDR.shape[1]):
            cx, cy = self.sim2screen(slam.hxDR[0, i], slam.hxDR[1, i])
            glVertex2f(cx, cy)

        glColor4f(0.2, 0.5, 0.2, 1.0)
        for i in range(max(0, slam.hxEst.shape[1] - HIST_LEN), slam.hxEst.shape[1]):
            cx, cy = self.sim2screen(slam.hxEst[0, i], slam.hxEst[1, i])
            glVertex2f(cx, cy)

        glEnd()
        glDisable(GL_POINT_SMOOTH)
        glDisable(GL_BLEND)

    def draw_polar_sensors(self):
        sensors = self.sim.get_sensors_polar_grid(self.sim.track.outer)
        n_angle = sensors.shape[1]

        x0 = self.sim.car.position[0]
        y0 = self.sim.car.position[1]
        cx, cy = self.sim2screen(x0, y0)
        max_dist = self.sim.slam.MAX_RANGE
        glColor4f(0.2, 0.2, 0.2, 0.5)
        glBegin(GL_LINES)
        for j in [0, n_angle]:
            angle = self.sim.car.heading + (j / n_angle - 0.5) * self.sim.fov
            dx = cos(angle)
            dy = sin(angle)
            sx, sy = self.sim2screen(x0 + dx * max_dist, y0 + dy * max_dist)
            glVertex2f(cx, cy)
            glVertex2f(sx, sy)

        n_dist = sensors.shape[0]
        # for j in range(n_dist + 1):
        dist = max_dist
        steps = 10
        for a in range(steps):
            angle0 = self.sim.car.heading + (a / steps - 0.5) * self.sim.fov
            dx0 = cos(angle0)
            dy0 = sin(angle0)
            sx0, sy0 = self.sim2screen(x0 + dx0 * dist, y0 + dy0 * dist)
            angle1 = self.sim.car.heading + \
                ((a + 1) / steps - 0.5) * self.sim.fov
            dx1 = cos(angle1)
            dy1 = sin(angle1)
            sx1, sy1 = self.sim2screen(x0 + dx1 * dist, y0 + dy1 * dist)

            glVertex2f(sx0, sy0)
            glVertex2f(sx1, sy1)

        glEnd()

        # glColor4f(1.0, 0.8, 0.0, 0.5)
        # sx = 128
        # sy = 256
        # for i in range(sensors.shape[0]):
        #     for j in range(sensors.shape[1]):
        #         if sensors[i][j] > 0:
        #             self.text(sx + 10 * (sensors.shape[1] - j), sy + 10 * (sensors.shape[0] - i), '0')
        #         else:
        #             self.text(sx + 10 * (sensors.shape[1] - j), sy + 10 * (sensors.shape[0] - i), '·')

    def draw_boundaries(self):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glLineWidth(1)
        glColor4f(0.0, 0.686, 1.0, 0.5)
        self.draw_poly(self.sim.track.inner)
        glColor4f(1.0, 0.8, 0.0, 0.5)
        self.draw_poly(self.sim.track.outer)

    # def draw_sensors(self):
    #     LEN = 100
    #     fov = self.sim.fov
    #     x = self.sim.car.position[0]
    #     y = self.sim.car.position[1]
    #     cx, cy = self.sim2screen(x, y)
    #     cxl, cyl = self.sim2screen(x + LEN * math.cos(self.sim.car.heading - fov / 2),
    #                                y + LEN * math.sin(self.sim.car.heading - fov / 2))
    #     cxr, cyr = self.sim2screen(x + LEN * math.cos(self.sim.car.heading + fov / 2),
    #                                y + LEN * math.sin(self.sim.car.heading + fov / 2))

    #     glColor4f(0.5, 0.5, 0.5, 0.5)
    #     glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    #     glEnable(GL_BLEND)
    #     glLineWidth(1)
    #     glBegin(GL_LINES)
    #     glVertex2f(cx, cy)
    #     glVertex2f(cxl, cyl)
    #     glVertex2f(cx, cy)
    #     glVertex2f(cxr, cyr)
    #     glEnd()

    def draw_field(self):
        LEN = 0.5
        glBegin(GL_LINES)
        for ix in np.linspace(0, SIZE, SIZE / 4 + 1):
            for iy in np.linspace(0, SIZE, SIZE / 4 + 1):
                fx, fy = self.sim.get_field(ix, iy)
                d = self.sim.get_dist(ix, iy)
                sx, sy = self.sim2screen(ix, iy)
                dx, dy = self.sim2screen(ix + fx * LEN * d, iy + fy * LEN * d)
                if sx >= 0.0 and sx <= self.width and sy >= 0.0 and sy <= self.height:
                    glVertex2f(sx, sy)
                    glVertex2f(dx, dy)
                    glEnd()

    def draw_box(self, x, y, heading, length, width):
        sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr = rotated_box(
            x, y, heading, length, width)

        sxtl, sytl = self.sim2screen(sxtl, sytl)
        sxtr, sytr = self.sim2screen(sxtr, sytr)
        sxbl, sybl = self.sim2screen(sxbl, sybl)
        sxbr, sybr = self.sim2screen(sxbr, sybr)

        glBegin(GL_QUADS)
        glVertex2f(sxtl, sytl)
        glVertex2f(sxbl, sybl)
        glVertex2f(sxbr, sybr)
        glVertex2f(sxtr, sytr)
        glEnd()

    def draw_car(self):
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)

        # Car body
        if self.sim.cone_collision():
            glColor4f(1, 1, 1, 1.0)
        else:
            glColor4f(0.647, 0.129, 0.149, 1.0)

        self.draw_box(self.sim.car.position[0], self.sim.car.position[1],
                      self.sim.car.heading,
                      self.sim.LENGTH, self.sim.WIDTH)

        glColor4f(0.3, 0.3, 1, 1.0)
        # Wheels
        sxtl, sytl, sxtr, sytr, sxbl, sybl, sxbr, sybr = rotated_box(self.sim.car.position[0], self.sim.car.position[1],
                                                                     self.sim.car.heading, self.sim.LENGTH, self.sim.WIDTH)
        wheel_length = 0.4
        wheel_width = 0.4
        self.draw_box(sxbr, sybr,
                      self.sim.car.heading + self.sim.car.steering_angle,
                      self.sim.LENGTH * wheel_length, self.sim.WIDTH * wheel_width)
        self.draw_box(sxtr, sytr,
                      self.sim.car.heading + self.sim.car.steering_angle,
                      self.sim.LENGTH * wheel_length, self.sim.WIDTH * wheel_width)

        self.draw_box(sxbl, sybl,
                      self.sim.car.heading,
                      self.sim.LENGTH * wheel_length, self.sim.WIDTH * wheel_width)
        self.draw_box(sxtl, sytl,
                      self.sim.car.heading,
                      self.sim.LENGTH * wheel_length, self.sim.WIDTH * wheel_width)

        x = self.sim.car.position[0]
        y = self.sim.car.position[1]
        vx = cos(self.sim.car.heading)
        vy = sin(self.sim.car.heading)
        sx0, sy0 = self.sim2screen(x, y)
        gas_length = 20
        sx1, sy1 = self.sim2screen(x + vx * gas_length, y + vy * gas_length)
        fx, fy = self.sim.get_field(x, y)
        sxg1, syg1 = self.sim2screen(x + vx * gas_length * self.sim.car.throttle,
                                     y + vy * gas_length * self.sim.car.throttle)
        sxb1, syb1 = self.sim2screen(x - vx * gas_length * self.sim.car.brakes,
                                     y - vy * gas_length * self.sim.car.brakes)

        glBegin(GL_LINES)
        glColor4f(0, 0.2, 0, 1.0)
        glVertex2f(sx0, sy0)
        glVertex2f(sx1, sy1)
        glEnd()

        glLineWidth(3)
        glBegin(GL_LINES)
        glColor4f(0, 1.0, 0, 1.0)
        glVertex2f(sx0, sy0)
        glVertex2f(sxg1, syg1)

        glColor4f(1.0, 0.0, 0, 1.0)
        glVertex2f(sx0, sy0)
        glVertex2f(sxb1, syb1)
        glEnd()
        glLineWidth(1)

        # x = self.sim.car.position[0]
        # y = self.sim.car.position[1]
        # vx = self.sim.car.velocity[0]
        # vy = self.sim.car.velocity[1]
        # sx0, sy0 = self.sim2screen(x, y)
        # sx1, sy1 = self.sim2screen(x + vx, y + vy)
        # fx, fy = self.sim.get_field(x, y)

        # glColor4f(1, 1, 0, 1.0)
        # glBegin(GL_LINES)
        # glVertex2f(sx0, sy0)
        # glVertex2f(sx1, sy1)
        # glEnd()

        # sx1, sy1 = self.sim2screen(x + fx * 2.0, y + fy * 2.0)
        # glColor4f(0, 1, 0, 1.0)
        # glBegin(GL_LINES)
        # glVertex2f(sx0, sy0)
        # glVertex2f(sx1, sy1)
        # glEnd()

        glColor4f(1, 1, 1, 1.0)
        # d = self.sim.get_dist(x, y)
        # self.text(sx0 + 16, sy0, 'D: %.2f' % (d))
        vx = self.sim.car.velocity[0]
        vy = self.sim.car.velocity[1]
        # self.text(sx0 + 16, sy0 + 16 * self.hidpi_scale, 'V: %.2f' % (vx * fx + vy * fy))
        self.text(sx0 + 16, sy0 + 32 * self.hidpi_scale,
                  'S: %.2f m/s' % math.sqrt(vx * vx + vy * vy))
        # self.text(sx0 + 16, sy0 + 48 * self.hidpi_scale, 'fx: %.2f, fy: %.2f' % (fx, fy))

    def draw_track(self):
        inner = self.sim.track.inner
        outer = self.sim.track.outer
        glPointSize(6.0 * self.zoom)
        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_NOTEQUAL, 0)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_POINT_SMOOTH)
        glHint(GL_POINT_SMOOTH_HINT, GL_NICEST)
        glBegin(GL_POINTS)

        glColor4f(0.0, 0.686, 1.0, 1.0)
        for i in range(inner.shape[1]):
            cx, cy = self.sim2screen(inner[0][i], inner[1][i])
            glVertex2f(cx, cy)

        glColor4f(1.0, 0.8, 0.0, 1.0)
        for i in range(outer.shape[1]):
            cx, cy = self.sim2screen(outer[0][i], outer[1][i])
            glVertex2f(cx, cy)

        glEnd()
        glDisable(GL_POINT_SMOOTH)
        glDisable(GL_BLEND)

    def text(self, x, y, string):
        if not hasattr(self, 'font'):
            return
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        # x, y = self.sim2screen(x, y)
        glTranslatef(x, y, 0.0)
        glScalef(1.0, -1.0, 1.0)
        self.font.Render(string)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

    def textim(self, x, y, string):
        if not hasattr(self, 'font'):
            return
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPushMatrix()
        x, y = self.sim2screen(x, y)
        glTranslatef(x, y, 0.0)
        glScalef(1.0 * self.zoom, -1.0 * self.zoom, 1.0)
        self.font.Render(string)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)

    def draw_grid(self):
        glColor4f(0.3, 0.3, 0.3, 0.3)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)
        glLineWidth(1)

        step = 10

        glBegin(GL_LINES)
        for ix in np.linspace(0, SIZE, SIZE / 4 + 1):
            sx = self.view_x + ix * self.zoom * SCALE
            if sx >= 0.0 and sx <= self.width:
                glVertex2f(sx, self.view_y)
                glVertex2f(sx, self.view_y + SIZE * self.zoom * SCALE)
        for iy in np.linspace(0, SIZE, SIZE / 4 + 1):
            sy = self.view_y + iy * self.zoom * SCALE
            if sy >= 0.0 and sy <= self.height:
                glVertex2f(self.view_x, sy)
                glVertex2f(self.view_x + SIZE * self.zoom * SCALE, sy)

        glEnd()
        glDisable(GL_BLEND)

    def screen2sim(self, x, y):
        return (float(x - self.view_x) / (self.zoom * SCALE),
                float(y - self.view_y) / (self.zoom * SCALE))

    def sim2screen(self, im_x, im_y):
        return (float(self.view_x) + im_x * self.zoom * SCALE,
                float(self.view_y) + im_y * self.zoom * SCALE)

    def auto_zoom(self):
        w = SIZE * SCALE
        h = SIZE * SCALE
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
        im_x, im_y = self.screen2sim(x, y)
        if self.left_down:
            old_im_x, old_im_y = self.screen2sim(self.old_x, self.old_y)
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

        wx.App.Get().frame.GetStatusBar().SetStatusText("(%d, %d)" % (im_x, im_y), 1)

    # def draw_bbox(self, bbox, colour, a=1.0, w=2.0, dashed=False, shaded=False):
    #     sx1, sy1 = self.sim2screen(bbox[0], bbox[1])
    #     sx2, sy2 = self.sim2screen(bbox[0] + bbox[2], bbox[1] + bbox[3])
    #     glColor4f(colour[0], colour[1], colour[2], a)
    #     glEnable(GL_BLEND)
    #     glLineWidth(w)
    #     glPushAttrib(GL_ENABLE_BIT)
    #     glLineStipple(1, 0x00FF)
    #     if dashed:
    #         glEnable(GL_LINE_STIPPLE)
    #     else:
    #         glDisable(GL_LINE_STIPPLE)
    #         glBegin(GL_LINES)
    #         glVertex2f(sx1, sy1)
    #         glVertex2f(sx2, sy1)
    #         glVertex2f(sx1, sy1)
    #         glVertex2f(sx1, sy2)
    #         glVertex2f(sx1, sy2)
    #         glVertex2f(sx2, sy2)
    #         glVertex2f(sx2, sy1)
    #         glVertex2f(sx2, sy2)
    #         glEnd()
    #         glPopAttrib()
    #     if shaded:
    #         glColor4f(colour[0], colour[1], colour[2], 0.15)
    #         draw_quad_solid(sx1, sy1, sx2, sy2)

    def screenshot(self, fn='screenshot.jpg'):
        _, _, width, height = glGetIntegerv(GL_VIEWPORT)

        # Make sure the dimensions of the image are divisible by two
        # (important for ffmpeg)
        width = (width // 2) * 2
        height = (height // 2) * 2
        buffer = glReadPixels(0, 0, width, height, GL_RGB,
                              GL_UNSIGNED_BYTE)
        im = np.fromstring(buffer, "uint8", count=width *
                           height * 3).reshape(height, width, 3)
        cv2.flip(im, 0, im)
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        cv2.imwrite(fn, im)

    def save_video(self):
        pass
