"""A playground environment, not to be used in production.

This module automatically connects to the different MySQL database and to 
Presto. It is expected to be loaded as `from bpa.sandbox import *`. The
following GrabMySQL objects are loaded:
    - `sql8`: connected to `external-8`
    - `sql8_stg`: connected to `staging-8`
    - `sql`: connected to `external`
    - `sql_stg`: connected to `staging`
together with a GrabPresto object `presto`.

The name of the SSM parameter is taken from an environment variable SSM_PARAM.
Use `setx SSM_PARAM </automation/...>` in console to setup the environment 
variable and then restart the command line.
The SSM parameter is expected to have `db_ext8`, `db_stg8`, `db_ext` and 
`db_stg` parameters (used to connect to MySQL database) and `db_presto` (for
Presto).

"""
import os

from .aws import get_ssm_parameter
from .presto import GrabPresto
from .sql import GrabMySQL

ssm_param = os.environ.get('SSM_PARAM')
if ssm_param is None:
    raise OSError(f"'SSM_PARAM' must be set as environment variable.")
PARAMS = get_ssm_parameter(ssm_param)

if 'db_ext8' in PARAMS:
    sql8 = GrabMySQL(PARAMS['db_ext8'])
if 'db_stg8' in PARAMS:
    sql_stg8 = GrabMySQL(PARAMS['db_stg8'])
if 'db_ext' in PARAMS:
    sql = GrabMySQL(PARAMS['db_ext'])
if 'db_stg' in PARAMS:
    sql_stg = GrabMySQL(PARAMS['db_stg'])

if 'db_presto' in PARAMS:
    presto = GrabPresto(PARAMS['db_presto'])
