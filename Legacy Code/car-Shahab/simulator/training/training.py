#!env python3
import os
import sys
import pickle
import argparse
import neat
from simulator import *
from neat.six_util import itervalues, iterkeys

# runs_per_net = 5
# simulation_seconds = 20.0

class BestReporter(neat.reporting.BaseReporter):
    def __init__(self):
        self.generation = None

    def start_generation(self, generation):
        self.generation = generation
        
    def post_evaluate(self, config, population, species, best_genome):
        print('Best fitness: {0:3.5f}'.format(best_genome.fitness))
        winner_net = neat.nn.FeedForwardNetwork.create(best_genome, config)
        with open(f'winner.net-{self.generation}', 'wb') as f:
            pickle.dump(winner_net, f)
        with open(f'winner.gen-{self.generation}', 'wb') as f:
            pickle.dump(best_genome, f)

        fitnesses = [c.fitness for c in itervalues(population)]
        with open('progress.txt', 'a+') as f:
            f.write(f'{self.generation}')
            for i in fitnesses:
                f.write(f', {i}')
            f.write('\n')

              


# @profile
def eval_genome(genome, config):
    net = neat.nn.FeedForwardNetwork.create(genome, config)

    fitnesses = []
    
    for runs in range(args.runs):
        sim = Simulator()
        
        # Run the given simulation for up to num_steps time steps.
        fitness = 0.0
        while sim.t < args.time and (not sim.dead):
            inputs = sim.get_sensors() + [sim.car.absVel]
            action = net.activate(inputs)
            # if action[0] > 0.0 or action[1] > 0.0:
                # print(action)
            
            dt = 0.05
            throttle = max(-1.0, min(1.0, action[0] * 2.0 - 1.0))
            brakes = 0
            if throttle < 0:
                throttle = 0
                brakes = -throttle
            steer = action[1] * 2.0 - 1.0
            sim.control(throttle, steer, brakes, dt)
            sim.advance(dt)
                
        fitness = sim.total_reward
        # if sim.dead:
            # fitness += -10000000
        fitnesses.append(fitness)
        # print(fitness)

    # The genome's fitness is its average performance across all runs.
    f = sum(fitnesses) / len(fitnesses)
    genome.fitness = f
    return f

def eval_genomes(genomes, config):
    best_fit = -1e10
    best_genome = None
    for genome_id, genome in genomes:
        genome.fitness = eval_genome(genome, config)
        if genome.fitness > best_fit:
            best_fit = genome.fitness
            best_genome = genome
    print('BEST: %.02f\n' % (best_fit))
    winner_net = neat.nn.FeedForwardNetwork.create(best_genome, config)
    with open('winner.net', 'wb') as f:
        pickle.dump(winner_net, f)
    with open('winner.gen', 'wb') as f:
        pickle.dump(best_genome, f)


parser = argparse.ArgumentParser(description='Train racing agent.')
parser.add_argument('--load', help='Load checkpoint', metavar=('CHECKPOINT'))
parser.add_argument('--winner', action='store_true', help='Save winner network')
parser.add_argument('--runs', help='Runs per net', default=5, action='store', type=int)
parser.add_argument('--time', help='Simulation time (seconds)', metavar=('SECONDS'), default=20, action='store', type=float)
args = parser.parse_args()

# print(args)
# sys.exit(0)

# Load configuration.
local_dir = os.path.dirname(__file__)
config_file = os.path.join(local_dir, 'config-racing')
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_file)

if args.load is None:
    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)
else:
    p = neat.Checkpointer.restore_checkpoint(args.load)

# Add a stdout reporter to show progress in the terminal.
p.add_reporter(neat.StdOutReporter(True))
stats = neat.StatisticsReporter()
p.add_reporter(stats)
p.add_reporter(neat.Checkpointer(1))
p.add_reporter(BestReporter())

if args.winner:
    winner = p.run(eval_genomes, 1)
    # winner = None
    # best_fit = -1e10
    # for idx in p.population:
    #     g = p.population[idx]
    #     print(g.fitness)
    #     if g.fitness > best_fit:
    #         best_fit = g.fitness
    #         winner = g
    # print('Best fitness: %.02f' % (best_fit))
else:
    # Run for up to 300 generations.
    pe = neat.ParallelEvaluator(2, eval_genome)
    winner = p.run(pe.evaluate, 3000)
    # winner = p.run(eval_genomes, 3000)

# Display the winning genome.
# print('\nBest genome:\n{!s}'.format(winner))

# Show output of the most fit genome against training data.
# print('\nOutput:')
winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
with open('winner.net', 'wb') as f:
    pickle.dump(winner_net, f)
