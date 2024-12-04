"""Image as an OpenGL texture."""

import wx
from OpenGL.GL import (glGenTextures, glBindTexture, glPixelStorei,
                       glTexImage2D, glDeleteTextures, GL_TEXTURE_2D,
                       GL_UNPACK_ALIGNMENT, GL_RGBA, GL_RGB, GL_UNSIGNED_BYTE)

class Image(object):
    """Image as an OpenGL texture."""
    def __init__(self, path):
        """Load image from PATH as an OpenGL texture."""
        self.image = wx.Image(path)
        # self.stack = []
        self.width, self.height = self.image.GetSize()
        self.id = glGenTextures(1)
        self.upload_texture()


    def upload_texture(self):
        glBindTexture(GL_TEXTURE_2D, self.id)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                     GL_RGB, GL_UNSIGNED_BYTE, self.image.GetData())


    def __del__(self):
        glDeleteTextures(self.id)
