#!/usr/bin/env python3

import concurrent.futures
import threading


FAIL_CHECK_TIMEOUT = 10  # ROUGH time between failure checks during shutdown


class _FailWorkItem(concurrent.futures.thread._WorkItem):
    def __init__(self, *args, fail_threadpool_recursive_ref, **kwargs):
        # self.fail_flag = fail_flag
        # self.fail_lock = fail_lock
        # self.fail_reason = fail_reason
        self.fail_parent = fail_threadpool_recursive_ref  # DON'T THINK ABOUT IT (exception wasn't making it back)
        super().__init__(*args, **kwargs)

    # I'm aware _WorkItem has no docs lol
    __init__.__doc__ = concurrent.futures.thread._WorkItem.__init__.__doc__

    def run(self):  # Yeah, we're just going to have to override the whole thing
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            # OH SHIT
            with self.fail_parent.fail_lock:
                if not self.fail_parent.fail_flag.is_set():
                    self.fail_parent.fail_reason = exc
                    self.fail_parent.fail_flag.set()

            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)

    run.__doc__ = concurrent.futures.thread._WorkItem.run.__doc__


class FailThreadPoolExecutor(concurrent.futures.thread.ThreadPoolExecutor):
    """
    ThreadPoolExecutor that eats it at the first sign of trouble.

    Submit/shutdown will re-raise the first exception a encountered
    """

    def __init__(self, *args, **kwargs):
        self.fail_flag = threading.Event()  # WE FUCKED IT?? flag
        self.fail_lock = threading.Lock()  # To be super safe. Processes don't need it, but we might
        self.fail_reason = Exception("UH-OH SPAGHETTIOS AN EXCEPTION WASN'T LOGGED??? MEMORY ISOLATED??")
        super().__init__(*args, **kwargs)

    __init__.__doc__ = concurrent.futures.thread.ThreadPoolExecutor.__init__.__doc__

    def submit(self, fn, *args, **kwargs):
        with self.fail_lock:
            if self.fail_flag.is_set():
                # Hell!
                raise self.fail_reason

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            f = concurrent.futures._base.Future()
            # w = _FailWorkItem(f, fn, args, kwargs,
            #                   fail_flag=self.fail_flag, fail_lock=self.fail_lock, fail_reason=self.fail_reason)
            w = _FailWorkItem(f, fn, args, kwargs, fail_threadpool_recursive_ref=self)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f

    submit.__doc__ = concurrent.futures.thread.ThreadPoolExecutor.submit.__doc__

    def shutdown(self, wait=True):
        with self._shutdown_lock:
            self._shutdown = True
            self._work_queue.put(None)
        if wait:
            # Jam in a timeout and keep checking the fail_flag
            for t in self._threads:
                while t.is_alive():
                    t.join(FAIL_CHECK_TIMEOUT)
                    with self.fail_lock:
                        if self.fail_flag.is_set():
                            raise self.fail_reason

            # One last check. No need to lock... probably
            if self.fail_flag.is_set():
                # Hell!
                raise self.fail_reason

    shutdown.__doc__ = concurrent.futures.thread.ThreadPoolExecutor.shutdown.__doc__
