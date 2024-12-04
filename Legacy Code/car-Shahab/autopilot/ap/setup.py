from distutils.core import setup, Extension

ap = Extension('ap',
                  sources=['ap.c'],
                  extra_compile_args=[
                      '-O3', '-march=native', '-mtune=native', '-ffast-math', '-fargument-noalias-global', '-fopenmp',  '-DNDEBUG'],
                  libraries=["gomp"]
                  )

setup(name='AUTOPILOT',
      version='1.0',
      description='Fast routines for CAR autopilot.',
      ext_modules=[ap])
