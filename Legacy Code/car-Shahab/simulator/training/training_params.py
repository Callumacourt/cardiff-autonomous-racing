import MultiNEAT as NEAT

params = NEAT.Parameters()

#
# BASIC PARAMETERS
#

# Size of population
params.PopulationSize = 300

# If true, this enables dynamic compatibility thresholding
# It will keep the number of species between MinSpecies and MaxSpecies
params.DynamicCompatibility = True

# Minimum number of species
params.MinSpecies = 2

# Maximum number of species
params.MaxSpecies = 10

# Don't wipe the innovation database each generation?
params.InnovationsForever = True

#
# GA PARAMETERS
#

# Age treshold, meaning if a species is below it, it is considered young
params.YoungAgeTreshold = 15

# Fitness boost multiplier for young species (1.0 means no boost)
# Make sure it is > 1.0 to avoid confusion
params.YoungAgeFitnessBoost = 1.1

# Number of generations without improvement (stagnation) allowed for a species
params.SpeciesDropoffAge = 50

# Minimum jump in fitness necessary to be considered as improvement.
# Setting this value to 0.0 makes the system to behave like regular NEAT.
params.StagnationDelta = 0.0

# AgeGens threshold, meaning if a species is above it, it is considered old
params.OldAgeTreshold = 35

# Multiplier that penalizes old species.
# Make sure it is < 1.0 to avoid confusion.
params.OldAgePenalty = 1.0

# Detect competetive coevolution stagnation
# This kills the worst species of age >N (each X generations)
params.DetectCompetetiveCoevolutionStagnation = False

# Each X generation...
params.KillWorstSpeciesEach = 15

# Of age above...
params.KillWorstAge = 10

# Percent of best individuals that are allowed to reproduce. 1.0 = 100%
params.SurvivalRate = 0.25

# Probability for a baby to result from sexual reproduction (crossover/mating). 1.0 = 100%
# If asexual reprodiction is chosen, the baby will be mutated 100%
params.CrossoverRate = 0.75

# If a baby results from sexual reproduction, this probability determines if mutation will
# be performed after crossover. 1.0 = 100% (always mutate after crossover)
params.OverallMutationRate = 0.25

# Probability for a baby to result from inter-species mating.
params.InterspeciesCrossoverRate = 0.0001

# Probability for a baby to result from Multipoint Crossover when mating. 1.0 = 100%
# The default is the Average mating.
params.MultipointCrossoverRate = 0.75

# Performing roulette wheel selection or not?
params.RouletteWheelSelection = False

#
# PHASED SEARCH PARAMETERS
#

# Using phased search or not
params.PhasedSearching = False

# Using delta coding or not
params.DeltaCoding = False

# What is the MPC + base MPC needed to begin simplifying phase
params.SimplifyingPhaseMPCTreshold = 20

# How many generations of global stagnation should have passed to enter simplifying phase
params.SimplifyingPhaseStagnationTreshold = 30

# How many generations of MPC stagnation are needed to turn back on complexifying
params.ComplexityFloorGenerations = 40

#
# NOVELTY SEARCH PARAMETERS
#

# the K constant
params.NoveltySearch_K = 15

# Sparseness treshold. Add to the archive if above
params.NoveltySearch_P_min = 0.5

# Dynamic Pmin?
params.NoveltySearch_Dynamic_Pmin = True

# How many evaluations should pass without adding to the archive
# in order to lower Pmin
params.NoveltySearch_No_Archiving_Stagnation_Treshold = 150

# How should it be multiplied (make it less than 1.0)
params.NoveltySearch_Pmin_lowering_multiplier = 0.9

# Not lower than this value
params.NoveltySearch_Pmin_min = 0.05

# How many one-after-another additions to the archive should
# pass in order to raise Pmin
params.NoveltySearch_Quick_Archiving_Min_Evaluations = 8

# How should it be multiplied (make it more than 1.0)
params.NoveltySearch_Pmin_raising_multiplier = 1.1

# Per how many evaluations to recompute the sparseness of the population
params.NoveltySearch_Recompute_Sparseness_Each = 25

#
# STRUCTURAL MUTATION PARAMETERS
#

# Probability for a baby to be mutated with the Add-Neuron mutation.
params.MutateAddNeuronProb = 0.1

# Allow splitting of any recurrent links
params.SplitRecurrent = True

# Allow splitting of looped recurrent links
params.SplitLoopedRecurrent = True

# Probability for a baby to be mutated with the Add-Link mutation
params.MutateAddLinkProb = 0.07

# Probability for a new incoming link to be from the bias neuron
# This enforces it. A value of 0.0 doesn't mean there will not be such links
params.MutateAddLinkFromBiasProb = 0.0

# Probability for a baby to be mutated with the Remove-Link mutation
params.MutateRemLinkProb = 0.01

# Probability for a baby that a simple neuron will be replaced with a link
params.MutateRemSimpleNeuronProb = 0.0

# Maximum number of tries to find 2 neurons to add/remove a link
params.LinkTries = 128

# Probability that a link mutation will be made recurrent
params.RecurrentProb = 0.25

# Probability that a recurrent link mutation will be looped
params.RecurrentLoopProb = 0.25

#
# MUTATION PARAMETERS
#

# Probability for a baby's weights to be mutated
params.MutateWeightsProb = 0.75

# Probability for a severe (shaking) weight mutation
params.MutateWeightsSevereProb = 0.25

# Probability for a particular gene's weight to be mutated. 1.0 = 100%
params.WeightMutationRate = 1.0

# ??? Probability for a particular gene's weight to be replaced. 1.0 = 100%
params.WeightReplacementRate = 0.25

# Maximum perturbation for a weight mutation
params.WeightMutationMaxPower = 1.0

# Maximum magnitude of a replaced weight
params.WeightReplacementMaxPower = 1.0

# Maximum absolute magnitude of a weight
params.MaxWeight = 8

# Probability for a baby's A activation function parameters to be perturbed
params.MutateActivationAProb = 0.0

# Probability for a baby's B activation function parameters to be perturbed
params.MutateActivationBProb = 0.0

# Maximum magnitude for the A parameter perturbation
params.ActivationAMutationMaxPower = 0.0

# Maximum magnitude for the B parameter perturbation
params.ActivationBMutationMaxPower = 0.0

# Activation parameter A min/max
params.MinActivationA = 1.0
params.MaxActivationA = 1.0

# Activation parameter B min/max
params.MinActivationB = 0.0
params.MaxActivationB = 0.0

# Maximum magnitude for time costants perturbation
params.TimeConstantMutationMaxPower = 0.0

# Maximum magnitude for biases perturbation
params.BiasMutationMaxPower = params.WeightMutationMaxPower

# Probability for a baby's neuron time constant values to be mutated
params.MutateNeuronTimeConstantsProb = 0.0

# Probability for a baby's neuron bias values to be mutated
params.MutateNeuronBiasesProb = 0.0

# Time constant range
params.MinNeuronTimeConstant = 0.0
params.MaxNeuronTimeConstant = 0.0

# Bias range
params.MinNeuronBias = 0.0
params.MaxNeuronBias = 0.0

# Probability for a baby that an activation function type will be changed for a single neuron
# considered a structural mutation because of the large impact on fitness
params.MutateNeuronActivationTypeProb = 0.1

# Probabilities for a particular activation function appearance
params.ActivationFunction_SignedSigmoid_Prob = 1.0
params.ActivationFunction_UnsignedSigmoid_Prob = 1.0
params.ActivationFunction_Tanh_Prob = 1.0
params.ActivationFunction_TanhCubic_Prob = 0.0
params.ActivationFunction_SignedStep_Prob = 0.0
params.ActivationFunction_UnsignedStep_Prob = 0.0
params.ActivationFunction_SignedGauss_Prob = 1.0
params.ActivationFunction_UnsignedGauss_Prob = 1.0
params.ActivationFunction_Abs_Prob = 0.0
params.ActivationFunction_SignedSine_Prob = 0.0
params.ActivationFunction_UnsignedSine_Prob = 0.0
params.ActivationFunction_SignedSquare_Prob = 0.0
params.ActivationFunction_UnsignedSquare_Prob = 0.0
params.ActivationFunction_Linear_Prob = 1.0

#
# SPECIATION PARAMETERS
#

# Percent of disjoint genes importance
params.DisjointCoeff = 1.0

# Percent of excess genes importance
params.ExcessCoeff = 1.0

# Average weight difference importance
params.WeightDiffCoeff = 1.5

# Node-specific activation parameter A difference importance
params.ActivationADiffCoeff = 0.0

# Node-specific activation parameter B difference importance
params.ActivationBDiffCoeff = 0.0

# Average time constant difference importance
params.TimeConstantDiffCoeff = 0.0

# Average bias difference importance
params.BiasDiffCoeff = 0.0

# Activation function type difference importance
params.ActivationFunctionDiffCoeff = 0.0

# Compatibility treshold
params.CompatTreshold = 5.0

# Minumal value of the compatibility treshold
params.MinCompatTreshold = 0.2

# Modifier per generation for keeping the species stable
params.CompatTresholdModifier = 0.2

# Per how many generations to change the treshold
# (used in generational mode)
params.CompatTreshChangeInterval_Generations = 1

# Per how many evaluations to change the treshold
# (used in steady state mode)
params.CompatTreshChangeInterval_Evaluations = 10

# ???
params.NormalizeGenomeSize = True
params.SpeciesMaxStagnation = 15

params.ArchiveEnforcement = False

params.MutateNeuronTraitsProb = 0.01
params.MutateLinkTraitsProb = 0.01

params.AllowLoops = True
params.AllowClones = True
