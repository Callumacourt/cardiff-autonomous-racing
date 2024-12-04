import numpy as np
import scipy.io as sio
import pycuda
from pycuda import gpuarray
import wx
from car import Car
from geometry import poly_dist
from scipy import interpolate
from math import sin, cos

class MPPI:
    def __init__(self, K=512, T=150, temperature=1.0, noise=0.003, context=None):
        self.K = np.int32(K)                                                            #defining variables for MPPI
        self.T = np.int32(T)                                                            
        self.temperature = temperature
        self.noise = noise
        self.context = context
        self.cfg = sio.loadmat('car_model.mat')['cfg'][:, 0].astype(np.float32)         #porting array from 'car_model.mat' 

        # State of the car: x, y, vx, vy, ax, ay, hdg, vhdg, ahdg, steering, throttle
        # self.X = np.zeros((11, 1), dtype=np.float32)

        # (Derivative of) control that is being evolved
        self.dF = np.zeros((self.T, 2), dtype=np.float32)                                # array of zeros created

        with open('predict_car.cu', 'r') as file:
            kernels_src = file.read()
        kernels = pycuda.compiler.SourceModule(kernels_src)
        # kernels = pycuda.driver.module_from_file('predict_car.ptx')
        # print(kernels)
        self.predict_car = kernels.get_function("predict_car")                           #porting function 'predict_car' from 'predict_car.cu'
        self.cost = np.zeros((self.K, 1), dtype=np.float32)                              #array of zeros for cost of trajectory
        self.cfg_gpu = gpuarray.to_gpu(self.cfg)                                         #more info: https://documen.tician.de/pycuda/array.html#the-gpuarray-array-class
        self.car = Car()                                                                 #for CPU checks

    @profile
    def advance(self, X_current, F_current, centreline, grid, field, dt):
        # print(X_current)
        if self.context is not None:
            self.context.push()

        score = np.sqrt(np.sum(np.square(field), axis=1))                                #current score of MPPI (to be improved)
        h = 41 # TODO: This should be a parameter!
        # score = np.reshape(score, (h, h))
        # print(score.shape)

        # print(np.amin(grid, axis=0), np.amax(grid, axis=0))
        

        # Generate perturbation to (derivative of) control
        noise = np.random.normal(loc=0.0, scale=self.noise, size=(                      #calculating noise of system (To be modified
            self.K, self.T, self.dF.shape[1])).astype(np.float32)
        # print(noise.shape)

        # print(F_current)
        # Add perturbations to control
        Fn = np.zeros((self.K, self.T, self.dF.shape[1]), dtype=np.float32)
        for k in range(self.K):
            dFn = self.dF + noise[k, :, :]
            Fn[k, :, :] = np.cumsum(dFn, axis=0) + F_current#self.X[-2:].T

        # print(Fn.shape)

        Fn_gpu = gpuarray.to_gpu(Fn)
        traj = gpuarray.zeros((self.K, self.T, 9), dtype=np.float32)

        X_gpu = gpuarray.to_gpu(X_current)
        # try:
        self.predict_car(self.K, self.T, X_gpu, Fn_gpu, self.cfg_gpu, np.float32(dt), traj,  #using the function predict_car
                         block=(int(self.K), 1, 1), grid=(1, 1))  # TODO: This is wrong!

        traj = traj.get()#.astype(np.double)
        # sio.savemat('traj.mat', {"traj": traj})

        hdg = X_current[6]                                                                                                    #arrays for calculating trajectory
        T = np.array([[cos(hdg), -sin(hdg), X_current[0]], [sin(hdg), cos(hdg), X_current[1]], [0.0, 0.0, 1.0]])              
        T = np.linalg.inv(T)
        T = T[0:2, :]
        rot = T[0:2, 0:2]
        skip = 0
        for k in range(self.K):                                                                                                      #calculating cost trajectories
            pos = traj[k, skip:, 0:2]
            # vel = (rot @ traj[k, skip:, 2:4].T).T
            # print(vel[0, :])
            # print(pos.shape)
            pos = np.hstack((pos, np.ones((pos.shape[0], 1))))
            pos_c = (T @ pos.T).T
            xi = np.int32(np.minimum(h - 1, np.maximum(0, np.round(h * ((pos_c[:, 1] + 10) / 20)))))
            yi = np.int32(np.minimum(h - 1, np.maximum(0, np.round(h * (pos_c[:, 0] / 20)))))
            idx = yi * h + xi
            if np.any(idx >= h * h) or any(idx < 0):
                self.cost[k]=1000
                continue
            C = score[idx]
            # fx = field[idx, 1]
            # fy = field[idx, 0]
            
            # direct = vel[:, 0] * fx + vel[:, 1] * fy
            speed = np.sqrt(np.square(traj[k, skip:, 2]) + np.square(traj[k, skip:, 3]))
            self.cost[k] = np.mean(C)*10 - 0.1 * np.mean(speed)# + 10.0*np.mean(np.abs(Fn[k, :, 0]))# - 1*np.mean(direct)

                                                                                                     #variables for cost trajectory
        beta = np.amin(self.cost)
        cost = np.exp(-1.0/self.temperature * (self.cost - beta))
        eta = np.sum(cost)
        omega = 1.0/eta * cost
        # print(beta, np.amax(self.cost), eta, np.amin(omega), np.amax(omega))

        # print('SUM OMEGA', np.sum(omega))
        # print(omega.shape)
        for k in range(self.K):                                                                      #trajectories with steering and throttle
             self.dF += float(omega[k, 0]) * noise[k, :, :]

        # F = np.cumsum(self.dF, axis=0) + F_current
        # self.traj_best = self.predict_car_cpu(X_current, F, dt)

        
        # print('MAX TRAJ_BEST', traj_best.shape, np.min(traj_best, axis=0))
        # sio.savemat('traj_best.mat', {"traj_best": traj_best})

        
        self.traj_all = traj[0::10, :, :]
        # print(self.traj_all.shape)
        self.traj_all = np.reshape(self.traj_all, (self.traj_all.shape[0] * self.T, 9))

        steering = self.dF[0, 0] + F_current[0]                                                      #calculating steering
        throttle = self.dF[0, 1] + F_current[1]                                                      #calculating throttle
        self.dF = np.vstack((self.dF[1:,:], self.dF[-1, :]))

        
        # finally:
        if self.context is not None:
            self.context.pop()

        spd = np.sqrt(np.square(X_current[2]) + np.square(X_current[3]))                             #calculating speed
        print("%.2f %.2f   %.2f\t%.3f %.3f beta = %.2f" % (X_current[0], X_current[1], spd, steering, throttle, beta))
        return float(steering), float(throttle)


    def predict_car_cpu(self, x, F, dt=0.05):                                                        # function which predicts car physics
        traj = np.zeros((F.shape[0], 9))                                                             # creating array
        for i in range(traj.shape[0]):                                                               # Creating physics for the different scenarios
            x = self.car.advance(x, F[i, :], dt)                                                     # using function 'advance' in car.py script
            # print(x)
            traj[i, :] = np.array(x)                                                                 # calculations put into 'traj' array
        return traj
    
