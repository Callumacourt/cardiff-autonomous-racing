import pycuda


class Kernels:
    def __init__(self, context):
        self.context = context
        with open('kernels.cu', 'r') as file:
            kernels_src = file.read()
        if self.context is not None:
            self.context.push()
        kernels = pycuda.compiler.SourceModule(kernels_src)
        # TODO: Make NN/BL an option
        self.resize_write_max = kernels.get_function(
            "resize_bl_write_max")
        self.write_max = kernels.get_function("write_max")
        # threshold = kernels.get_function("threshold")
        self.relu = kernels.get_function("relu")
        self.threshold_max_argmax_label = kernels.get_function(
            "threshold_max_argmax_label")
        self.visualise_detection = kernels.get_function(
            "visualise_detection")
        if self.context is not None:
            self.context.pop()
