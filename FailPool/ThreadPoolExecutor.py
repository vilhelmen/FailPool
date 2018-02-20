#!/usr/bin/env python3

import concurrent.futures
import threading
import queue
import logging


class _FailWorkItem(concurrent.futures.thread._WorkItem):
    def __init__(self, *args, fail_threadpool_recursive_ref, **kwargs):
        # self._fail_flag = _fail_flag
        # self._fail_lock = _fail_lock
        # self._fail_reason = _fail_reason
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
        self._fail_flag = threading.Event()  # WE FUCKED IT?? flag
        self._fail_lock = threading.Lock()  # To be super safe. Processes don't need it, but we might
        self._fail_reason = Exception("UH-OH SPAGHETTIOS AN EXCEPTION WASN'T LOGGED??? MEMORY ISOLATED??")
        self._queue_dumped = False
        self._check_timeout = 10
        super().__init__(*args, **kwargs)

    __init__.__doc__ = concurrent.futures.thread.ThreadPoolExecutor.__init__.__doc__

    def _dump_queue(self):
        """
        Toss any remaining work in the queue
        """
        try:
            while True:
                self._work_queue.get(block=False)
        except queue.Empty:
            pass
        self._queue_dumped = True

    def _eat_it(self):
        raise self._fail_reason

    def submit(self, fn, *args, **kwargs):
        # self._fail_lock.aquire()  # Don't bother locking, if we ever so slightly miss seeing it get set, oh well.
        if self._fail_flag.is_set():
            # Move dump to post-shutdown flagging so threads will best coordinate with the dump
            # self._fail_lock.release()
            self.shutdown(_dump=True)
        # self._fail_lock.release()

        with self._shutdown_lock:
            if self._shutdown:
                raise RuntimeError('cannot schedule new futures after shutdown')

            f = concurrent.futures._base.Future()
            # w = _FailWorkItem(f, fn, args, kwargs,
            #                   _fail_flag=self._fail_flag, _fail_lock=self._fail_lock, _fail_reason=self._fail_reason)
            w = _FailWorkItem(f, fn, args, kwargs, fail_threadpool_recursive_ref=self)

            self._work_queue.put(w)
            self._adjust_thread_count()
            return f

    submit.__doc__ = concurrent.futures.thread.ThreadPoolExecutor.submit.__doc__

    def shutdown(self, wait=True, _dump=False):

        with self._shutdown_lock:
            if self._shutdown:
                # This should avoid the contextmanager from raising when it calls shutdown
                #  if submit already triggered shutdown
                return
            self._shutdown = True
            if _dump:
                self._dump_queue()
            self._work_queue.put(None)

        if wait:
            # Keep checking fail flag, assuming we haven't already failed and dumped the queue
            for t in self._threads:
                while t.is_alive():
                    t.join(timeout=self._check_timeout)
                    if not self._queue_dumped:  # if we dumped the queue, nothing to do but move on
                        logging.info(f'~{self._work_queue.qsize()} jobs remaining')
                        # with self._fail_lock: # Once again, don't bother. If we miss it by one iteration, who cares
                        if self._fail_flag.is_set():
                            self._dump_queue()
                            self._check_timeout = None  # we've done what we can, wait on joins

            self._threads.clear()

            # even if the very last thread to join failed, we will have caught it and dumped the queue
            if self._queue_dumped:
                self._eat_it()

    shutdown.__doc__ = concurrent.futures.thread.ThreadPoolExecutor.shutdown.__doc__
