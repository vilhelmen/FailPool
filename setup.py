#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='FailPool',
      version='0.0.5',
      description='Processing pools that grow up and blow away.',
      author='Will Starms',
      packages=find_packages(),
      license='MIT',
      install_requires=['progressbar2'],
      python_requires='>=3.6, <=3.9'
      )

