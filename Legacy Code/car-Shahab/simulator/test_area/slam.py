# import math
from math import sin, cos, sqrt, atan2, radians, pi, exp
import sys
import numpy as np
from simslam import compute_jacobians_fast, update_kf_with_cholesky_fast, proposal_sampling_fast, compute_weight_fast, pi_2_pi
# from simslam import pi_2_pi as pi2pi
# import matplotlib.pyplot as plt


# def pi_2_pi(angle):
#     a =  (angle + pi) % (2 * pi) - pi
#     a_ = pi2pi(angle)
#     if abs(a - a_) > 0.001:
#         print('pi2pi: ', a, a_, a - a_)
#     return a


STATE_SIZE = 3  # State size [x, y, yaw, vx, vy]
LM_SIZE = 2  # LM srate size [x, y]
N_PARTICLE = 100  # number of particle
NTH = N_PARTICLE * 0.7  # Number of particle for re-sampling
# OFFSET_YAW_RATE_NOISE = 0.0

# DT = 0.1  # time tick [s]
# SIM_TIME = 50.0  # simulation time [s]
# M_DIST_TH = 2.0  # Threshold of Mahalanobis distance for data association.

N_LM = 350


class Particle:
    def __init__(self, N_LM, x, y, heading, vx, vy):
        self.w = 1.0 / N_PARTICLE
        self.x = x
        self.y = y
        self.yaw = heading
        self.vx = vx
        self.vy = vy
        self.P = np.eye(3)
        # landmark x-y positions
        self.lm = np.zeros((N_LM, LM_SIZE))
        # landmark position covariance
        self.lmP = np.zeros((N_LM * LM_SIZE, LM_SIZE))


class SLAM:
    def __init__(self, x, y, heading):
        # # Fast SLAM covariance
        # self.Q = np.diag([3.0, np.deg2rad(10.0)]) ** 2
        # self.R = np.diag([1.0, 1.0, np.deg2rad(20.0)]) ** 2

        # #  Simulation parameter
        # self.Q_sim = np.diag([0.3, np.deg2rad(2.0)]) ** 2
        # self.R_sim = np.diag([0.5, 0.5, np.deg2rad(10.0)]) ** 2
        self.MAX_RANGE = 50.0  # maximum observation range

        self.Q = np.diag([3.0, np.deg2rad(5.0)]) ** 2
        self.R = np.diag([1.0, 1.0, np.deg2rad(5.0)]) ** 2

        #  Simulation parameter
        self.Q_sim = np.diag([0.3, np.deg2rad(2.0)]) ** 2 * 0.0
        self.R_sim = np.diag([0.5, 0.5, np.deg2rad(10.0)]) ** 2 * 0.0

        self.particles = [Particle(N_LM, x, y, heading, 0.0, 0.0) for _ in range(N_PARTICLE)]

        self.fov = radians(75)
        
        # State Vector [x y yaw]'
        state = np.array([[x, y, heading]]).transpose()
        self.xEst = state#np.zeros((STATE_SIZE, 1))  # SLAM estimation
        self.xTrue = state#np.zeros((STATE_SIZE, 1))  # True state
        self.xDR = state#np.zeros((STATE_SIZE, 1))  # Dead reckoning

        # history
        self.hxEst = self.xEst
        self.hxTrue = self.xTrue
        self.hxDR = self.xTrue

    def advance(self, vx, vy, yaw_rate, RFID, dt=0.01):
        u = np.array([vx, vy, yaw_rate]).reshape(3, 1)
        self.xTrue, z, self.xDR, ud = self.observation(
            self.xTrue, self.xDR, u, RFID, dt)

        self.particles = self.fast_slam2(self.particles, ud, z, dt)

        self.xEst = self.calc_final_state(self.particles)

        x_state = self.xEst[0: STATE_SIZE]

        # store data history
        self.hxEst = np.hstack((self.hxEst, x_state))
        self.hxDR = np.hstack((self.hxDR, self.xDR))
        self.hxTrue = np.hstack((self.hxTrue, self.xTrue))

    # @profile
    def fast_slam2(self, particles, u, z, dt):
        particles = self.predict_particles(particles, u, dt)
        particles = self.update_with_observation(particles, z)
        particles = self.resampling(particles)
        return particles

    def normalize_weight(self, particles):
        sum_w = sum([p.w for p in particles])
        #print(sum_w)
        try:
            for i in range(N_PARTICLE):
                particles[i].w /= sum_w    
        except ZeroDivisionError:
            for i in range(N_PARTICLE):
                particles[i].w = 1.0 / N_PARTICLE

            return particles

        return particles

    def calc_final_state(self, particles):
        xEst = np.zeros((STATE_SIZE, 1))

        particles = self.normalize_weight(self.particles)

        for i in range(N_PARTICLE):
            xEst[0, 0] += particles[i].w * particles[i].x
            xEst[1, 0] += particles[i].w * particles[i].y
            xEst[2, 0] += particles[i].w * particles[i].yaw

        xEst[2, 0] = pi_2_pi(xEst[2, 0])

        return xEst

    def predict_particles(self, particles, u, dt):
        for i in range(N_PARTICLE):
            px = np.zeros((STATE_SIZE, 1))
            px[0, 0] = particles[i].x
            px[1, 0] = particles[i].y
            px[2, 0] = particles[i].yaw
            # px[3, 0] = particles[i].vx
            # px[4, 0] = particles[i].vy
            ud = u + (np.random.randn(1, 3) @ self.R ** 0.5).T  # add noise
            px = self.motion_model(px, ud, dt)
            particles[i].x = px[0, 0]
            particles[i].y = px[1, 0]
            particles[i].yaw = px[2, 0]
            # particles[i].vx = px[3, 0]
            # particles[i].vy = px[4, 0]

        return particles

    def add_new_lm(self, particle, z, Q_cov):
        r = z[0]
        b = z[1]
        lm_id = int(z[2])

        s = sin(pi_2_pi(particle.yaw + b))
        c = cos(pi_2_pi(particle.yaw + b))

        particle.lm[lm_id, 0] = particle.x + r * c
        particle.lm[lm_id, 1] = particle.y + r * s

        # covariance
        Gz = np.array([[c, -r * s],
                       [s, r * c]])

        particle.lmP[2 * lm_id:2 * lm_id + 2] = Gz @ Q_cov @ Gz.T

        return particle

    # @profile
    def compute_jacobians(self, particle, xf, Pf, Q_cov):
        zp = np.zeros((2, 1))
        Hv = np.zeros((2, 3))
        Hf = np.zeros((2, 2))
        Sf = np.zeros((2, 2))
        compute_jacobians_fast(xf[0, 0], xf[1, 0],
                               particle.x, particle.y, particle.yaw,
                               Pf, Q_cov,
                               zp, Hv, Hf, Sf)

        # zp_, Hv_, Hf_, Sf_ = self.compute_jacobians_old(particle, xf, Pf, Q_cov)
        # delta = np.sum(np.sum(np.abs(zp - zp_)))
        # if abs(delta) > 0.000001:
        #     print('ERROR!')
        return zp, Hv, Hf, Sf

    # def compute_jacobians_old(self, particle, xf, Pf, Q_cov):
    #     dx = xf[0, 0] - particle.x
    #     dy = xf[1, 0] - particle.y
    #     d2 = dx ** 2 + dy ** 2
    #     d = sqrt(d2)

    #     zp = np.array(
    #         [d, pi_2_pi(atan2(dy, dx) - particle.yaw)]).reshape(2, 1)

    #     Hv = np.array([[-dx / d, -dy / d, 0.0],
    #                    [dy / d2, -dx / d2, -1.0]])

    #     Hf = np.array([[dx / d, dy / d],
    #                    [-dy / d2, dx / d2]])

    #     Sf = Hf @ Pf @ Hf.T + Q_cov

    #     return zp, Hv, Hf, Sf

    # @profile
    def update_kf_with_cholesky(self, xf, Pf, v, Q_cov, Hf):
        x = np.zeros((2, 1))
        P = np.zeros((2, 2))
        update_kf_with_cholesky_fast(xf, Pf, v, Q_cov, Hf, x, P);
        # _x, _P = self.update_kf_with_cholesky_old(xf, Pf, v, Q_cov, Hf)
        # delta_x = np.sum(_x - x)
        # if abs(delta_x) > 0.000001:
        #     print(delta_x)
        # delta_P = np.sum(_P - P)
        # if abs(delta_P) > 0.000001:
        #     print(delta_P)
        return x, P

    # def update_kf_with_cholesky_old(self, xf, Pf, v, Q_cov, Hf):
    #     PHt = Pf @ Hf.T
    #     S = Hf @ PHt + Q_cov

    #     S = (S + S.T) * 0.5
    #     SChol = np.linalg.cholesky(S).T
    #     SCholInv = np.linalg.inv(SChol)
    #     W1 = PHt @ SCholInv
    #     W = W1 @ SCholInv.T

    #     x = xf + W @ v
    #     P = Pf - W1 @ W1.T
    #     return x, P

    # @profile
    def update_landmark(self, particle, z, Q_cov):
        lm_id = int(z[2])
        xf = np.array(particle.lm[lm_id, :]).reshape(2, 1)
        Pf = np.array(particle.lmP[2 * lm_id:2 * lm_id + 2])

        zp, Hv, Hf, Sf = self.compute_jacobians(particle, xf, Pf, Q_cov)

        dz = z[0:2].reshape(2, 1) - zp
        dz[1, 0] = pi_2_pi(dz[1, 0])

        xf, Pf = self.update_kf_with_cholesky(xf, Pf, dz, self.Q, Hf)

        particle.lm[lm_id, :] = xf.T
        particle.lmP[2 * lm_id:2 * lm_id + 2, :] = Pf

        return particle

    # @profile
    def compute_weight(self, particle, z, Q_cov):
        lm_id = int(z[2])
        xf = np.array(particle.lm[lm_id, :]).reshape(2, 1)
        Pf = np.array(particle.lmP[2 * lm_id:2 * lm_id + 2])
        zp, Hv, Hf, Sf = self.compute_jacobians(particle, xf, Pf, Q_cov)

        z = z.copy()
        w = compute_weight_fast(Sf, z, zp)

        # dz = z[0:2].reshape(2, 1) - zp
        # dz[1, 0] = pi_2_pi(dz[1, 0])
        # try:
        #     invS = np.linalg.inv(Sf)
        # except np.linalg.linalg.LinAlgError:
        #     return 1.0

        # num = exp(-0.5 * dz.T @ invS @ dz)
        # den = 2.0 * pi * sqrt(np.linalg.det(Sf))

        # w_ = num / den
        # print(w - w_)

        return w

    # @profile
    def proposal_sampling(self, particle, z, Q_cov):
        lm_id = int(z[2])
        xf = particle.lm[lm_id, :].reshape(2, 1)
        Pf = particle.lmP[2 * lm_id:2 * lm_id + 2]
        # State
        x = np.array([particle.x, particle.y, particle.yaw]).reshape(3, 1)
        P = particle.P
        zp, Hv, Hf, Sf = self.compute_jacobians(particle, xf, Pf, Q_cov)

        dz = z[0:2].reshape(2, 1) - zp
        dz[1] = pi_2_pi(dz[1])

        proposal_sampling_fast(Sf, Hv, dz, x, P)
        particle.P = P

        particle.x = x[0, 0]
        particle.y = x[1, 0]
        particle.yaw = x[2, 0]

        return particle


    # @profile
    def update_with_observation(self, particles, z):
        for iz in range(len(z[0, :])):
            lmid = int(z[2, iz])

            for ip in range(N_PARTICLE):
                # new landmark
                if abs(particles[ip].lm[lmid, 0]) <= 0.001:
                    particles[ip] = self.add_new_lm(
                        particles[ip], z[:, iz], self.Q)
                # known landmark
                else:
                    w = self.compute_weight(particles[ip], z[:, iz], self.Q)
                    particles[ip].w *= w

                    particles[ip] = self.update_landmark(
                        particles[ip], z[:, iz], self.Q)
                    particles[ip] = self.proposal_sampling(
                        particles[ip], z[:, iz], self.Q)

        return particles

    def resampling(self, particles):
        """
        low variance re-sampling
        """

        particles = self.normalize_weight(particles)

        pw = []
        for i in range(N_PARTICLE):
            pw.append(particles[i].w)

        pw = np.array(pw)

        Neff = 1.0 / (pw @ pw.T)  # Effective particle number
        #print(Neff, NTH)

        if Neff < NTH:  # resampling
            wcum = np.cumsum(pw)
            base = np.cumsum(pw * 0.0 + 1 / N_PARTICLE) - 1 / N_PARTICLE
            resamplei_id = base + np.random.rand(base.shape[0]) / N_PARTICLE

            inds = []
            ind = 0
            for ip in range(N_PARTICLE):
                while (ind < wcum.shape[0] - 1) and (resamplei_id[ip] > wcum[ind]):
                    ind += 1
                inds.append(ind)

            tparticles = particles[:]
            for i in range(len(inds)):
                particles[i].x = tparticles[inds[i]].x
                particles[i].y = tparticles[inds[i]].y
                particles[i].yaw = tparticles[inds[i]].yaw
                particles[i].lm = tparticles[inds[i]].lm[:, :]
                particles[i].lmP = tparticles[inds[i]].lmP[:, :]
                particles[i].w = 1.0 / N_PARTICLE

        return particles

    # def calc_input(time):
    #     if time <= 3.0:  # wait at first
    #         v = 0.0
    #         yawrate = 0.0
    #     else:
    #         v = 1.0  # [m/s]
    #         yawrate = 0.1  # [rad/s]

    #     u = np.array([v, yawrate]).reshape(2, 1)

    #     return u

    def observation(self, xTrue, xd, u, RFID, dt):
        # calc true state
        xTrue = self.motion_model(xTrue, u, dt) 

        # add noise to range observation
        z = np.zeros((3, 0))

        for i in range(len(RFID[:, 0])):

            dx = RFID[i, 0] - xTrue[0, 0]
            dy = RFID[i, 1] - xTrue[1, 0]
            d = sqrt(dx ** 2 + dy ** 2)
            angle = pi_2_pi(atan2(dy, dx) - xTrue[2, 0])
            if d <= self.MAX_RANGE and angle >= -self.fov * 0.5 and angle <= self.fov * 0.5:
                dn = d + np.random.randn() * \
                    self.Q_sim[0, 0] ** 0.5  # add noise
                anglen = angle + np.random.randn() * \
                    self.Q_sim[1, 1] ** 0.5  # add noise
                zi = np.array([dn, pi_2_pi(anglen), i]).reshape(3, 1)
                z = np.hstack((z, zi))

        # add noise to input
        ud1 = u[0, 0] + np.random.randn() * self.R_sim[0, 0] ** 0.5
        ud2 = u[1, 0] + np.random.randn() * self.R_sim[1, 1] ** 0.5
        ud3 = u[2, 0] + np.random.randn() * self.R_sim[2, 2] ** 0.5
        ud = np.array([ud1, ud2, ud3]).reshape(3, 1)
        #print(ud)

        # Dead reckoning with noise in the input
        xd = self.motion_model(xd, ud, dt)
        #print(xd)

        return xTrue, z, xd, ud

    def motion_model(self, x, u, dt):
        # # x = [x, y, hdg, vx, vy]
        # F = np.array([[1.0, 0.0, 0.0,  dt, 0.0],
        #               [0.0, 1.0, 0.0, 0.0,  dt],
        #               [0.0, 0.0, 1.0, 0.0, 0.0],
        #               [0.0, 0.0, 0.0, 1.0, 0.0],
        #               [0.0, 0.0, 0.0, 0.0, 1.0]])
        # x = [x, y, hdg]
        F = np.array([[1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0],
                      [0.0, 0.0, 1.0]])
        # u = [vx, vy, hdg_rate]
        # cs = cos(x[2, 0])
        # sn = sin(x[2, 0])
        c = u * 1.0
        # c[0, 0] = cs * c[0] - sn * c[1]
        # c[1, 0] = sn * c[0] + cs * c[1]

        B = np.array([[ dt, 0.0, 0.0],
                      [0.0,  dt, 0.0],
                      [0.0, 0.0,  dt]])
        x = F @ x
        x += B @ c

        x[2, 0] = pi_2_pi(x[2, 0])

        return x
