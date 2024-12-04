#!env python3

import os
import copy
import warnings
import argparse

import MultiNEAT as NEAT
from MultiNEAT.viz import Draw, DrawPhenotype
import cv2
import numpy as np


parser = argparse.ArgumentParser(description='Visualise (MultiNEAN) NN genome.')
parser.add_argument('genome', help='Genome to draw')
parser.add_argument('output', help='Image file name')
args = parser.parse_args()

genome = NEAT.Genome(args.genome)

# im = Draw(genome, size=(512, 512))
img = np.zeros((768, 768, 3), dtype=np.uint8)
img += 10

nn = NEAT.NeuralNetwork()
genome.BuildPhenotype(nn)
DrawPhenotype(img, (0, 0, 768, 768), nn, 10, 5)

cv2.imwrite(args.output, img)
