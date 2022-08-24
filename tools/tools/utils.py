"""Codebase for general utility functions.
"""
import inspect
import sys
import time
from functools import wraps

import pandas as pd

"""Nice looking log message sent to stdout"""
logger_params = {
    'format': '%(asctime)s:%(levelname)s:%(message)s', 
    'datefmt': '%H:%M:%S', 'stream': sys.stdout
}

"""Grab country_id's"""
COUNTRIES = pd.DataFrame(
    {
        'country_id': [1, 2, 3, 4, 5, 6, 9, 10],
        'code': ['MY', 'PH', 'TH', 'SG', 'VN', 'ID', 'MM', 'KH'],
        'name': [
            'Malaysia', 'Philippines', 'Thailand', 'Singapore', 'Vietnam', 
            'Indonesia','Myanmar', 'Cambodia'
            ]
    }
)

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def chunkify(chunk_size, param_name, delay=0):
    """Decorator to run a function by chunk.

    The decorated function is run by chunk based on its argument `param_name`. 
    The returned value is a list of returned values from the original function.
    `param_name` must be a list-like argument from the decorated function. It
    needs to support the slice indexing (works for `pandas.DataFrame`).

    Parameters
    ----------
    chunk_size : int
        Size of chunk.
    param_name : str
        Name of the parameter of the decorated function to split into chunk.
    delay : float
        Delay in seconds between chunks.

    Returns
    -------
    A decorator.

    Examples
    --------
    >>> @chunkify(3, 'x')
    ... def f(x):
    ...     return sum(x)
    >>> f(list(range(10)))
    ... [3, 12, 21, 9]

    """
    def decorator(fn):
        @wraps(fn)
        def inner(*fargs, **fkwargs):
            sig = inspect.signature(fn)
            bound_arguments = sig.bind(*fargs, **fkwargs)
            bound_arguments.apply_defaults()
            if param_name not in bound_arguments.arguments:
                raise ValueError(
                    f'"{param_name}" must be an argument of {fn.__name__}')
            res_list = []
            args = bound_arguments.arguments[param_name]
            for chunk_args in chunks(args, chunk_size):
                bound_arguments.arguments[param_name] = chunk_args
                res_list.append(fn(**bound_arguments.arguments))
                time.sleep(delay)
            return res_list
        return inner
    return decorator
