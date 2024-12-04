# Padding around bounding boxes used when training
# and that needs to be correspondingly removed after detection.
BBOX_PADDING = 6

# From which folder to load the images.
DATA_PREFIX = '../../../car_data/cones'

# Extension for the files containing annotations.
LABELS_EXT = '.txt'

# In which colour to draw the bounding boxes.
LABEL_COLOURS = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]

# In which colour to draw the bounding boxes when they are selected.
LABEL_COLOURS_SELECTED = [[1.0, 1.0, 1.0], [1.0, 1.0, 0.5], [0.5, 0.5, 1.0], [0.5, 1.0, 0.5], [1.0, 0.5, 0.5]]

# File name of the cascade detector model.
DETECTOR_FN = '../cone_detector.xml'
