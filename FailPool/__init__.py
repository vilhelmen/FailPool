#!/usr/bin/env python3

import platform
import sys

assert sys.version_info.major == 3 and sys.version_info.minor in (
    6, 7, 8, 9) and platform.python_implementation() == 'CPython'

from .ThreadPoolExecutor import FailThreadPoolExecutor
from .multiprocessing import FailPool, FailThreadPool

__all__ = ['FailThreadPoolExecutor', 'FailPool', 'FailThreadPool']
