# FailPool

What's the point of going on when something breaks

### FailPool

When an exception is raised, the pool will be terminated and the exception re-raised.

Note that specific submit functions will need to be overridden before use.


### FailThreadPoolExecutor

When an exception is raised, the work queue will be purged and the pool shutdown.
The exception will then be re-raised.