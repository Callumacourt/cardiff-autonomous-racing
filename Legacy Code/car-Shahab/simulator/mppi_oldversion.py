import math
#from math import sin, cos, sqrt, atan2, radians, pi, exp
import scipy.integrate as integrate
import sys
import matplotlib.pyplot as plt
import numpy as np
from simslam import compute_jacobians_fast, update_kf_with_cholesky_fast, proposal_sampling_fast, compute_weight_fast, pi_2_pi
# from simslam import pi_2_pi as pi2pi
# import matplotlib.pyplot as plt

class MPPI:
    def __init__(self, x0, u, num_timesteps, number_of_samples, sigma, landa, sys_noise, movement):
        self.x0 = x0
        self.u = u
        self.num_timesteps = num_timesteps
        self.number_of_samples = number_of_samples
        self.sigma = sigma
        self.landa = landa
        self.sys_noise = sys_noise
        self.movement = movement

    def system(self):
    	# control of the system
    	pass

    def instantaneous_cost():
    	# cost of getting to this state
    	pass

    def terminal_cost():
    	# final cost of this state
    	pass

    def Method(self):
    	x = np.zeros(num_timesteps)
		Sys_Error = np.zeros(num_timesteps)
		Sample_Costs = np.zeros(number_of_samples)
		weight = np.zeros(number_of_samples)
		for i in Sys_Error:
			Sys_Error[i] = sys_noise ** i
		x[0] = x0
		for k in range(0,number_of_samples):
			sample_cost = 0
			for i in range(1,num_timesteps):
				x[i] = system(x[i-1], u[i-1]+Sys_Error[i-1])
				sample_cost += (instantaneous_cost(x[i], u[i]) + landa*(u[i]**num_timesteps)*(sigma**-1)*Sys_Error[i-1])
			sample_cost += terminal_cost(x[num_timesteps-1], u[num_timesteps-1])
			Sample_Costs[k] = sample_cost
		beta = min(Sample_Costs)
		normal = 0
		for a in range(0,number_of_samples):
			normal += math.exp((-1/landa)*(Sample_Costs[a]-beta))
		for b in range(0,number_of_samples):
			weight[b] = (1/normal)*math.exp((-1/landa)*(Sample_Costs[b]-beta))
		for s in range(0,num_timesteps):
			for i in range(0,number_of_samples):
				u[s] += weight[i]*Sample_Costs[i]
		#action u[0] movement
		movement = np.append(movement, u[0])
		movement = np.delete(movement, 0)
		u = np.delete(u, 0)
		return x, u, movement