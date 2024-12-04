import math
import copy
import wx
from wx import glcanvas
from OpenGL.GL import (shaders, glColor4f, glLineWidth, glLineStipple, glPushAttrib,
                       glPopAttrib, glClear, glEnable, glDisable, glActiveTexture, glBlendFunc,
                       GL_COLOR_BUFFER_BIT,  GL_DEPTH_BUFFER_BIT, GL_BLEND, GL_TEXTURE0,
                       GL_TEXTURE_2D,  GL_LIGHTING, GL_ENABLE_BIT, GL_LINE_STIPPLE, GL_LINES,
                       GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
import numpy as np
import cv2
from image import *
from image_viewer import ImageViewer
from util import *
# from cone_tool import log, frame
import config

SELECTED_ALL = 0
SELECTED_N = 1
SELECTED_S = 2
SELECTED_W = 3
SELECTED_E = 4
SELECTED_NW = 5
SELECTED_NE = 6
SELECTED_SW = 7
SELECTED_SE = 8

      
class ImageEditor(ImageViewer):
    """Image annotation tool"""
    def __init__(self, parent, id = wx.ID_ANY,
                 attribList=(glcanvas.WX_GL_RGBA, glcanvas.WX_GL_DOUBLEBUFFER, glcanvas.WX_GL_DEPTH_SIZE, 24),
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='editor'):
        super(self.__class__, self).__init__(parent, id, attribList, pos, size, style, name)
        self.image = None
        self.parent = parent
        self.label = 1
        self.old_x = 0
        self.old_y = 0
        self.left_down = False
        self.right_down = False
        self.right_popup = False

        self.bbox = None
        self.bboxes = []

        self.stack = []

        self.selected = None
        self.selected_how = SELECTED_ALL
        self.cv_image = None
        self.cv_grayscale = None
        self.cone_cascade = cv2.CascadeClassifier(config.DETECTOR_FN)

        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMotion)


    def load_image(self, fn):
        # cone_tool.log('load_image ' + fn)
        self.fn = fn
        self.stack = []
        self.bboxes = []
        self.image = Image(fn)
        # log('Looking for ' + labels_fn)
        self.bboxes = load_labels(labels_fn(fn))

        self.cv_image = np.fromstring(bytes(self.image.image.GetData()), np.uint8).reshape(self.image.height, self.image.width, 3)
        self.cv_grayscale = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2GRAY)

        # self.auto_zoom()
        self.OnDraw()

    # def select_tool(self, tool):
    #     cone_tool.log('Selecting tool ' + str(tool))
    #     self.tool = tool
    #     if self.tool == TOOL_SELECT:
    #         self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))
    #     if self.tool == TOOL_FILL:
    #         self.SetCursor(self.parent.cursor_fill)
    #     if self.tool == TOOL_PENCIL:
    #         self.SetCursor(self.parent.cursor_pencil)

        
    def InitGL(self):
        pass
    
    def OnDraw(self):
        if (not self.parent.IsShown()) or (not self.init):
            return
        # Clear color and depth buffers
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # self.SwapBuffers()

        
        if not self.image:
            self.SwapBuffers()
            return
        
        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)
        glActiveTexture(GL_TEXTURE0)
        glEnable(GL_TEXTURE_2D)
        
        select_texture(GL_TEXTURE0, self.image.id)
        draw_quad(self.view_x, self.view_y,
                  self.view_x + self.image.width * self.zoom,
                  self.view_y + self.image.height * self.zoom)
        glDisable(GL_TEXTURE_2D)
        shaders.glUseProgram(0)

            
        if self.zoom >= 5.0:
            self.draw_grid()

        if not (self.bbox is None):
            self.draw_bbox([round(x) for x in self.bbox], config.LABEL_COLOURS[int(self.label)], 1, 1, False, False, False, False)
            self.draw_bbox([round(x) for x in self.bbox], config.LABEL_COLOURS_SELECTED[int(self.label)], 1, 3, False, False, False, False)

        for idx, b in enumerate(self.bboxes):
            if idx == self.selected:
                if self.selected_how == SELECTED_N:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, True, True, True, True)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, True, False, False, False)
                elif self.selected_how == SELECTED_S:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, False, True, False, False)
                elif self.selected_how == SELECTED_E:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, False, False, True, False)
                elif self.selected_how == SELECTED_W:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, False, False, False, True)
                elif self.selected_how == SELECTED_NW:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, True, False, False, True)
                elif self.selected_how == SELECTED_NE:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, True, False, True, False)
                elif self.selected_how == SELECTED_SW:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, False, True, False, True)
                elif self.selected_how == SELECTED_SE:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, False, True, True, False)
                else:
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS[int(b[4])], 1, 1, False)
                    self.draw_bbox([round(x) for x in b], config.LABEL_COLOURS_SELECTED[int(b[4])], 1, 3, False, False, False, False)
            else:
                self.draw_bbox(b, config.LABEL_COLOURS[int(b[4])], 1, 1, True, True, True, True)
            
        self.SwapBuffers()

    def draw_bbox(self, bbox, colour, a = 1.0, w = 2.0, dashed_n = True, dashed_s = True, dashed_e = True, dashed_w = True):
        sx1, sy1 = self.im2screen(bbox[0], bbox[1])
        sx2, sy2 = self.im2screen(bbox[0] + bbox[2], bbox[1] + bbox[3])
        glColor4f(colour[0], colour[1], colour[2], a)
        glDisable(GL_BLEND)
        glLineWidth(w)
        glPushAttrib(GL_ENABLE_BIT)
        glLineStipple(1, 0x00FF)
        if not dashed_n:
            glEnable(GL_LINE_STIPPLE)
        else:
            glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(sx1, sy1)
        glVertex2f(sx2, sy1)
        glEnd()
        if not dashed_w:
            glEnable(GL_LINE_STIPPLE)
        else:
            glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(sx1, sy1)
        glVertex2f(sx1, sy2)
        glEnd()
        if not dashed_s:
            glEnable(GL_LINE_STIPPLE)
        else:
            glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(sx1, sy2)
        glVertex2f(sx2, sy2)
        glEnd()
        if not dashed_e:
            glEnable(GL_LINE_STIPPLE)
        else:
            glDisable(GL_LINE_STIPPLE)
        glBegin(GL_LINES)
        glVertex2f(sx2, sy1)
        glVertex2f(sx2, sy2)
        glEnd()
        glPopAttrib()
        
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
        
        
    def OnLeftDown(self, event):
        # self.letter_menu.Show(False)
        x, y = event.GetPosition()
        
        self.old_x, self.old_y = event.GetPosition()
        self.left_down = True
        if not self.selected is None:
            self.push()


    def OnRightDown(self, event):
        # if not self.letter_menu.IsShown():
        #     self.right_popup = True # Possibly a popup menu

        # self.letter_menu.Show(False)
        self.old_x, self.old_y = event.GetPosition()
        self.right_down = True

    def OnLeftUp(self, event):
        self.left_down = False
        if not (self.bbox is None):
            bbox = [round(x) for x in normalise_bbox(self.bbox)]
            self.push()
            self.bboxes.append(bbox)
            self.bbox = None
            # cone_tool.log('Current' + str(self.bboxes));
            # cone_tool.log('Stack' + str(self.stack));
            self.OnDraw()
            self.save()
        else:
            normalised = []
            for b in self.bboxes:
                normalised.append([round(x) for x in normalise_bbox(b)])
            self.bboxes = normalised
            self.save()
            

    def OnRightUp(self, event):
        self.right_down = False
        if self.right_popup:
            self.OnPopup(event)
            
        self.right_popup = False
        

    def OnMotion(self, event):
        self.SetFocus()
        x, y = event.GetPosition()
        im_x, im_y = self.screen2im(x, y)
        if self.left_down:
            if self.bbox is None:
                if (not self.selected is None) and not (self.selected_how == SELECTED_ALL):
                    old_im_x, old_im_y = self.screen2im(self.old_x, self.old_y)
                    if self.selected_how == SELECTED_W:
                        self.bboxes[self.selected][0] += (im_x - old_im_x)
                        self.bboxes[self.selected][2] -= (im_x - old_im_x)
                    if self.selected_how == SELECTED_E:
                        self.bboxes[self.selected][2] += (im_x - old_im_x)
                    if self.selected_how == SELECTED_N:
                        self.bboxes[self.selected][1] += (im_y - old_im_y)
                        self.bboxes[self.selected][3] -= (im_y - old_im_y)
                    if self.selected_how == SELECTED_S:
                        self.bboxes[self.selected][3] += (im_y - old_im_y)
                    if self.selected_how == SELECTED_NW:
                        self.bboxes[self.selected][0] += (im_x - old_im_x)
                        self.bboxes[self.selected][2] -= (im_x - old_im_x)
                        self.bboxes[self.selected][1] += (im_y - old_im_y)
                        self.bboxes[self.selected][3] -= (im_y - old_im_y)
                    if self.selected_how == SELECTED_NE:
                        self.bboxes[self.selected][2] += (im_x - old_im_x)
                        self.bboxes[self.selected][1] += (im_y - old_im_y)
                        self.bboxes[self.selected][3] -= (im_y - old_im_y)
                    if self.selected_how == SELECTED_SW:
                        self.bboxes[self.selected][0] += (im_x - old_im_x)
                        self.bboxes[self.selected][2] -= (im_x - old_im_x)
                        self.bboxes[self.selected][3] += (im_y - old_im_y)
                    if self.selected_how == SELECTED_SE:
                        self.bboxes[self.selected][2] += (im_x - old_im_x)
                        self.bboxes[self.selected][3] += (im_y - old_im_y)
                else:
                    self.bbox = [im_x, im_y, 0, 0, self.label]
            else:
                self.right_popup = False # Motion has occurred, hence this is not popup menu
                old_im_x, old_im_y = self.screen2im(self.old_x, self.old_y)
                self.bbox[2] += (im_x - old_im_x)
                self.bbox[3] += (im_y - old_im_y)
            self.old_x, self.old_y = x, y
            self.OnDraw()
            return
        else:
            self.selected, self.selected_how = self.check_selection(x, y)
            if self.selected is None:
                self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            else:
                if self.selected_how == SELECTED_W or self.selected_how == SELECTED_E:
                    self.SetCursor(wx.Cursor(wx.CURSOR_SIZEWE))
                if self.selected_how == SELECTED_N or self.selected_how == SELECTED_S:
                    self.SetCursor(wx.Cursor(wx.CURSOR_SIZENS))
                if self.selected_how == SELECTED_NW or self.selected_how == SELECTED_SE:
                    self.SetCursor(wx.Cursor(wx.CURSOR_SIZENESW))
                if self.selected_how == SELECTED_SW or self.selected_how == SELECTED_NE:
                    self.SetCursor(wx.Cursor(wx.CURSOR_SIZENWSE))
                elif self.selected_how == SELECTED_ALL:
                    self.SetCursor(wx.Cursor(wx.CURSOR_ARROW))
            self.OnDraw()

        if self.right_down:
            self.view_x += (x - self.old_x)
            self.view_y += (y - self.old_y)
            self.old_x, self.old_y = x, y
            self.OnDraw()
            return

        wx.GetApp().frame.GetStatusBar().SetStatusText("(%d, %d)" % (im_x, im_y), 1)


    def check_selection(self, x, y):
        selected = None
        selected_dist = 1e10
        selected_area = 1e10
        selected_how = SELECTED_ALL
        HANDLE_SIZE = 4
        for idx, b in enumerate(self.bboxes):
            sb = self.bbox_im2screen(b)
            # W
            if x >= sb[0] - HANDLE_SIZE and x <= sb[0] + HANDLE_SIZE and y >= sb[1] + HANDLE_SIZE and y <= sb[1] + sb[3] - HANDLE_SIZE:
                dist = abs(x - sb[0])
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_W
                    continue
            # E
            if x >= sb[0] + sb[2] - HANDLE_SIZE and x <= sb[0] + sb[2] + HANDLE_SIZE and y >= sb[1] + HANDLE_SIZE and y <= sb[1] + sb[3] - HANDLE_SIZE:
                dist = abs(x - sb[0] + sb[2])
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_E
                    continue
            # N
            if x >= sb[0] + HANDLE_SIZE and x <= sb[0] + sb[2] - HANDLE_SIZE and y >= sb[1] - HANDLE_SIZE and y <= sb[1] + HANDLE_SIZE:
                dist = abs(y - sb[1])
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_N
                    continue
            # S
            if x >= sb[0] + HANDLE_SIZE and x <= sb[0] + sb[2] - HANDLE_SIZE and y >= sb[1] + sb[3] - HANDLE_SIZE and y <= sb[1] + sb[3] + HANDLE_SIZE:
                dist = abs(y - sb[1])
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_S
                    continue
            # NW
            if x >= sb[0] - HANDLE_SIZE and x <= sb[0] + HANDLE_SIZE and y >= sb[1] - HANDLE_SIZE and y <= sb[1] + HANDLE_SIZE:
                dist = math.sqrt(float(x - sb[0]) * (x - sb[0]) + float(y - sb[1]) * (y - sb[1]))
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_NW
                    continue
            # NE
            if x >= sb[0] + sb[2] - HANDLE_SIZE and x <= sb[0] + sb[2] + HANDLE_SIZE and y >= sb[1] - HANDLE_SIZE and y <= sb[1] + HANDLE_SIZE:
                dist = math.sqrt(float(x - sb[0] - sb[2]) * (x - sb[0] - sb[2]) + float(y - sb[1]) * (y - sb[1]))
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_NE
                    continue
            # SW
            if x >= sb[0] - HANDLE_SIZE and x <= sb[0] + HANDLE_SIZE and y >= sb[1] + sb[3] - HANDLE_SIZE and y <= sb[1] + sb[3] + HANDLE_SIZE:
                dist = math.sqrt(float(x - sb[0]) * (x - sb[0]) + float(y - sb[1] - sb[3]) * (y - sb[1] - sb[3]))
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_SW
                    continue
                    
            # SE
            if x >= sb[0] + sb[2] - HANDLE_SIZE and x <= sb[0] + sb[2] + HANDLE_SIZE and y >= sb[1] + sb[3] - HANDLE_SIZE and y <= sb[1] + sb[3] + HANDLE_SIZE:
                dist = math.sqrt(float(x - sb[0] - sb[2]) * (x - sb[0] - sb[2]) + float(y - sb[1] - sb[3]) * (y - sb[1] - sb[3]))
                if dist < selected_dist:
                    selected = idx
                    selected_dist = dist
                    selected_how = SELECTED_SE
                    continue

            # The entire bbox
            if x >= sb[0] and x <= sb[0] + sb[2] and y >= sb[1] and y <= sb[1] + sb[3]:
                area = b[2] * b[3]
                if area < selected_area:
                    selected = idx
                    selected_area = area
                    selected_how = SELECTED_ALL

        return selected, selected_how
        
    def screen2im(self, x, y):
        return float(x - self.view_x) / self.zoom, float(y - self.view_y) / self.zoom

    def im2screen(self, im_x, im_y):
        return (float(self.view_x) + im_x * self.zoom, float(self.view_y) + im_y * self.zoom)

    def bbox_im2screen(self, b):
        sx1, sy1 = self.im2screen(b[0], b[1])
        sx2, sy2 = self.im2screen(b[0] + b[2], b[1] + b[3])
        return [sx1, sy1, sx2 - sx1, sy2 - sy1, b[4]]

    def auto_annotate(self):
        cones = self.cone_cascade.detectMultiScale(self.cv_grayscale, 1.1, 4)
        self.push()

        # Remove padding
        self.bboxes = []
        pad = config.BBOX_PADDING
        for (x, y, w, h) in cones:
            self.bboxes.append([x + pad, y + pad, w - 2 * pad, h - 2 * pad, 1])
            
        self.OnDraw()
        self.save()

    def set_label(self, label):
        self.label = label
        if not (self.selected is None):
            self.push()
            self.bboxes[self.selected][4] = label
            self.OnDraw()
            self.save()

    def delete(self):
        if not (self.selected is None):
            self.push()
            self.bboxes = self.bboxes[:self.selected] + self.bboxes[self.selected + 1:]
            self.selected = None
            self.save()
            
    def push(self):
        self.stack.append(copy.deepcopy(self.bboxes))
        # cone_tool.log('Pushing ' + str(self.bboxes))
        # cone_tool.log('Stack became ' + str(self.stack))
        
    def undo(self):
        # cone_tool.log('Undo')
        if len(self.stack) > 0:
            self.bboxes = copy.deepcopy(self.stack.pop())
            # cone_tool.log('Popped ' + str(self.bboxes))
            self.OnDraw()
            self.save()
        else:
            log('No more actions to undo.')

    def save(self):
        # log('Saving ' + str(self.bboxes))
        count = [0] * 5
        for bb in self.bboxes:
            count[int(bb[4])] += 1
        wx.GetApp().frame.image_list.set_bbox_count(count)
        try:
            with open(labels_fn(self.fn), 'w') as f:
                for bb in self.bboxes:
                    f.write("%d %d %d %d %d\n" % (bb[4] - 1, bb[0] + 1, bb[1] + 1, bb[2], bb[3]))
        except:
            log('Could not save changes!')
