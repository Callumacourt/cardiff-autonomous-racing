"""Convenience functions for Cone Annotation Tool."""

import fnmatch
import os
from OpenGL.GL import (glBegin, glEnd, glVertex2f, glActiveTexture,
                       glTexCoord2f, glTexEnvf, glTexParameterf,
                       glBindTexture, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                       GL_TEXTURE_MIN_FILTER, GL_NEAREST, GL_TEXTURE_ENV,
                       GL_TEXTURE_ENV_MODE, GL_DECAL, GL_QUADS)
import config
from log import log

def load_labels(fn):
    """Load annotated bounding boxes."""
    try:
        bboxes = []
        if os.path.isfile(fn):
            with open(fn) as f:
                for line in f:
                    bb = list(map(int, line.split(' ')))
                    bboxes.append([bb[1] - 1, bb[2] - 1, bb[3], bb[4], bb[0] + 1])
            return bboxes
    except:
        log('Could not read labels from ' + labels_fn)
    return []


def labels_fn(fn):
    """Given an image file name, compute the corresponding name of the
    file containing annotations."""
    name, _ = os.path.splitext(fn)
    return name + config.LABELS_EXT


def replace_last(string, old, new):
    return string[::-1].replace(old[::-1], new[::-1], 1)[::-1]


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


def select_texture(gl_idx, tex_id):
    """Select and bind OpenGL texture. Set filters."""
    glActiveTexture(gl_idx)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL)


def normalise_bbox(bbox):
    if bbox[2] < 0:
        bbox[0] += bbox[2]
        bbox[2] = -bbox[2]
    if bbox[3] < 0:
        bbox[1] += bbox[3]
        bbox[3] = -bbox[3]

    return bbox


def in_bbox(x, y, bbox):
    return x >= bbox[0] and x <= bbox[0] + bbox[2] and y >= bbox[1] and y <= bbox[1] + bbox[3]


def glob_files(path, mask):
    matches = []
    for root, _, filenames in os.walk(path):
        if root.endswith('flipped'):
            continue
        for ext in mask:
            for filename in fnmatch.filter(filenames, ext):
                matches.append(os.path.join(root, filename))
    return matches
