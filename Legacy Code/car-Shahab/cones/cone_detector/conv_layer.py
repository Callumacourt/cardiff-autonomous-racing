from pycuda import gpuarray
import libcudnn
import numpy as np
import wx
from log import log

tensor_format = libcudnn.cudnnTensorFormat['CUDNN_TENSOR_NCHW']
data_type = libcudnn.cudnnDataType['CUDNN_DATA_FLOAT']
convolution_mode = libcudnn.cudnnConvolutionMode['CUDNN_CROSS_CORRELATION']

class ConvLayer:
    def __init__(self, filters, biases, relu=True, softmax=False):
        # Filter tensor
        self.filters = gpuarray.to_gpu(filters.astype(np.float32))
        self.biases = gpuarray.to_gpu(biases.astype(np.float32))
        self.biases_desc = libcudnn.cudnnCreateTensorDescriptor()

        # print(filters.shape)
        # self.biases = gpuarray.to_gpu(biases).astype(np.float32)
        self.relu = relu
        self.softmax = softmax

        # Filter descriptor
        self.filters_desc = libcudnn.cudnnCreateFilterDescriptor()
        libcudnn.cudnnSetFilter4dDescriptor(self.filters_desc, data_type, tensor_format,
                                            filters.shape[0], filters.shape[1], filters.shape[2], filters.shape[3])
        # Convolution descriptor
        self.conv_desc = libcudnn.cudnnCreateConvolutionDescriptor()
        pad_h = 0#filters.shape[2] // 2
        pad_w = 0#filters.shape[3] // 2
        libcudnn.cudnnSetConvolution2dDescriptor(self.conv_desc, pad_h, pad_w,
                                                 1, 1, 1, 1, convolution_mode, data_type)

        # Biases descriptor
        libcudnn.cudnnSetTensor4dDescriptor(
            self.biases_desc, tensor_format, data_type, self.biases.shape[0], self.biases.shape[1], self.biases.shape[2], self.biases.shape[3])

        # print('Filters: ' + str(self.filters.shape))

    def channels_in(self):
        return self.filters.shape[1]

    def channels_out(self):
        return self.filters.shape[0]

    def __del__(self):
        log('conv_layer: Destroying filters_desc, conv_desc')
        libcudnn.cudnnDestroyFilterDescriptor(self.filters_desc)
        libcudnn.cudnnDestroyFilterDescriptor(self.conv_desc)
        libcudnn.cudnnDestroyFilterDescriptor(self.biases_desc)
