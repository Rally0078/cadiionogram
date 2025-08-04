from setuptools import setup, Extension
from Cython.Build import cythonize
ext_modules = [Extension("mainGUI", ['./src/plot/main.py']), 
               Extension("mainWidget", ['./src/ui/mainwidget.py']),
               Extension('metadatatable', ['./src/ui/metadatatable.py']),
               Extension('mdxreader', ['./src/ionogramparser/mdxreader.py'])]
for e in ext_modules:
    e.cython_directives = {'language_level' : '3'}
setup(
    name='testbuild',
    ext_modules = ext_modules
)