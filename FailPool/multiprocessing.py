#!/usr/bin/env python3

import multiprocessing.pool
import logging
from threading import Event


class FailPool(multiprocessing.pool.Pool):
    """
    Multiprocessing Pool that chlorinates the pool when a worker dies in it

    Uses the error_callback to flag if a worker died.
    If it did, apply_async and join will terminate the pool and raise the original exception

    Don't use a job submit function without overriding it here
        Overriding enables error_callback for test job errors and tests for pool failure on job submit
    """

    def __init__(self, *args, **kwargs):
        self.fail_flag = Event()
        self.fail_reason = "FAIL REASON UNSET OH NO MEMORY IS SEPARATE AND THIS IS BROKEN"
        super().__init__(*args, **kwargs)

    # Ahh hell, we can't have self in the callback probably
    # May need to expose a global or something disgusting like that.
    # Will need to move to a separate file if that's the case
    def _error_callback_override(self, e):
        if not self.fail_flag.is_set():
            self.fail_flag.set()  # technically this should be safe because there is only one result processor thread
            self.fail_reason = e

    def _eat_it(self):
        self.terminate()
        # raising dumps a RemoteTraceback showing where in the worker it died
        # But it may need more testing
        raise self.fail_reason

    def apply_async(self, *args, error_callback=None, **kwargs):
        """
        Apply async, but with a fail check and no error_callback
        """
        if error_callback:
            raise ValueError('Attempt to use error_callback in FailPool')
        if self.fail_flag.is_set() and self._state != multiprocessing.pool.TERMINATE:
            self._eat_it()

        error_callback = self._error_callback_override  # maybe this will work?

        return super().apply_async(*args, error_callback=error_callback, **kwargs)

    def join(self):
        """
        Join, but periodically checks fail state
        """
        while not self._timeout_join(10):
            logging.info(f'~{self._taskqueue.qsize()} jobs remaining')
            if self.fail_flag.is_set():
                self._eat_it()
        if self.fail_flag.is_set():
            self._eat_it()

    def _timeout_join(self, timeout):
        """
        Join but with a timeout. Does not check fail state. Probably don't use this directly.
        :param timeout: timeout in seconds
        :return: Bool, whether the pool was joined or not
        """
        if self._state == multiprocessing.pool.RUN:
            raise ValueError("Pool is still running")
        elif self._state not in (multiprocessing.pool.CLOSE, multiprocessing.pool.TERMINATE):
            raise ValueError("In unknown state")
        self._worker_handler.join(timeout=timeout)
        if self._worker_handler.is_alive():
            return False
        self._task_handler.join()
        self._result_handler.join()
        for p in self._pool:
            p.join()
        return True


class FailThreadPool(multiprocessing.pool.ThreadPool, FailPool):
    """
    Multiprocessing ThreadPool that chlorinates the pool when a worker dies in it.

    ThreadPool is such a thin wrapper this probably works maybe

    Uses the error_callback to flag if a worker died.
    If it did, apply_async and join will terminate the pool and raise the original exception

    Don't use a job submit function without overriding it in FailPool
        Overriding enables error_callback for test job errors and tests for pool failure on job submit
    """
    pass
