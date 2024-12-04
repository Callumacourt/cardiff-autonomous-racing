"""Image as an OpenGL texture."""

import wx
from OpenGL.GL import (glGenTextures, glBindTexture, glPixelStorei,
                       glTexImage2D, glDeleteTextures, GL_TEXTURE_2D,
                       GL_UNPACK_ALIGNMENT, GL_RGBA, GL_RGB, GL_UNSIGNED_BYTE)
import cv2

class Image(object):
    """Image as an OpenGL texture."""
    # @profile
    def __init__(self, arg):
        if isinstance(arg, str):
            bgr = cv2.imread(arg)
            self.image = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        else:
            self.image = arg

        self.height, self.width, self.channels = self.image.shape
        self.id = None
        self.upload_texture()


    # @profile
    def upload_texture(self):
        if self.id is None:
            self.id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, self.id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, self.image)


    def __del__(self):
        glDeleteTextures(self.id)
