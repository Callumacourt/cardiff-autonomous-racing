from distutils.core import setup, Extension

amsvm = Extension('amsvm',
                  sources=['amsvm.c'],
                  extra_compile_args=[
                      '-O3', '-march=native', '-mtune=native', '-ffast-math', '-fargument-noalias-global', '-fopenmp',  '-DNDEBUG'],
                  libraries=["gomp"]
                  )

setup(name='AM_SVM',
      version='1.0',
      description='Classifying images using eigenspace appearane models and SVM.',
      ext_modules=[amsvm])
