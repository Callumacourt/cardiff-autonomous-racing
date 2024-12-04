from distutils.core import setup, Extension
import numpy

simslam = Extension('simslam',
                  sources=['simslam.c'],
                  extra_compile_args=[
                      '-O3', '-march=native', '-mtune=native', '-ffast-math', '-fargument-noalias-global', '-fopenmp',  '-DNDEBUG'],
                  libraries=["gomp"]
                  )

setup(name='SIMSLAM',
      version='1.0',
      description='Functions for the SLAM.',
      ext_modules=[simslam],
      include_dirs=[numpy.get_include()])  # Get numpy install location incase it is not default
