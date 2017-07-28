from setuptools import setup
import os
import sys

sys.setrecursionlimit(1500)

def under(parent):
    for dirpath, dirnames, files in os.walk(parent):
        for f in files:
            yield os.path.join(dirpath, f)

APP = ['EggDrop.py']
MODULES = ['header', 'helper', 'sprites']
DIR = ['fonts', 'data', 'img', 'snd']
DATA_FILES = [(i, [i for i in under(i)]) for i in DIR]
OPTIONS = {
    'iconfile':os.path.join('img', 'eggdrop.icns'),
    'excludes':['metaplotlib','scipy','numpy', 'cjkcodecs', 'docutils', 'PIL', 'pydoc', 'PyOpenGL', 'sip']}

setup(
    name='EggDrop',
    version="1.0.0",
    author="Moku",
    license="This work is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License.",
    app=APP,
    py_modules=MODULES,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
