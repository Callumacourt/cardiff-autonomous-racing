"""Convenience functions for Cone Annotation Tool."""

import fnmatch
import math
from decimal import Decimal, ROUND_HALF_UP
import os
import psutil
from OpenGL.GL import (glBegin, glEnd, glVertex2f, glActiveTexture,
                       glTexCoord2f, glTexEnvf, glTexParameterf,
                       glBindTexture, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER,
                       GL_TEXTURE_MIN_FILTER, GL_NEAREST, GL_LINEAR, GL_TEXTURE_ENV,
                       GL_TEXTURE_ENV_MODE, GL_DECAL, GL_QUADS)
import numpy as np
import config


def round(x):                                                         #rounding variable x
    return int(Decimal(x).to_integral_value(rounding=ROUND_HALF_UP))

def read_text(filename):                                              #reading from file
    with open(filename, 'r') as f:
        result = f.read()
    return result


def write_text(filename, text):                                        #writing to file
    with open(filename, "w") as f:
        f.write(text)


def draw_quad(x1, y1, x2, y2):                                         
    glBegin(GL_QUADS)                                                  #treating each group of four vertices as an independent quadrilateral
    glTexCoord2f(0.0, 0.0)                                             #setting the current texture coordinates
    glVertex2f(x1, y1)                                                 #specifying the vertex position
    glTexCoord2f(1.0, 0.0)
    glVertex2f(x2, y1)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(x2, y2)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(x1, y2)
    glEnd()

def draw_quad_solid(x1, y1, x2, y2):
    glBegin(GL_QUADS)                                                  #treating each group of four vertices as an independent quadrilateral
    glVertex2f(x1, y1)                                                 #specifying the vertex position
    glVertex2f(x2, y1)
    glVertex2f(x2, y2)
    glVertex2f(x1, y2)
    glEnd()

    
def select_texture(gl_idx, tex_id):                                     #select and bind OpenGL texture. Set filters.
    glActiveTexture(gl_idx)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    # glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    # glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)



def in_bbox(x, y, bbox):                                               #returing some values from arraya x,y and bbox
    return x >= bbox[0] and x <= bbox[0] + bbox[2] and y >= bbox[1] and y <= bbox[1] + bbox[3]


def glob_files(path, mask):                                            #checking if file or multiple files is/are in corresponding path 
    matches = []
    for root, _, filenames in os.walk(path):                    
        if root.endswith('flipped'):
            continue
        for ext in mask:
            for filename in fnmatch.filter(filenames, ext):
                matches.append(os.path.join(root, filename))
    return matches


def memory():                                                          #for allowing the system's memory to be monitored
    return psutil.virtual_memory().available / (1024 * 1024)

def quaternion_to_euler(q):
    angles = np.zeros((3, 1))                                          #variable with 3x1 matrix of zeros for roll, pitch and yaw
    
    #finding the roll
    sinr_cosp = 2.0 * (q[0] * q[1] + q[2] * q[3])                  
    cosr_cosp = 1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2])
    angles[0] = math.atan2(sinr_cosp, cosr_cosp)
    
    #finding the pitch
    sinp = 2.0 * (q[0] * q[2] - q[3] * q[1])
    if (abs(sinp) >= 1.0):
        if sinp < 0.0:
            angles[1] = -math.pi * 0.5
        else:
            angles[1] = math.pi * 0.5
    else:
        angles[1] = math.asin(sinp)

    #finding the yaw
    siny_cosp = 2.0 * (q[0] * q[3] + q[1] * q[2]);
    cosy_cosp = 1.0 - 2.0 * (q[2] * q[2] + q[3] * q[3])
    angles[2] = math.atan2(siny_cosp, cosy_cosp)

    return angles
