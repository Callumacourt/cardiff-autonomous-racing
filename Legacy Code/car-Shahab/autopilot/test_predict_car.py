#!env python3
from car import Car
import numpy as np
car = Car()
X = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
ctr = np.array([0.1, 1.0])

dt = 0.05
for i in range(10):
    X = car.advance(X, ctr, dt)
    print("% .4f % .4f % .4f % .4f % .4f % .4f % .4f % .4f % .4f" % (X[0], X[1], X[2], X[3], X[4], X[5], X[6], X[7], X[8]))
