from distutils.core import setup, Extension
import numpy

simgeom = Extension('simgeom',
                  sources=['simgeom.c'],
                  extra_compile_args=[
                      '-O3', '-march=native', '-mtune=native', '-ffast-math', '-fargument-noalias-global', '-fopenmp',  '-DNDEBUG'],
                  libraries=["gomp"]
                  )

setup(name='SIMGEOM',
      version='1.0',
      description='Geometric functions for the simulator.',
      ext_modules=[simgeom],
      include_dirs=[numpy.get_include()])  # Get numpy install location incase it is not default
