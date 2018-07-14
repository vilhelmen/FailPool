# FailPool

What's the point of going on when something breaks. Also ETA reports.

A progress bar with ETA will be written to stdout on pool join, or a job total to the logger.
Pool totals will not be completely accurate because the job totals aren't tracked internally.

### FailPool

When an exception is raised, the pool will be terminated and the exception re-raised.

Note that specific submit functions will need to be overridden before use.


### FailThreadPoolExecutor

When an exception is raised, the work queue will be purged and the pool shutdown.
The exception will then be re-raised.