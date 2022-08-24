import logging

import pandas as pd
from pyhive import presto


class GrabPresto:
    """A simple wrapper around `pyhive.presto`.

    Presto should not be queried directly from Python in production. Only for
    testing on local laptop.
    
    """
    DEFAULT_CONNECTION = {
        'protocol': 'https', 'catalog': 'hive', 
        'host': 'presto-s.grab-bat.net',
        'port': 443
    }
    def __init__(self, db_params):
        """Instantiates a GrabPresto object

        Parameters
        ----------
        db_params : dict
            Dictionary with `host`, `port`, `username`, `password`. `catalog`
            and `protocol` are optional.
        
        Returns
        -------
        A GrabPresto object

        """
        logging.info('Connecting to Presto')
        self._con = presto.connect(
            **{**self.__class__.DEFAULT_CONNECTION, **db_params})
        self._cursor = self._con.cursor()    


    def __repr__(self):
        return f'GrabPresto(...)'


    def extract(self, query, params=None):
        """Extracts data from Presto and returns its result as a DataFrame.

        Parameters
        ----------
        query : str
            The SQL query to run.
        params : tuple, list, or dict
            Parameters used with query.
        
        Returns
        -------
        <pd.DataFrame>
        """
        self._cursor.execute(query, params)
        data = self._cursor.fetchall()
        clmns = [d[0] for d in self._cursor.description]
        df = pd.DataFrame(list(data), columns=clmns)
        logging.info('%s rows extracted successfully', len(df))
        return df
