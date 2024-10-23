from setuptools import setup
from panda3d_toolbox.__version__ import __version__

setup(
    name='panda3d_toolbox',
    description='A collection of helpful utility methods and constants for working with the Panda3D game engine',
    long_description=open("README.md", 'r').read(),
    long_description_content_type='text/markdown',
    license='MIT',
    version=__version__,
    author='Jordan Maxwell',
    maintainer='Jordan Maxwell',
    url='https://github.com/NxtStudios/panda3d-toolbox',
    packages=['panda3d_toolbox'],
    classifiers=[
        'Programming Language :: Python :: 3',
    ],
    install_requires=[
        'panda3d_vfs==1.0.0'
    ])
