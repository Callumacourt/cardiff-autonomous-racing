from threading import Thread
import math
import time
import wx
import cv2
from image_folder import ImageFolder
# from camera import Camera
from log import log
from timer import Timer
from config import config
import numpy as np
from scipy import stats, optimize
import detector_process
from simulator_camera import SimulatorCamera
from ap import analyse_cc, max_argmax
# import matplotlib as plt
import matplotlib.pyplot as plt
from stereo_pair import StereoPair, project_point
from car import Car
from mppi import MPPI
from control import Controller
from ipc import *
from math import sin, cos
from geometry import delaunay, transverse_edges, track_boundaries, poly_dist
from mppi import MPPI
import pycuda.driver as cuda
from pycuda.tools import make_default_context, clear_context_caches
from pycuda.compiler import SourceModule
from airsim.utils import to_eularian_angles

# TODO: Move to config
THR_SOFT = 0.5
THR_HARD = 0.8

# Cone labels
CONE_YELLOW = 0
CONE_BLUE = 1
CONE_RED = 2

NO_MATCH_COST = 10000


def cone_colour(label):
    if label == CONE_YELLOW:
        return (200, 200, 0)
    if label == CONE_BLUE:
        return (96, 96, 255)
    if label == CONE_RED:
        return (255, 0, 0)


# @profile
def cone_centroids(lab, soft):
    lab = lab.copy()  # TODO: Investigate why this is needed. Race condition?
    n_cc, cc_labels = cv2.connectedComponents(lab)
    cones = np.zeros((5, n_cc - 1), dtype=np.float32)

    analyse_cc(cc_labels, lab, soft, cones)
    cones[0, :] = cones[0, :] / cones[3, :]
    cones[1, :] = cones[1, :] / cones[3, :]
    # TODO: Merge nerby connected components
    # Delete those where no pixels are above the THR_HARD
    cones = cones[:, cones[4, :] > 0]
    return cones


class AutopilotThread(Thread):
    def __init__(self, subscriber, conn, sim):
        Thread.__init__(self)

        cuda.init()
        self.context = make_default_context()
        self.device = self.context.get_device()

        self.sim = sim
        # self.video = ImageFolder('../../car_data/cones/amz', image_buffer)
        self.stereo = StereoPair()
        # self.video = ImageFolder(
        #     '../../car_data/test_days/2019-12-11/recording0_flipped/',
        #     image_buffer_l, image_buffer_r, self.stereo, start=1000)
        # self.video = ImageFolder('sim_camera', self.stereo)
        self.video = SimulatorCamera(
            self.sim, image_buffer_l, image_buffer_r, image_lock)
        self.controller = Controller(self.sim)
        self.car = Car()
        self.mppi = MPPI(context=self.context)
        self.centreline = np.zeros((0, 2))
        # self.video = ImageFolder('../../../car_data/cones/ka-raceing-240919/every10')
        # self.video = ImageFolder('../../../car_data/cones/office.261019')
        # self.video = ImageFolder('../../../car_data/local/fs2019_track1_fixed')
        # self.video = ImageFolder('../fsuk 2019 recordings/track1')
        # self.video = ImageFolder('../../data/recording.2310191746')
        # self.video = ImageFolder('../../data/local/recording')
        # self.video = ImageFolder('../../data/cones/single_lap')
        # log('Found %d image files.' % (self.video.N))

        # self.video = Camera(0, image_buffer)

        self.conn = conn
        self.im_result = None

        self.subscriber = subscriber
        self.abort_requested = False
        self.FPS = 0
        self.paused = True

        self.kbd_throttle = 0.0
        self.kbd_steering = 0.0

        self.car_X_prev = None
        self.car_theta_prev = None
        self.plan_all_prev = None

        self.last_timestamp = None
        # self.last_hdg = 0
        # self.last_hdgv = 0

    def play(self):
        self.paused = False
        self.video.play()

    def pause(self):
        self.paused = True
        self.video.pause()

    def notify(self):
        try:
            wx.CallAfter(self.subscriber)
        except:
            log('Detector thread: Cannot notify subscriber.')

    def set_kbd_control(self, steering, throttle):
        # print('Throttle', throttle, 'Steering', steering)
        self.kbd_steering = steering
        self.kbd_throttle = throttle

    def draw_cone_centroids(self, cones_l, cones_r):
        w = self.video.image_l.shape[1]
        for i in range(cones_l.shape[1]):
            cv2.circle(self.im_result,
                       (int(round(cones_l[0, i])), int(round(cones_l[1, i]))),
                       int(round(math.sqrt(cones_l[3, i]))), cone_colour(cones_l[2, i]), 2)
        for i in range(cones_r.shape[1]):
            cv2.circle(self.im_result,
                       (int(round(cones_r[0, i])) +
                        w, int(round(cones_r[1, i]))),
                       int(round(math.sqrt(cones_r[3, i]))), cone_colour(cones_r[2, i]), 2)

    def draw_track_boundary(self, lines, colour):
        w = self.video.image_l.shape[1]
        for line in lines:
            S = np.array([line[0][0] * 1000.0 + 600.0,
                          2000.0, line[0][1] * 1000.0, 1]).T
            E = np.array([line[1][0] * 1000.0 + 600.0,
                          2000.0, line[1][1] * 1000.0, 1]).T
            s_l = project_point(self.stereo.P1, S)
            e_l = project_point(self.stereo.P1, E)
            s_r = project_point(self.stereo.P2, S)
            e_r = project_point(self.stereo.P2, E)
            cv2.line(self.im_result,
                     (int(round(s_l[0])), int(round(s_l[1]))),
                     (int(round(e_l[0])), int(round(e_l[1]))),
                     colour, 2, cv2.LINE_AA)
            cv2.line(self.im_result,
                     (int(round(s_r[0])) + w, int(round(s_r[1]))),
                     (int(round(e_r[0])) + w, int(round(e_r[1]))),
                     colour, 1, cv2.LINE_AA)

    def draw_track_boundaries(self, lines_y, lines_b):
        self.draw_track_boundary(lines_y, (255, 255, 0))
        self.draw_track_boundary(lines_b, (96, 96, 255))

    # @profile
    def match_cones(self, cones_l, cones_r):
        assignment_cost = np.zeros((cones_l.shape[1], cones_r.shape[1]))
        W = np.zeros((cones_l.shape[1], cones_r.shape[1], 3))
        for i in range(cones_l.shape[1]):
            for j in range(cones_r.shape[1]):
                p3d, err = self.stereo.triangulate(
                    cones_l[0:2, i], cones_r[0:2, j])
                err = np.max(err)
                W[i, j, :] = p3d.flatten()

                height = 1840.0 - W[i, j, 1]
                # c = np.hstack((p3d.flatten(), [1.0])).T
                # gr = self.stereo.CtoG @ c
                # gr = gr / gr[3]
                # height = gr[2]
                if err > 5.0 or p3d[2] < 0.0 or cones_l[2, i] != cones_r[2, j] or abs(height) > 500.0:
                    assignment_cost[i, j] = NO_MATCH_COST
                else:
                    assignment_cost[i, j] = err + abs(height) * 0.05

        row, col = optimize.linear_sum_assignment(assignment_cost)
        cost = assignment_cost[row, col]
        valid = cost < NO_MATCH_COST
        row = row[valid]
        col = col[valid]
        cost = cost[valid]
        return row, col, cost, W

    def predict_trajectory(self, X0):
        X = X0.copy()
        horz = 60
        traj = np.zeros((horz, 2))
        traj[0, :] = X[0:2]
        cmd_ctr = self.sim.client.getCarControls()
        control = np.array([cmd_ctr.steering, cmd_ctr.throttle])
        dt = 0.050
        for t in range(horz):
            X = self.car.advance(X, control, dt)
            traj[t, 0] = X[1]
            traj[t, 1] = X[0]
        return traj

    def plot_trajectory(self, traj):
        for t in range(traj.shape[0] - 1):
            ts = np.array([traj[t, 0] * 1000.0 + 600.0,
                           2000, traj[t, 1] * 1000.0, 1.0])
            te = np.array([traj[t + 1, 0] * 1000.0 + 600.0,
                           2000, traj[t + 1, 1] * 1000.0, 1.0])
            if (ts[2] < 1000.0) or (te[2] < 1000.0):
                continue

            ts_l = project_point(self.stereo.P1, ts)
            te_l = project_point(self.stereo.P1, te)
            try:
                x0 = int(round(ts_l[0]))
                x1 = int(round(te_l[0]))
                y0 = int(round(ts_l[1]))
                y1 = int(round(te_l[1]))
                if x0 < 0 or y0 < 0 or x1 >= w or y1 >= h:  # TODO: Get actual image size
                    continue
                cv2.line(self.im_result, (x0, y0), (x1, y1),
                         (255, 255, 255), 2, cv2.LINE_AA)
            except:
                pass
                # print(ts_l, te_l)


    @profile
    def localise_cones(self):
        h = self.video.image_l.shape[0]
        w = self.video.image_l.shape[1]

        self.labels_l = np.frombuffer(labels_buffer_l,
                                      dtype=np.uint8, count=h * w).reshape((h, w))
        self.labels_r = np.frombuffer(labels_buffer_r,
                                      dtype=np.uint8, count=h * w).reshape((h, w))
        self.coneness_l = np.frombuffer(coneness_buffer_l,
                                        dtype=np.float32, count=h * w).reshape((h, w))
        self.coneness_r = np.frombuffer(coneness_buffer_r,
                                        dtype=np.float32, count=h * w).reshape((h, w))

        # This is what will be displayed
        vis_l = np.frombuffer(vis_buffer_l,
                              dtype=np.uint8, count=h * w * 3).reshape((h, w, 3))
        vis_r = np.frombuffer(vis_buffer_r,
                              dtype=np.uint8, count=h * w * 3).reshape((h, w, 3))
        self.im_result = np.concatenate((vis_l, vis_r), axis=1)

        cones_l = cone_centroids(self.labels_l, self.coneness_l)
        cones_r = cone_centroids(self.labels_r, self.coneness_r)
        row, col, cost, W = self.match_cones(cones_l, cones_r)

        w = self.video.image_l.shape[1]
        h = self.video.image_l.shape[0]
        for i in range(len(cost)):
            cv2.line(self.im_result,
                     (int(round(cones_l[0, row[i]])),
                      int(round(cones_l[1, row[i]]))),
                     (int(round(cones_r[0, col[i]])) +
                      w, int(round(cones_r[1, col[i]]))),
                     (255, 128, 25), 1, cv2.LINE_AA)
            cv2.putText(self.im_result,
                        f"{W[row[i], col[i], 0] * 0.001:.2f} {2.0 - W[row[i], col[i], 1] * 0.001:.2f} {W[row[i], col[i], 2] * 0.001:.2f}",
                        (int(round(cones_l[0, row[i]])) - 64,
                         int(round(cones_l[1, row[i]])) - 16),
                        cv2.FONT_HERSHEY_PLAIN,
                        1.3, (255, 255, 255), 1,
                        cv2.LINE_AA)

        idx_y = np.where(cones_l[2, row] == 0)[0]
        idx_b = np.where(cones_l[2, row] == 1)[0]

        # Convert to meters and shift to centre
        self.plan_y = W[row, col][:, [0, 2]][idx_y, :] * 0.001
        self.plan_y[:, 0] -= 0.6
        self.plan_b = W[row, col][:, [0, 2]][idx_b, :] * 0.001
        self.plan_b[:, 0] -= 0.6
        self.plan_all = np.concatenate((self.plan_y, self.plan_b), axis=0)
        labels = np.concatenate((np.zeros((self.plan_y.shape[0]), dtype=np.int32),
                                 np.zeros((self.plan_b.shape[0]), dtype=np.int32) + 1))


        self.triangulation = delaunay(self.plan_all)

        self.ctr = np.zeros((0, 2))
        self.ctr_i = np.zeros((0, 2))
        MAX_DIST = 10.0

        self.lines_y = []
        self.lines_b = []
        
        xx, yy = np.meshgrid(np.linspace(-10, 10, 41), np.linspace(0, 20, 41))
        self.Xgrid = np.vstack((xx.flatten(), yy.flatten())).T
        self.V = np.zeros(shape=self.Xgrid.shape)


        if self.triangulation.shape[0] > 0:
            transverse = transverse_edges(
                self.plan_all, labels, self.triangulation, max_dist=MAX_DIST)

            # Determine the centre line as the sequence of midpoints of the transverse edges
            self.ctr = np.zeros((len(transverse), 2))
            for i, e in enumerate(transverse):
                self.ctr[i, :] = (self.plan_all[e[0], :] + self.plan_all[e[1], :]) * 0.5


            try:
                # PCA on ctr
                avg = np.reshape(np.mean(self.ctr, axis=0), (1, 2))
                ctr_0 = self.ctr - avg
                covar = ctr_0.T @ ctr_0;
                # print(covar)
                evec, sigma, Vt = np.linalg.svd(covar, compute_uv=True)
                # print('V', evec)
                # print('sigma', sigma)
                ctr_proj = evec.T @ ctr_0.T
                # print(ctr_proj.shape)
                mi = np.min(ctr_proj, axis=1)
                ma = np.max(ctr_proj, axis=1)
                # print(mi, ma)
                poly = np.poly1d(np.polyfit(ctr_proj[0, :], ctr_proj[1, :], 2))
                # print(poly)
                x = np.linspace(mi[0] - 10.0, ma[0] + 10.0, 21)
                # print(x.shape)
                ctr_i_proj = np.vstack((x, poly(x)))
                # print(ctr_i_proj)
                self.ctr_i = (evec @ ctr_i_proj + avg.T).T
                # # print(ctr_i)

                # Compute direction/distance field
                X0 = (evec.T @ (self.Xgrid - avg).T).T
                D, self.V, Ds = poly_dist(ctr_i_proj.T, X0)
                self.V = (evec @ self.V.T).T


                            # dist = np.sqrt(np.sum(ctr * ctr, axis=1))
            # order = np.argsort(dist)
            # ctr = ctr[order, :]
            # dist = dist[order]
            # angle = np.zeros(len(dist))
            # for i in range(len(dist)):
            #     angle[i] = math.atan2(ctr[i, 0], ctr[i, 1])

            # try:
            #     poly = np.poly1d(np.polyfit(dist, angle, 1))
            #     # print(poly)
            # except TypeError:
            #     poly = np.poly1d(np.array([0, 0]))
            # dist_i = np.linspace(3.0, 20.0, 10)
            # angle_i = poly(dist_i)
            # ctr_i = np.vstack(
            #     (dist_i * np.sin(angle_i), dist_i * np.cos(angle_i))).T


                vn = np.sqrt(np.sum(np.square(self.V), axis=1))
                vn = np.reshape(vn, (len(vn), 1))
                self.V = self.V * 1
                # self.V = self.V * np.exp(-vn * 0.5) * 10
                self.V = np.vstack((-self.V[:, 1], self.V[:, 0])).T

                # Global orientation
                # a = (self.plan_y - avg)
                # print(a.shape)
                cyt = (evec.T @ (self.plan_y - avg).T).T
                Dy, Vy, Dsy = poly_dist(ctr_i_proj.T, cyt)

                Dsy = np.mean(Dsy)
                neg = np.where(np.sign(Ds) * np.sign(Dsy) < 0)
                self.V[neg, :] = -self.V[neg, :]
            except:
                self.ctr_i = np.zeros((0, 2))

            self.centreline = self.ctr_i



            self.lines_y, self.lines_b = track_boundaries(
                self.plan_all, labels, self.triangulation)
        # print(self.plan_y)
        # if len(ctr_i) > 0:
        #     # dist_y = np.sqrt(np.sum(self.plan_y * self.plan_y, axis=1))
        #     # nearest_y = self.plan_y[np.argmin(dist_y), :]
        #     # dist_b = np.sqrt(np.sum(self.plan_b * self.plan_b, axis=1))
        #     # nearest_b = self.plan_b[np.argmin(dist_b), :]
        #     # self.target = (nearest_y + nearest_b) * 0.5
        #     self.target = ctr_i[0, :]
        # else:
        #     self.target = np.array([0, 0])

        # print(self.target)

        # Predict motion
        X0 = self.sim.state_vector_c()
        traj = self.predict_trajectory(X0)
        self.plot_trajectory(traj)

        
        
        self.draw_track_boundaries(self.lines_y, self.lines_b)
        self.draw_cone_centroids(cones_l, cones_r)


        # Save to file
        # with open('cones.txt', 'a') as file:
        #     file.write(" ".join([f"0 {self.plan_y[i, 0]} {self.plan_y[i, 1]}" for i in range(self.plan_y.shape[0])] +
        #                         [f"1 {self.plan_b[i, 0]} {self.plan_b[i, 1]}" for i in range(self.plan_b.shape[0])]))
        #     file.write("\n")
        
        #
        # Draw projections in im_result
        #
        # print(self.ctr_i.shape)
        for i in range(self.ctr_i.shape[0] - 1):
            if self.ctr_i[i, 1] < 2.0:
                continue
            A_l = np.array([self.ctr_i[i, 0] * 1000.0 + 600.0,
                            2000.0, self.ctr_i[i, 1] * 1000.0, 1.0])
            B_l = np.array([self.ctr_i[i + 1, 0] * 1000.0 + 600.0,
                            2000.0, self.ctr_i[i + 1, 1] * 1000.0, 1.0])
            A_r = np.array([self.ctr_i[i, 0] * 1000.0 + 600.0,
                            2000.0, self.ctr_i[i, 1] * 1000.0, 1.0])
            B_r = np.array([self.ctr_i[i + 1, 0] * 1000.0 + 600.0,
                            2000.0, self.ctr_i[i + 1, 1] * 1000.0, 1.0])
            # print(A)
            a_l = project_point(self.stereo.P1, A_l)
            b_l = project_point(self.stereo.P1, B_l)
            a_r = project_point(self.stereo.P2, A_r)
            b_r = project_point(self.stereo.P2, B_r)
            cv2.line(self.im_result,
                     (int(round(a_l[0])), int(round(a_l[1]))),
                     (int(round(b_l[0])), int(round(b_l[1]))),
                     (64, 255, 64), 2, cv2.LINE_AA)
            cv2.line(self.im_result,
                     (int(round(a_r[0])) + w, int(round(a_r[1]))),
                     (int(round(b_r[0])) + w, int(round(b_r[1]))),
                     (64, 255, 64), 1, cv2.LINE_AA)

    @profile
    def run(self):
        self.frame = 0
        t = time.time()
        while True:
            if self.abort_requested:
                return

            if self.paused:
                if self.video.image_l is None:
                    self.video.get()
                time.sleep(0.1)
                continue

            if config.CD_ENABLE and (self.video.image_l is not None):
                self.conn.send((detector_process.CMD_DETECT,
                                {'height': self.video.image_l.shape[0],
                                 'width': self.video.image_l.shape[1]}))
                # self.result_lock.acquire()
                self.localise_cones()
                # self.sim.client.enableApiControl(True)
                # self.controller.control(
                #     dt, self.kbd_steering, self.kbd_throttle, self.plan_y, self.plan_b, self.target)
                # self.sim.client.enableApiControl(False)


                kin = self.controller.sim.client.simGetGroundTruthKinematics()
                ctr = self.controller.sim.client.getCarControls()
                st = self.controller.sim.client.getCarState()
                # Kinematics
                # kin = sim.client.getImuData()
                x = kin.position.x_val
                y = kin.position.y_val
                # wx = kin.angular_velocity.x_val
                # wy = kin.angular_velocity.y_val 
                vhdg = kin.angular_velocity.z_val
                ahdg = kin.angular_acceleration.z_val
                vx = kin.linear_velocity.x_val
                vy = kin.linear_velocity.y_val
                ax = kin.linear_acceleration.x_val
                ay = kin.linear_acceleration.y_val
                # az = kin.linear_acceleration.z_val
                # vz = kin.linear_velocity.z_val
                q = kin.orientation
                _, _, hdg = to_eularian_angles(q)

                tst = st.timestamp / 1000000000.0
                # print(tst)
                if self.last_timestamp is None:
                    DT = 0.067
                else:
                    DT = tst - self.last_timestamp

                self.last_timestamp = tst
                X = np.array([x, y, vx, vy, ax, ay, hdg, vhdg, ahdg], dtype=np.float32)
                steering, throttle = self.mppi.advance(X, np.array([ctr.steering, ctr.throttle]), self.centreline,
                                                       self.Xgrid, self.V, dt=0.05)
                # print(steering.shape, throttle.shape)
                # throttle = 1

                # traj_best = np.hstack((self.mppi.traj_best[:, 0:2], np.ones((self.mppi.traj_best.shape[0], 1))))
                traj_all = np.hstack((self.mppi.traj_all[:, 0:2], np.ones((self.mppi.traj_all.shape[0], 1))))
                
                T = np.array([[cos(hdg), -sin(hdg), x], [sin(hdg), cos(hdg), y], [0.0, 0.0, 1.0]])
                T = np.linalg.inv(T)
                # print(T.shape, traj_best.shape)
                # traj_best_c = (T @ traj_best.T).T
                traj_all_c = (T @ traj_all.T).T
                # traj_best_c = traj_best
                # print(traj_all_c.shape)

                wx.GetApp().frame.plan_view.draw(self.plan_y, self.plan_b, self.plan_all,
                                         self.triangulation, self.ctr, self.ctr_i, self.lines_y, self.lines_b, self.Xgrid, self.V,
                                                 None, traj_all_c, self.frame)
                
                

                if abs(self.kbd_steering) > 0:
                    steering += self.kbd_steering * 0.05
                if abs(self.kbd_throttle) > 0:
                    throttle += self.kbd_throttle * 0.025

                throttle = max(0.0, min(1.0, throttle))
                steering = max(-1.0, min(1.0, steering))
                self.controller.sim.control(steering, throttle, 0.0)
                
                # ctr = self.controller.sim.client.getCarControls()
                # print(ctr)

                dt = time.time() - t
                t = time.time()
                n = 10
                self.FPS = self.FPS * (n - 1) / n + 1 / (dt * n)

                self.notify()
                self.video.get()
                # self.result_lock.release()
                self.conn.recv()  # Blocking

            else:
                self.video.get()
            self.frame += 1

    def abort(self):
        log('Autopilot thread: Cleaning up CUDA.\n')
        self.context.pop()
        self.context = None
        clear_context_caches()

        try:
            self.sim.disconnect()
        finally:
            self.abort_requested = True


        # print(self.sim.client.getCarState())
        # kin = self.sim.client.simGetGroundTruthKinematics()
        # pos = kin.position
        # q = kin.orientation
        # car_X = np.array([[pos.x_val, pos.y_val]])
        # # print(car_X)
        # car_theta = quaternion_to_euler(np.array([q.w_val, q.x_val, q.y_val, q.z_val]))[2]

        # # Estimate rotation and translation compared to the previous frame
        # if self.car_X_prev is not None:
        #     T = car_X - self.car_X_prev
        #     d_theta = car_theta - self.car_theta_prev
        # else:
        #     T = np.array([[0, 0]])
        #     d_theta = 0.0

        # d_theta = -d_theta
        # # T = -T
        # R = np.array([[math.cos(d_theta), -math.sin(d_theta)], [math.sin(d_theta), math.cos(d_theta)]])
        # self.car_X_prev = car_X
        # self.car_theta_prev = car_theta

        # tform_T = np.vstack((np.hstack((np.eye(2), T.T)), np.array([[0, 0, 1]])))
        # print(tform_T)
        # tform_R = np.vstack((np.hstack((R, np.zeros((2, 1)))), np.array([[0, 0, 1]])))
        # print(tform_R)
        # tform = tform_R @ tform_R @ tform_T
        # print(tform)
        # tform_inv = np.linalg.inv(tform)
        # # print(tform_inv)

        # if self.plan_all_prev is not None:
        #     plan_prev = (tform_inv @ np.vstack((self.plan_all_prev.T, np.ones((1, self.plan_all_prev.shape[0])))))[0:2, :].T
        #     # plan_prev = (R @ (self.plan_all_prev.T - T.T) + T.T).T
        #     self.plan_all_prev = np.vstack((plan_all, plan_prev))
        # else:
        #     plan_prev = plan_all#np.zeros((0, 2))
        #     self.plan_all_prev = plan_prev
        # # print(self.plan_all_prev)

        # print(plan_all)
        # print(labels)
