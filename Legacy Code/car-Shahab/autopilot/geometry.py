import numpy as np
from scipy.spatial import Delaunay
import math


def delaunay(points):          
    if len(points) > 2:
        try:
            return Delaunay(points).simplices           # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.Delaunay.html
        except:
            return np.zeros((0, 3), dtype=np.int32)     # 0x3 array of zeros varialbes declared as int32
    else:
        return np.zeros((0, 3), dtype=np.int32)         # 0x3 array of zeros varialbes declared as int32


def transverse_edges(points, labels, tri, max_dist=math.inf):
    '''Compute the set of edges that span from one side of the track to the other.'''
    transverse = set()                                                                                       #empty set
    for i in range(tri.shape[0]):                                                                       #for-loop in the range of the number of dimensions 'tri' variable has
        t = tri[i, :]
        if labels[t[0]] != labels[t[1]] and np.linalg.norm(points[t[0], :] - points[t[1], :]) < max_dist:
            transverse.add(tuple(sorted((t[0], t[1]))))                                                      #add to the transverse set the array 't[0], t[1]'
        if labels[t[1]] != labels[t[2]] and np.linalg.norm(points[t[1], :] - points[t[2], :]) < max_dist:
            transverse.add(tuple(sorted((t[1], t[2]))))                                                      #add to the transverse set the array 't[1], t[2]'
        if labels[t[2]] != labels[t[0]] and np.linalg.norm(points[t[2], :] - points[t[0], :]) < max_dist:
            transverse.add(tuple(sorted((t[2], t[0]))))                                                      #add to the transverse set the array 't[2], t[0]'
    return transverse


def track_boundaries(points, labels, tri):
    '''Estimate the track boundaries from triangulation. If a triangle has two vertices of one colour,
    and another vertex of a different colour, then these are on the opposite sides of the track and
    the edge with two vertices of the same colour belongs to the track boundary.'''
    edges_y = set()
    edges_b = set()
    lines_y = []
    lines_b = []
    for i in range(tri.shape[0]):                                                                        #for-loop in the range of the number of dimensions 'tri' variable has
        t = tri[i, :]
        if labels[t[0]] == 0 and labels[t[1]] == 0 and labels[t[2]] == 1:
            edges_y.add(tuple(sorted((t[0], t[1]))))                                                      #add to the edges_y set the array 't[0], t[1]'
        if labels[t[0]] == 0 and labels[t[1]] == 1 and labels[t[2]] == 0:
            edges_y.add(tuple(sorted((t[0], t[2]))))                                                      #add to the edges_y set the array 't[0], t[2]'
        if labels[t[0]] == 1 and labels[t[1]] == 0 and labels[t[2]] == 0:
            edges_y.add(tuple(sorted((t[1], t[2]))))                                                      #add to the edges_y set the array 't[1], t[2]'
        if labels[t[0]] == 1 and labels[t[1]] == 1 and labels[t[2]] == 0:
            edges_b.add(tuple(sorted((t[0], t[1]))))                                                      #add to the edges_b set the array 't[0], t[1]'
        if labels[t[0]] == 1 and labels[t[1]] == 0 and labels[t[2]] == 1:
            edges_b.add(tuple(sorted((t[0], t[2]))))                                                      #add to the edges_b set the array 't[0], t[2]'
        if labels[t[0]] == 0 and labels[t[1]] == 1 and labels[t[2]] == 1:
            edges_b.add(tuple(sorted((t[1], t[2]))))                                                      #add to the edges_b set the array 't[1], t[2]'

        for i, e in enumerate(edges_y):                                    #for-loop 'i' being the number of items in 'edges_y' and 'e' being the actual values of 'edges_y'
            lines_y.append([tuple(points[e[0], :]),                        #add to the end of array 'lines_y' the variables in 'edges_y'
                                tuple(points[e[1], :])])
        for i, e in enumerate(edges_b):                                    #add to the end of array 'lines_b' the variables in 'edges_b'
            lines_b.append([tuple(points[e[0], :]),
                                tuple(points[e[1], :])])

    return lines_y, lines_b


def poly_dist(poly, X):
    # print('poly', poly.shape)
    V = np.zeros((X.shape[0], 2))                                  #create array of zeros with dimensions 'order of dimensions of X' by 2
    D = np.full((X.shape[0]), np.inf)                              #create array of zeros with dimensions 'order of dimensions of X' by infinity
    Ds = np.full((X.shape[0]), np.inf)                             #create array of zeros with dimensions 'order of dimensions of X' by infinity
    for i in range(poly.shape[0] - 1):                             #for-loop with arange of dimensions of array 'poly' - 1
        '''Estimating distance between two nodes'''
        v0 = poly[i, :]                                            
        v1 = poly[i + 1, :]
        d, v = psdist(v0, v1, X)

        v1v0 = v1 - v0
        n = np.array([-v1v0[1], v1v0[0]])
        ds = d * np.sign(dot(v, n))

        # print(d.shape, D.shape, ds.shape, v.shape)
        less = np.where(d < D)
        # print(less)
        V[less, :] = v[less, :]
        Ds[less] = ds[less]
        D = np.minimum(d, D)

    return D, V, Ds
        
def dot(a, b):
    # print(a.shape, b.shape)
    return np.sum(a * b, axis=1)
    

def psdist(v, w, p):
    '''Estimating magnitude of distance between two nodes'''
    # print(p.shape, v.shape, w.shape)
    vw = v - w
    l2 = np.square(vw[0]) + np.square(vw[1]) # Squared length
    if l2 == 0.0:
        vp = v - p
        d = np.sqrt(np.square(vp[:, 0]) + np.square(vp[:, 1]))
        return d

    '''Estimating the minimum magnitude of distance between two nodes'''
    dt = dot(p - v, w - v)
    t = np.maximum(0, np.minimum(1, dt / l2))
    t = np.vstack((t, t))
    
    wv = (w - v).reshape((2, 1))
    # print(t.shape, w.shape, v.shape, wv.shape)
    proj = (t * wv + v.reshape((2, 1))).T
    pproj = p - proj
    d = np.sqrt(np.square(pproj[:, 0]) + np.square(pproj[:, 1]))
    return d, pproj

