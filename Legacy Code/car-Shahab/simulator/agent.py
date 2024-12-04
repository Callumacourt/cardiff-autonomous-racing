# import MultiNEAT as NEAT


# class AgentNN:
#     def __init__(self, genome):
#         self.net = None
#         # try:
#         if isinstance(genome, str):
#             # We are given a filename from which to load a genome
#             genome = NEAT.Genome(genome)
#         self.net = NEAT.NeuralNetwork()
#         genome.BuildPhenotype(self.net)
#         # except:
#             # pass

#     def action(self, inputs):
#         self.net.Input(inputs)
#         self.net.Activate()
#         action = self.net.Output()
#         throttle = max(0.0, min(1.0, action[0]))
#         brakes = max(0.0, min(1.0, action[2]))
#         steer = max(-1.0, min(1.0, action[1] * 2.0 - 1.0))

#         # print("%.2f, %.2f, %.2f\t%.2f, %.2f, %.2f" %
#               # (action[0], action[1], action[2], throttle, steer, brakes))

#         return (throttle, steer, brakes)
