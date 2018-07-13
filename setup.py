#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='FailPool',
      version='0.0.1',
      description='Processing pools that grow up and blow away.',
      author='Will Starms',
      author_email='vilhelmen!AT!gmail.com',
      packages=find_packages(),
      license='Copyleft',
      install_requires=['progressbar2'],
      )
