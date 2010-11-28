#!/usr/bin/env python
#
# Modified by Berlin Brown from the Numenta example

#####################################################################
# Test Run Once 
#####################################################################
# Tested with python 2.5.4

from nupic.network.helpers import  \
    AddSensor, AddClassifierNode,  \
    AddZeta1Level, TrainBasicNetwork, RunBasicNetwork

from nupic.network import CreateRuntimeNetwork, Network
from nupic.analysis import InferenceAnalysis, responses

from nupic.analysis import netexplorer
import random

#####################################################################
# Init Data 
# Possibly: 50seqs x 20time x 2
# Where num sequences per bit worm type, is each SET
#####################################################################
        
# Data generation parameters 
useCoherentData            = True       # If False, there will be no temporal
                                        # coherence in the training data
numSequencesPerBitwormType = 20         # No. of sequences for each bitworm type
sequenceLength             = 32         # No. of patterns in each temporal sequence
inputSize                  = 400        # Size of input vector
additiveNoiseTraining      = 0.0        # Range of noise added or subtracted
                                        # from training data
bitFlipProbabilityTraining = 0.0        # Prob. of switching a bit in training data
trainingMinLength          = 32         # Shortest bitworm used for training
trainingMaxLength          = 64         # Longest bitworm used for training
additiveNoiseTesting       = 0.1        # Range of noise added or subtracted
                                        # from test data
bitFlipProbabilityTesting  = 0.0        # Prob. of switching a bit in test data
testMinLength              = 30         # Shortest bitworm used for testing
testMaxLength              = 50         # Longest bitworm used for testing

# Learning parameters
maxDistance                = 0.0
topNeighbors               = 3
transitionMemory           = 4

# Various file names
untrainedNetwork   = "untrained_bitworm.xml"    # Name of the untrained network
trainedNetwork     = "trained_bitworm.xml"      # Name of the trained network
trainingFile       = "training_data.txt"        # Location of training data
trainingCategories = "training_categories.txt"  # Location of training categories
trainingResults    = "training_results.txt"     # File containing inference
                                                # results for each training pattern
testFile           = "test_data.txt"            # Location of test data
testCategories     = "test_categories.txt"      # Location of test categories
testResults        = "test_results.txt"         # File containing inference
                                                # results for each test pattern
reportFile         = "report.txt"               # File containing overall results
                                                # generated by generateReport()

#####################################################################
# Bit Worm Data
#####################################################################
class BitwormData(netexplorer.DataInterface):
      
    def __init__(self):
        """ Initialize parameters to default values."""
        netexplorer.DataInterface.__init__(self)
        self.addParam('inputSize', default=16) 
        self.addParam('numSequencesPerBitwormType', default=10)
        self.addParam('sequenceLength', default=20)
        self.addParam('minLength', default=5)
        self.addParam('maxLength', default=8)
        self.addParam('randomSeed', default=41)
        self.addParam('additiveNoise', default=0.0)
        self.addParam('bitFlipProbability', default=0.0)
        self.inputs = []
        self.categories = []  # will be 0 for solid, 1 for textured

    def createBitworm(self, wormType, pos, length, inputSize):
        input = []
        for _ in range(0, pos): input.append(self.getBit(0))
        if wormType == 'solid':
            self.categories.append(0)
            for _ in range (pos, pos+length): input.append(self.getBit(1))    
        elif wormType == 'textured':
            self.categories.append(1)
            bit = 1
            for _ in range (pos, pos+length):
                input.append(self.getBit(bit))
                bit = 1 - bit
                        
        for _ in range (pos+length, inputSize): input.append(self.getBit(0))
        self.inputs.append(input)
    
    def appendBlank(self):
        """ Append a blank vector."""
        size = self['inputSize']
        blank = []
        for _ in range(0,size): blank.append(0)
        self.inputs.append(blank)
        self.categories.append(0)
      
    def createData(self):        
        size = self['inputSize']
        random.seed(self['randomSeed'])
        for _ in range(0, self['numSequencesPerBitwormType']):
            increment = 1
            for wormType in ['solid','textured']:
                length = random.randint(self['minLength'], self['maxLength'])
                pos = random.randint(0, size-length-1)
                increment = -1*increment
                for _ in range(0, self['sequenceLength']):
                    self.createBitworm(wormType, pos, length, size)
                    if pos+length >= size:
                        increment = -1*increment
                    if pos + increment < 0: increment = -1*increment
                    pos += increment
                              
                self.appendBlank()
            
        self.writeFiles()

    def writeFiles(self):
        """ Write the generated data into files."""
        # Ensure vector data and category data have the same length
        if len(self.inputs) != len(self.categories):
            raise "Data and category vectors don't match"
        
        # write out data vectors    
        dataFile = open(self['prefix']+'data.txt', 'w')
        for input in self.inputs:
            for x in input: print >>dataFile, x,
            print >> dataFile
    
        # write out category file
        catFile = open(self['prefix']+'categories.txt', 'w')
        for c in self.categories: print >> catFile, c
        catFile.close()
        dataFile.close()        
        print len(self.inputs), "data vectors written to ",self['prefix']+'data.txt'

    def getBit(self, originalBit):
        """ Adds noise to originalBit (additive or bitFlip) and returns it."""
        bit = originalBit
        if random.uniform(0,1) < self['bitFlipProbability']: bit = 1 - bit
        bit += random.uniform(-self['additiveNoise'], self['additiveNoise'])        
        if bit==0 or bit==1: return int(bit)
        else: return bit
                
###################
# End of class
###################    

def generateBitwormData(additiveNoiseTraining = 0.0, 
                        bitFlipProbabilityTraining = 0.0,
                        additiveNoiseTesting = 0.0, 
                        bitFlipProbabilityTesting = 0.0,
                        numSequencesPerBitwormType = 10, 
                        sequenceLength = 20,
                        inputSize = 16,
                        trainingMinLength = 9, 
                        trainingMaxLength = 12,
                        testMinLength = 5, 
                        testMaxLength = 8):
    
    # Generate training data with worms of lengths between 5 and 8
    trainingData = BitwormData()
    trainingData['prefix'] = 'training_'
    trainingData['minLength'] = trainingMinLength
    trainingData['maxLength'] = trainingMaxLength
    trainingData['sequenceLength'] = sequenceLength
    trainingData['inputSize'] = inputSize
    trainingData['numSequencesPerBitwormType'] = numSequencesPerBitwormType
    trainingData['additiveNoise'] = additiveNoiseTraining
    trainingData['bitFlipProbability'] = bitFlipProbabilityTraining
    trainingData.createData()
    
    print "Training Data"
    print trainingData
    
    # Generate test data containing different worms, with lengths between 9 and 12
    testData = BitwormData()
    testData['prefix'] = 'test_'
    testData['minLength'] = testMinLength
    testData['maxLength'] = testMaxLength
    testData['sequenceLength'] = sequenceLength
    testData['inputSize'] = inputSize
    testData['numSequencesPerBitwormType'] = numSequencesPerBitwormType
    testData['randomSeed'] = trainingData['randomSeed'] + 1
    testData['additiveNoise'] = additiveNoiseTesting
    testData['bitFlipProbability'] = bitFlipProbabilityTesting
    testData.createData()
            
    print "Test Data"
    print testData
    
#####################################################################
# Run Application
#####################################################################
def runApp():
    
    print "Running Test Program"
        
    # Generate and write bitworm data into the default files train_* and test_*    
    dataParameters = generateBitwormData(
                            additiveNoiseTraining      = additiveNoiseTraining,
                            bitFlipProbabilityTraining = bitFlipProbabilityTraining,
                            additiveNoiseTesting       = additiveNoiseTesting,
                            bitFlipProbabilityTesting  = bitFlipProbabilityTesting,
                            numSequencesPerBitwormType = numSequencesPerBitwormType,
                            sequenceLength             = sequenceLength,
                            inputSize                  = inputSize,
                            trainingMinLength          = trainingMinLength,
                            trainingMaxLength          = trainingMaxLength,
                            testMinLength              = testMinLength,
                            testMaxLength              = testMaxLength)
    
    # Create the bitworm network.
    bitNet = Network()
    AddSensor(bitNet, featureVectorLength = inputSize)
    AddZeta1Level(bitNet, numNodes = 1)
    AddClassifierNode(bitNet, numCategories = 2)
    
    # Set some of the parameters we are interested in tuning
    bitNet['level1'].setParameter('topNeighbors', topNeighbors)
    bitNet['level1'].setParameter('maxDistance', maxDistance)
    bitNet['level1'].setParameter('transitionMemory', transitionMemory)
    bitNet['topNode'].setParameter('spatialPoolerAlgorithm','dot')    
    
    # Train the network
    bitNet = TrainBasicNetwork(bitNet,
                dataFiles     = [trainingFile],
                categoryFiles = [trainingCategories])
    print "Bit Net [1]: ", bitNet
    
    # Ensure the network learned the training set
    accuracy = RunBasicNetwork(bitNet,
                dataFiles     = [trainingFile],
                categoryFiles = [trainingCategories],
                resultsFile   = trainingResults)
    print "Bit Net [2]: ", bitNet
    print "Training set accuracy with HTM = ", accuracy*100.0

    # Run inference on test set to check generalization
    accuracy = RunBasicNetwork(bitNet,
                dataFiles     = [testFile],
                categoryFiles = [testCategories],
                resultsFile   = testResults)
    print "Bit Net [3]: ", bitNet
    print "Test set accuracy with HTM = ", accuracy*100.0
            
#####################################################################
# Main 
#####################################################################
if __name__ == '__main__':
    runApp()
    print "Done!"

###################
# End of File
###################

    