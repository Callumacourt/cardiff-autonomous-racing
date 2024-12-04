import ctypes
import pycuda.compiler
import pycuda.driver as drv
from pycuda import gpuarray
import libcudnn
import numpy as np
import scipy.io as sio
from conv_layer import ConvLayer, data_type, tensor_format, convolution_mode
import wx
from log import log
# from context import cudnn_context
# start, end = (drv.Event(), drv.Event())
# def start_bench():
#     start.record()

# def end_bench(op):
#     end.record()
#     end.synchronize()
#     msecs = end.time_since(start)
#     print("%s: %7.3f msecs" % (op, msecs))

convolution_fwd_pref = libcudnn.cudnnConvolutionFwdPreference[
    'CUDNN_CONVOLUTION_FWD_PREFER_FASTEST']
softmax_algorithm = libcudnn.cudnnSoftmaxAlgorithm['CUDNN_SOFTMAX_FAST']
softmax_mode = libcudnn.cudnnSoftmaxMode['CUDNN_SOFTMAX_MODE_CHANNEL']


def load_cnn(filename):
    net = sio.loadmat(filename)

    f1 = np.ascontiguousarray(net['f1'])
    b1 = np.ascontiguousarray(net['b1'][None, :, :, None])
    f2 = np.ascontiguousarray(net['f2'])
    b2 = np.ascontiguousarray(net['b2'][None, :, :, None])
    f3 = np.ascontiguousarray(net['f3'])
    b3 = np.ascontiguousarray(net['b3'][None, :, :, None])
    f4 = np.ascontiguousarray(net['f4'])
    b4 = np.ascontiguousarray(net['b4'][None, :, :, None])
    f5 = np.ascontiguousarray(net['f5'][:, :, None, None])
    b5 = np.ascontiguousarray(net['b5'][None, :, :, None])

    t = f5[2, :, :, :].copy()
    f5[2, :, :, :] = f5[3, :, :, :]
    f5[3, :, :, :] = t

    t = b5[:, 2, :, :].copy()
    b5[:, 2, :, :] = b5[:, 3, :, :]
    b5[:, 3, :, :] = t

    log('Loading CNN from ' + filename)
    log('\tLayer 1: ' + str(f1.shape))
    log('\tLayer 2: ' + str(f2.shape))
    log('\tLayer 3: ' + str(f3.shape))
    log('\tLayer 4: ' + str(f4.shape))
    log('\tLayer 5: ' + str(f5.shape))

    layer1 = ConvLayer(f1, b1)
    layer2 = ConvLayer(f2, b2)
    layer3 = ConvLayer(f3, b3)
    layer4 = ConvLayer(f4, b4)
    layer5 = ConvLayer(f5, b5, relu=False, softmax=True)

    return [layer1, layer2, layer3, layer4, layer5]


class CNN:
    def __init__(self, layers, context=None, cudnn_context=None):
        self.layers = layers
        self.context = context
        self.cudnn_context = cudnn_context
        self.X_desc = libcudnn.cudnnCreateTensorDescriptor()
        self.Y_desc = libcudnn.cudnnCreateTensorDescriptor()
        self.reset()

    def reset(self):
        log('Resetting CNN.')
        self.ws_ptr = [None] * len(self.layers)
        self.Y = [None] * len(self.layers)
        self.algo = [None] * len(self.layers)
        self.output = None

    # @profile
    def predict(self, X):
        # app = wx.GetApp()
        # if app is None:
        #     return
        if self.context:
            self.context.push()

        # Allocate output buffer if necessary
        if self.output is None:
            self.output = gpuarray.zeros(
                (X.shape[0], self.layers[-1].filters.shape[0],
                 X.shape[2], X.shape[3]),
                dtype=np.float32)

        # Descriptor for input
        if X is not gpuarray.GPUArray:
            # log('Uploading to GPU.')
            X = gpuarray.to_gpu(X.astype(np.float32))
        for i, layer in enumerate(self.layers):
            # log('\nLAYER %d\n' % i)
            if 0 == i:
                libcudnn.cudnnSetTensor4dDescriptor(self.X_desc, tensor_format, data_type,
                                                    X.shape[0], X.shape[1], X.shape[2], X.shape[3])
            else:
                libcudnn.cudnnSetTensor4dDescriptor(self.X_desc, tensor_format, data_type,
                                                    X.shape[0], layer.channels_in(), height_output, width_output)

            # Get output dimensions (first two values are n_input and channels_out)
            _, _, height_output, width_output = libcudnn.cudnnGetConvolution2dForwardOutputDim(
                layer.conv_desc, self.X_desc, layer.filters_desc)

            # log('Output (%d x %d x %d x %d)\n' % (
            # X.shape[0], layer.channels_out(), height_output, width_output))

            # Output tensor
            if self.Y[i] is None:
                # log('Allocating output tensor.')
                self.Y[i] = gpuarray.empty(
                    (X.shape[0], layer.channels_out(), height_output, width_output), np.float32)
            libcudnn.cudnnSetTensor4dDescriptor(
                self.Y_desc, tensor_format, data_type,
                X.shape[0], layer.channels_out(), height_output, width_output)

            # Get pointers to GPU memory
            X_data = ctypes.c_void_p(int(X.gpudata))
            filters_data = ctypes.c_void_p(int(layer.filters.gpudata))
            Y_data = ctypes.c_void_p(int(self.Y[i].gpudata))

            # Perform convolution
            if self.algo[i] is None:
                # log('Detecting convolution algorithm.')
                self.algo[i] = libcudnn.cudnnGetConvolutionForwardAlgorithm(self.cudnn_context, self.X_desc,
                                                                            layer.filters_desc, layer.conv_desc, self.Y_desc, convolution_fwd_pref, 0)
            # log('Algorithm: %d' % (algo.value))

            ws_size = libcudnn.cudnnGetConvolutionForwardWorkspaceSize(
                self.cudnn_context, self.X_desc, layer.filters_desc, layer.conv_desc, self.Y_desc, self.algo[i])
            # log('Work space size: %d ' % (ws_size.value))
            if self.ws_ptr[i] is None:
                # log('Allocating workspace.')
                self.ws_ptr[i] = drv.mem_alloc(
                    ws_size.value) if ws_size.value > 0 else 0
            ws_data = ctypes.c_void_p(int(self.ws_ptr[i]))
            # start_bench()
            alpha = 1.0
            beta = 0.0
            libcudnn.cudnnConvolutionForward(self.cudnn_context, alpha, self.X_desc, X_data,
                                             layer.filters_desc, filters_data, layer.conv_desc, self.algo[
                                                 i], ws_data, ws_size.value, beta,
                                             self.Y_desc, Y_data)
            # end_bench('Convolution ')
            # ws_ptr = None

            # TODO: Custom kernel for both biases and activation?
            # Add bias
            # start_bench()
            biases_data = ctypes.c_void_p(int(layer.biases.gpudata))
            libcudnn.cudnnAddTensor(
                self.cudnn_context, 1.0, layer.biases_desc, biases_data, 1.0, self.Y_desc, Y_data)
            # end_bench('Biases      ')

            # Activation
            # start_bench()
            if layer.relu:
                self.Y[i] = gpuarray.maximum(self.Y[i], 0.0)

            # Softmax
            if layer.softmax:
                libcudnn.cudnnSoftmaxForward(
                    self.cudnn_context, softmax_algorithm, softmax_mode, alpha, self.Y_desc, Y_data, beta, self.Y_desc, Y_data)

            # end_bench('Activation  ')
            X = self.Y[i]

        shift_row = round((self.output.shape[2] - X.shape[2]) * 0.5 + 0.5)
        shift_col = round((self.output.shape[3] - X.shape[3]) * 0.5 + 0.5)
        self.output[:, :, shift_row:shift_row + X.shape[2],
                    shift_col:shift_col + X.shape[3]] = X
        # X = X[0, 0, 0:-1, 0:-1].get()
        # X = X.get()

        # app = wx.GetApp()
        # if app is None:
        #     return
        # out = self.output.get()

        if self.context:
            self.context.pop()
        return self.output

    def __del__(self):
        log('CNN: Destroying X_desc, Y_desc')
        libcudnn.cudnnDestroyTensorDescriptor(self.X_desc)
        libcudnn.cudnnDestroyTensorDescriptor(self.Y_desc)
        for i in range(len(self.ws_ptr)):
            self.ws_ptr[i] = None
