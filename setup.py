from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = [cythonize('./src/plot/main.py'), cythonize('./src/plot/mainwidget.py')]
)