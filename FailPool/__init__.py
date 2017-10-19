#!/usr/bin/env python3

# I have no idea what I'm doing

from .ThreadPoolExecutor import FailThreadPoolExecutor
from .multiprocessing import FailPool

__all__ = ['FailThreadPoolExecutor', 'FailPool']

import sys

assert sys.version_info.major == 3 and sys.version_info.minor == 6
