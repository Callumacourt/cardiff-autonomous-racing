#!env python3
import os
import sys
import argparse
import math
from concurrent.futures import ProcessPoolExecutor

from simulator import *

import MultiNEAT as NEAT
from training_params import params
from agent import AgentNN


args = None


# @profile
def eval_genome(genome):
    agent = AgentNN(genome)
    fitnesses = []

    for runs in range(args.runs):
        sim = Simulator()

        # Run the given simulation for up to num_steps time steps.
        fitness = 0.0
        while sim.t < args.time and (not sim.dead):
            speed = sim.car.absVel
            accel = math.sqrt(
                sim.car.accel[0] * sim.car.accel[0] + sim.car.accel[1] * sim.car.accel[1])
            yaw_rate = sim.car.yawRate
            bias = 1.0  # Must always provide a dummy 1.0 bias input
            inputs = sim.get_sensors() + [speed, accel, yaw_rate, bias]

            throttle, steer, brakes = agent.action(inputs)
            dt = 0.05
            sim.control(throttle, steer, brakes, dt)
            sim.advance(dt)

        fitness = sim.total_reward
        # if sim.dead:
        # fitness += -10000000
        fitnesses.append(fitness)
        # print(fitness)

    # The genome's fitness is its average performance across all runs.
    f = sum(fitnesses) / len(fitnesses)
    genome.SetFitness(f)
    return f


def main():
    global args
    parser = argparse.ArgumentParser(description='Train racing agent.')
    parser.add_argument('--load', help='Load checkpoint',
                        metavar=('CHECKPOINT'))
    # parser.add_argument('--winner', action='store_true', help='Save winner network')
    parser.add_argument('--runs', help='Runs per net',
                        default=20, action='store', type=int)
    # parser.add_argument('--gens', help='Number of generations to run',
    # default=5, action='store', type=int)
    parser.add_argument('--time', help='Simulation time (seconds)',
                        metavar=('SECONDS'), default=40, action='store', type=float)
    parser.add_argument('--workers', help='Numbe of worker processes to run',
                        default=3, action='store', type=int)
    args = parser.parse_args()

    # print(args)
    # sys.exit(0)

    if args.load is None:
        # Create the population, which is the top-level object for a NEAT run.
        genome = NEAT.Genome(0, 16 * 16 + 4, 0, 3, False,
                             NEAT.ActivationFunction.UNSIGNED_SIGMOID,
                             NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, params, 0, 1)
        pop = NEAT.Population(genome, params, True, 1.0, 0)
        generation = 0
    else:
        pop = NEAT.Population(args.load)
        with open(args.load, 'r') as f:
            lines = f.readlines()
        generation = int(lines[-1].split()[-1]) + 1


    best_genome_ever = None
    best_fitness_ever = -1e30
    while True:
        print(f'\nGENERATION: {generation}\n')

        now = time.time()

        fitness_list = []
        # genome_list = []
        # for s in pop.Species:
            # for i in s.Individuals:
                # genome_list.append(i)

        genome_list = NEAT.GetGenomeList(pop)
        print('Number of individuals:', len(genome_list))
        print('Number of species:    ', len(pop.Species))
        best_genome = None
        best_fitness = -1e30
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            for i, fitness in enumerate(executor.map(eval_genome, genome_list)):
        # for i, fitness in enumerate(map(eval_genome, genome_list)):
                fitness_list += [fitness]
                genome_list[i].SetFitness(fitness)
                # print('Individuals: (%s/%s) Fitness: %3.4f' % (i, len(genome_list), fitness))
                if fitness > best_fitness:
                    best_fitness = fitness
                    best_genome = genome_list[i]
                if fitness > best_fitness_ever:
                    best_fitness_ever = fitness
                    best_genome_ever = genome_list[i]
                    print("BEST FITNESS EVER: %.2f" % (best_fitness_ever))
                    best_genome_ever.Save('state/best_genome_ever')



        with open('state/progress.txt', 'a+') as f:
            f.write(f'{generation}')
            for fitness in fitness_list:
                f.write(f', {fitness}')
            f.write('\n')

        best_genome.Save("state/best_genome.%04d" % generation)
        pop.Save('state/population.%04d' % generation)
        with open('state/population.%04d' % generation, 'a+') as f:
            f.write('Generation %d' % generation)

        print()

        best = max([x.GetLeader().GetFitness() for x in pop.Species])
        print('Best fitness in generation %d: %.2f' % (generation, best))
        print("Best fitness ever: %.2f" % (best_fitness_ever))

        print("Evaluation took %.2f seconds" % (time.time() - now))
        print("Reproducing...")
        pop.Epoch()
        generation += 1


if __name__ == '__main__':
    main()
