"""Buffers for inter-process communication."""
''' For more info look: https://docs.python.org/3/library/multiprocessing.html '''
from multiprocessing import Pipe, RawArray, Lock

# Buffers in shared memory large enough to hold the images and the detection results
# This is a horrible hack for the sake of performance
BUF_SIZE = 16 * 1024 * 1024

image_buffer_l = RawArray('B', BUF_SIZE)            #data returned is of type 'unsigned char' with buffer size of 16x1024x1024
image_buffer_r = RawArray('B', BUF_SIZE)
result_buffer_l = RawArray('f', BUF_SIZE)           #data returned is of type 'float' with buffer size of 16x1024x1024
result_buffer_r = RawArray('f', BUF_SIZE)
coneness_buffer_l = RawArray('f', BUF_SIZE)
coneness_buffer_r = RawArray('f', BUF_SIZE)
labels_buffer_l = RawArray('B', BUF_SIZE)           #data returned is of type 'unsigned char' with buffer size of 16x1024x1024
labels_buffer_r = RawArray('B', BUF_SIZE)
vis_buffer_l = RawArray('B', BUF_SIZE)
vis_buffer_r = RawArray('B', BUF_SIZE)
image_lock = Lock()                                 #locks the thread to prevent different processes to get mixed up
result_lock = Lock()
