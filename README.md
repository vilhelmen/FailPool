# FailPool

A mod to the cpython multiprocessing pool class that terminates the pool when an error occurs.

A progress bar with ETA will be written to stdout on pool join, or a job total to the logger.
Pool totals will not be completely accurate because the job totals aren't tracked internally by Pool.


### Keeping up to date

Since this is a mod against cpython internals, it can be risky to run on unchecked versions.

The most important part is that the `_timeout_join` functions does the same as `join`, but with timeouts.

### TODO

1. Reevaluate progress bars, imports, etc
1. Enable user-provided error_callback and just call mine after
1. Make better
1. Make pool kill optional while keeping timeout join (because pool can lock up otherwise!)[https://bugs.python.org/issue31782]
1. Check on FailThreadPoolExecutor becasue it probably works, buuuuut...


## FailPool

When an exception is raised, the pool will be terminated and the exception re-raised.

Note that specific submit functions will need to be overridden before use.


## FailThreadPoolExecutor

When an exception is raised, the work queue will be purged and the pool shutdown.
The exception will then be re-raised.
