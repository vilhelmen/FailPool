#!/usr/bin/env python3

# I have no idea what I'm doing

from .ThreadPoolExecutor import FailThreadPool
from .multiprocessing import FailPool

__all__ = ['FailThreadPool', 'FailPool']
