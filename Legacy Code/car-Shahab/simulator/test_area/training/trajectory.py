#!env python3
import argparse
from agent import AgentNN
from simulator import Simulator
from math import sqrt

# @profile
def main():
    parser = argparse.ArgumentParser(
        description='Play racing simulation and output trajectory.')
    parser.add_argument('--agent', help='Load agent', metavar=('AGENT'))
    parser.add_argument('--track', help='Load track', metavar=('TRACK'))
    parser.add_argument('--time', help='Simulation time (seconds)',
                        metavar=('SECONDS'), default=40, action='store', type=float)

    args = parser.parse_args()

    agent = AgentNN(args.agent)
    sim = Simulator(track_fn=args.track, agent_fn=args.agent)

    print(sim.car.position[0], sim.car.position[1], sim.car.heading)

    while sim.t < args.time and (not sim.dead):
        speed = sim.car.absVel
        accel = sqrt(sim.car.accel[0] * sim.car.accel[0] + sim.car.accel[1] * sim.car.accel[1])
        yaw_rate = sim.car.yawRate
        bias = 1.0  # Must always provide a dummy 1.0 bias input
        inputs = sim.get_sensors() + [speed, accel, yaw_rate, bias]

        throttle, steer, brakes = agent.action(inputs)
        dt = 0.05
        sim.control(throttle, steer, brakes, dt)
        sim.advance(dt)
        print(sim.car.position[0], sim.car.position[1], sim.car.heading)


if __name__ == '__main__':
    main()
