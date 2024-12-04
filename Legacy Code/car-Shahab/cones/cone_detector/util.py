"""Convenience functions for Cone Annotation Tool."""

import fnmatch
import os
import psutil
from OpenGL.GL import (glBegin, glEnd, glVertex2f, glActiveTexture,
                       glTexCoord2f, glTexEnvf, glTexParameterf,
                       glBindTexture, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                       GL_TEXTURE_MIN_FILTER, GL_NEAREST, GL_TEXTURE_ENV,
                       GL_TEXTURE_ENV_MODE, GL_DECAL, GL_QUADS)
import config


def read_text(filename):
    with open(filename, 'r') as f:
        result = f.read()
    return result


def write_text(filename, text):
    with open(filename, "w") as f:
        f.write(text)


def draw_quad(x1, y1, x2, y2):
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(x1, y1)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(x2, y1)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(x2, y2)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(x1, y2)
    glEnd()

def draw_quad_solid(x1, y1, x2, y2):
    glBegin(GL_QUADS)
    glVertex2f(x1, y1)
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

    
def select_texture(gl_idx, tex_id):
    """Select and bind OpenGL texture. Set filters."""
    glActiveTexture(gl_idx)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    # glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)



def in_bbox(x, y, bbox):
    return x >= bbox[0] and x <= bbox[0] + bbox[2] and y >= bbox[1] and y <= bbox[1] + bbox[3]


def glob_files(path, mask):
    matches = []
    for root, _, filenames in os.walk(path):
        # if root.endswith('flipped'):
            # continue
        for ext in mask:
            for filename in fnmatch.filter(filenames, ext):
                matches.append(os.path.join(root, filename))
    return matches


def memory():
    return psutil.virtual_memory().available / (1024 * 1024)
