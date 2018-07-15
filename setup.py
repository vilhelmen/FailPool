#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='FailPool',
      version='0.0.3',
      description='Processing pools that grow up and blow away.',
      author='Will Starms',
      packages=find_packages(),
      license='Copyleft',
      install_requires=['progressbar2'],
      python_requires='>=3.6, <3.8'  # I hate this so much
      )

