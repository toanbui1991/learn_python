"""Module to interact with MySQL

Functions
---------
    mysql_retry :
        Decorator used to retry MySQL queries.
    prepare_df :
        Prepares a `pd.DataFrame` to be used a query parameters for MySQL.
    jsonify_sql :
        Turns a SQL query into a json files for BatMan-style source input.
    replace :
        Replaces the parameter from a BatMan-style parametrized query.
           
Classes
-------
    GrabSQL : 
        Class used to interact with MySQL. Can be used either for single
        query which are directly commited, or within a context manager to
        replicate MySQL transaction.

"""
import contextlib
import json
import logging
import os
import pathlib
import re
import reprlib
from ssl import SSLError
from pathlib import Path
import backoff
import pandas as pd
import pymysql
import pyperclip

"""Errors to retry for MySQL
"""
MYSQL_ERRORS = (
    pymysql.err.OperationalError, pymysql.err.InternalError,
    ConnectionResetError
)


"""MySQL retry decorator
"""
mysql_retry = backoff.on_exception(backoff.expo, MYSQL_ERRORS, max_time=20)


class QueryRepr(reprlib.Repr):
    """String repr of a query.

    Simply `reprlib.Repr` with a maximum string length of 120.

    """
    def __init__(self):
        super(QueryRepr, self).__init__()
        self.maxstring = 120
query_repr = QueryRepr().repr


def query_type(query):
    """Returns the type (SELECT, EXPLAIN, INSERT or UPDATE) of query

    """
    return query.split(maxsplit=1)[0].upper()


def prepare_df(df, type='list', null_to_none=True):
    """Prepares a DataFrame to be used as parameters for MySQL queries.

    The DataFrame is either transformed into a list of list (type='list') - for
    un-named query parameters (%s or %(1)s) - or into a list of dictionary
    (type='dict') - for named query parameters (%(name)s).
    If `null_to_none=True` then the Null values are replaced by None.

    Parameters
    ----------
    df : `pd.DataFrame`
        The DataFrame to prepare.
    type : str {'list', 'dict'}
        If 'list' then the a list of list is returned. If 'dict' then a dict of
        list is returned. 
    null_to_none : bool
        If `True` then null values are replaced to None.
    
    Returns
    -------
    List of list, or list of dict, depending on `type` parameter.
    """
    if null_to_none:
        df = df.where((pd.notnull(df)), None)
    if type.lower() == 'list':
        return df.values.tolist()
    elif type.lower() == 'dict':
        return df.to_dict('records')
    else:
        raise ValueError('type must be either "list" or "dict".')


class GrabMySQL():
    """Class implementing common and simple interactions with MySQL.

    The class mainly implements two methods: `extract` and `modify`. 
    The `extract` is used for SELECT or EXPLAIN statements, and returns the 
    results as a `pd.DataFrame`.
    The `modify` method runs a INSERT or UPDATE statements, and returns the
    a tuple with the number of row modified and the first row id modified.
    When a GrabMySQL object is used outside a `with` statements, then it is
    in auto_commit mode, and rolled-back in case of error and retried using
    the `mysql_retry` decorator.
    When a GrabMySQL object is used as a context manager, then the transaction
    is commited when exiting the `with` statement. No retry is applied in this 
    case; the retry needs to be manually implemented.

    Examples
    --------
    >>> db_params = {
    ...     'db': 'invoicing_collection', 
    ...     'host': 'staging-8.cssioamt5bki.ap-southeast-1.rds.amazonaws.com', 
    ...     'port': 3306, 
    ...     'user': 'tibor_frossard', 
    ...     'password': '<my_password>'
    ... }
    >>> sql = GrabMySQL(db_params)

    auto_commit mode: each SQL statement is directly commited.

    >>> df = sql.extract(
    ...     "SELECT * FROM disputes WHERE country_id = %s LIMIT 10", 2)
    >>> query_insert = '''
    ...    INSERT INTO 
    ...         dispute_batch (batch_id, dispute_id, booking_code) 
    ...    VALUES 
    ...         (%s, %s, %s)
    ... '''
    >>> sql.modify(query_insert, ((12, 23, 'a'), (12, 2333, 'a')))
    (2, 0)
    >>> df = pd.DataFrame(
    ...     [(811, 223, 'xxxaa'), (805, 22222333, 'aa')], 
    ...     columns=['batch_id', 'dispute_id', 'booking_code']
    ... )
    >>> sql.insert_df(df, 'dispute_batch', on_dupl_update_clmns=df.columns)

    transaction mode: commit when exiting the `with` statement. The queries
    are not retried in this case.

    >>> with sql:
    ...     sql.modify(query_insert, ((12, 23, 'a'), (12, 2333, 'a')))
    ...     sql.modify(query_insert, ((14, 23, 'a'), (1222, 2333, 'a')))

    Add retry feature: use mysql_retry decorator

    >>> @mysql_retry
    ... def transaction(sql):
    ...     with sql:
    ...         sql.modify(query_insert, ((12, 23, 'a'), (12, 2333, 'a')))
    ...         sql.modify(query_insert, ((14, 23, 'a'), (1222, 2333, 'a')))
    >>> transaction(sql)     

    Some additional convenience functions

    >>> query = 'SELECT * FROM disputes WHERE country_id = %s'
    >>> df_explain = sql.explain(query, 2)  # Run EXPLAIN on query
    >>> query_str = sql.query(query, 2)  # Return actual query string

    """
    DEFAULT_SSL_PATH = os.path.join(
        pathlib.Path(__file__).parent.absolute(), 'ssl', 'Amazon RDS 2020.pem')

    def __init__(self, db_params):
        """Instantiate a GrabMySQL object

        if `db_params` does not specified the SSL certificate or the specified
        path cannot be found, then the default SSL certificate, located in the
        `ssl` folder, is temptatively used.

        Parameters
        ----------
        db_params : dict
            Connection parameters.
        
        Returns
        -------
        <GrabMySQL> object.

        """
        logging.info('Connecting to %s', db_params.get('host'))
        valid_ssl_path = False
        db_params = db_params.copy()  # Avoid modification of arguments
        if 'ssl' in db_params:
            try:
                valid_ssl_path = os.path.isfile(db_params['ssl'].get('ca'))
            except (AttributeError, TypeError):
                valid_ssl_path = False
            if not valid_ssl_path:
                del db_params['ssl']
                logging.info(
                    'The provided SSL certificate is invalid. Trying default.')
        if not valid_ssl_path:
            ca_path = self.__class__.DEFAULT_SSL_PATH
            if os.path.isfile(ca_path):
                logging.debug('Using default SSL certificate at %s', ca_path)
                db_params['ssl'] = {'ca': ca_path}
            else:
                logging.debug(
                    'Default SSL certificate at %s cannot be found.', ca_path)
        try:
            self._con = pymysql.connect(**db_params)
        except SSLError:
            ssl =  db_params.pop('ssl')
            self._con = pymysql.connect(**db_params)
            logging.info(
                'Invalid SSL certificate %s. Connect without SSL', ssl)
        self._auto_commit = True
        logging.info('Connection opened successfully')


    def __repr__(self):
        return f"GrabMySQL({{'host':{reprlib.repr(self._con.host)}, ...}})"


    def extract(self, query, params=None):
        """Runs a `SELECT` or `EXPLAIN` query and returns its result as a 
        DataFrame.

        If used outside a context manager, then query is automatically retried
        in case of SQL errors.

        Parameters
        ----------
        query : str
            The SQL `SELECT` or `EXPLAIN` query to run.
        params : tuple, list, or dict
            Parameters used with query.
        
        Returns
        -------
        <pd.DataFrame>
        """

        if self._auto_commit:
            return mysql_retry(self._extract)(query=query, params=params)
        else:
            return self._extract(query=query, params=params)


    def modify(self, query, params=None):
        """Run an `INSERT`, `UPDATE` or `DELETE` query.

        If params is a list/tuple of dict/list/tuple, then the query is run
        using `executemany`. Otherwise, it is run using `execute`.
        If used outside a context manager, then query is automatically 
        rolled-bakc and retried in case of SQL errors, and commited when run 
        successfully.

        Parameters
        ----------
        query : str
            The SQL `INSERT`, `UPDATE` or `DELETE` query to run.
        params : tuple, list, or dict
            Parameters used with query.
        
        Returns
        -------
        A 2-elements tuple with number of modified rows, and the id of the
        first modified row.

        """
        if self._auto_commit:
            try:
                res = mysql_retry(self._modify)(query=query, params=params)
            except Exception as err:
                logging.info(
                    'Catching exception during modify', exc_info=True)
                self._con.rollback()
                raise err
            else:
                return res
        else:
            logging.info('Using transaction mode')
            return self._modify(query, params) 
    

    def __enter__(self):
        """Enter auto-commit mode.

        The transactions are automatically commited or rolled-back (in case of 
        errors) when exiting the `with` statement. No retry is applied.

        """
        self._con.ping()
        self._cursor = self._con.cursor()
        self._auto_commit = False
        return self


    def __exit__(self, exception_type, exception_value, traceback):
        """Exit auto-commit mode.

        The transactions are either rolled-back or commited.
        """
        self._auto_commit = True
        if traceback:
            self._con.rollback()
        else:
            self._con.commit()


    def _extract(self, query, params=None):
        if query_type(query) not in ('SELECT', 'EXPLAIN'):
            logging.info(
                'The query %s is not a SELECT or EXPLAIN query', 
                query_repr(query)
            )
            raise ValueError('`query` must be a SELECT or EXPLAIN query.')
        logging.info(
            'Extract data using %s with parameters %s', 
            query_repr(query), query_repr(params)
        )
        logging.debug('Full query: %s', self.query(query, params))
        if self._auto_commit:
            self._con.ping()
            cursor = self._con.cursor()
        else:
            cursor = self._cursor
        cursor.execute(query, params)
        data = cursor.fetchall()
        clmns = [d[0] for d in cursor.description]
        df = pd.DataFrame(list(data), columns=clmns)
        logging.info('%s rows extracted successfully', len(df))
        logging.debug('Full extraction: %s', df)
        return df


    def _modify(self, query, params=None):
        if query_type(query) not in ('INSERT', 'UPDATE', 'DELETE'):
            logging.info(
                'The query %s is not a INSERT, UPDATE or DELETE query', 
                query_repr(query)
            )
            raise ValueError('`query` must be a UPDATE, INSERT or DELETE query.')
        # Find out if it must be run using executemany
        many = False
        if isinstance(params, (list, tuple)):
            if isinstance(params[0], (dict, list, tuple)):
                many = True
        logging.info(
            'Run modifier query %s with parameters %s',
            query_repr(query), query_repr(params))
        if self._auto_commit:
            self._con.ping()
            cursor = self._con.cursor()
        else:
            cursor = self._cursor
        
        if many:
            nrows = cursor.executemany(query, params)
        else:
            nrows = cursor.execute(query, params)
        if self._auto_commit:
            self._con.commit()
        first_row_id = cursor.lastrowid  # This is actually the first row.
        logging.info(
            '%s rows modified with %s first row id', nrows, first_row_id)
        return nrows, first_row_id


    def insert_df(self, df, table_name, on_dupl_update_clmns=None):
        """Insert a DataFrame into a table.

        The column names of the DataFrame and table must match. As the SQL
        query is created from the DataFrame columns and table_name it is not
        safe from SQL query injection. It is the responsabilty of the user to
        make sure the query is safe.

        Parameters
        ----------
        df : <pd.DataFrame>
            The DataFrame to insert.
        table_name : str
            The name of the table. The column names must match the DataFrame
            column names.
        on_dupl_update_clmns : iterable
            The list of columns to update in case of duplicated key. If None, 
            then no columns are updated (and an error is raised in case of 
            duplicated keys.).
        
        Returns
        -------
        A 2-elements tuple as returned by `GrabMySQL.modify`.

        """
        if len(df) == 0:
            logging.info(
                'Inserting dataframe into %s. Nothing to insert.', table_name
            )
            return (0, 0)

        query = f"""
            INSERT INTO 
                {table_name} ({','.join(list(df.columns))})
            VALUES
                ({','.join(['%s'] * df.shape[1])})
        """
        if isinstance(on_dupl_update_clmns, str):
            on_dupl_update_clmns = list(on_dupl_update_clmns)
        if on_dupl_update_clmns is not None and len(on_dupl_update_clmns) > 0:
            update = [f'{clmn}=VALUES({clmn})' for clmn in on_dupl_update_clmns]
            query = query + ' ON DUPLICATE KEY UPDATE ' + ', '.join(update)
        return self.modify(query, prepare_df(df, 'list', True))


    def explain(self, query, params=None):
        """Run EXPLAIN on the query, and returns its result as a DataFrame.
        
        Parameters
        ----------
        query : str
            The SQL query to explain, without the `EXPLAIN` keyword.
        params : tuple, list, or dict
            Parameters used with query.
        
        Returns
        -------
        <pd.DataFrame>

        """
        explained_query = 'EXPLAIN ' + query
        return self.extract(explained_query, params)


    @mysql_retry
    def query(self, query, params=None, to_clipboard=False):
        """Returns the exact string (with parameters replaced).

        Parameters
        ----------
        query : str
            The parametrized SQL query.
        params : tuple, list, or dict
            Parameters used with query.
        to_clipboard : bool
            Wether to copy the resulting string to clipboard.

        Returns
        -------
        str.

        """
        self._con.ping()
        cursor = self._con.cursor()
        query = cursor.mogrify(query, params)
        if to_clipboard:
            pyperclip.copy(query)
        return query


    def close(self):
        """Close the connection to the database

        """
        self._con.close()
        logging.info('Connection closed successfully.')


    @contextlib.contextmanager
    def named_lock(self, lock_name, timeout):
        """Get a named lock on MySQL database.

        The lock is exclusive. While held by one session, other sessions cannot 
        obtain a lock of the same name. Other sessions might still access the 
        database if they do not try to obtain a lock with the same name. This
        is usefull to avoid multiple scripts running at the same time.

        Parameters
        ----------
        lock_name : str
            Name of the lock. 
        timeout : int
            Timeout in seconds to acquire lock before raising an error. A 
            negative timeout means infinite timeout.
        
        Returns
        -------
        None.
        
        """
        lock = self.extract("SELECT GET_LOCK(%s, %s)", (lock_name, timeout))
        if lock.iloc[0, 0] == 1:
            logging.debug('Named lock %s obtained successfully', lock_name)
            try:
                yield None
            finally:
                logging.debug('Releasing named lock %s', lock_name)
                self.extract('SELECT RELEASE_LOCK(%s)', (lock_name))
        else:
            e = f'Could not obtain named lock {lock_name} within {timeout} seconds.'
            raise RuntimeError(e)


def jsonify_sql(path_sql, path_json=None):
    """Transforms a SQL query into the corresponding json file.

    The SQL query is read from `path_sql`, and then the result is saved
    in `path_json`. The parameters in a commented part of the query
    are also extracted and added to the json. If the parameters are not
    following the expected format `{{name>value>default}}` where `default` is
    optional, then it raises an `ValueError`.

    Parameters
    ----------
    path_sql : str
        Path to `.sql` file.
    path_json : str, optional
        Path to output file, including json extension. If None (default), the
        folder is the parent directory of `path_sql` and the filename is the
        original filename with .json extension.

    Returns
    -------
    None

    """
    if path_json is None:
        folder, sql_name = os.path.split(path_sql) 
        json_name = sql_name + '.json'
        path_json = os.path.join(Path(folder).parent, json_name)
    with open(path_sql, encoding='utf-8') as file:
        sql = file.read()

    params = get_params(sql)
    sql_json = {'sql': sql}
    if params:
        sql_json['params'] = params

    with open(path_json, 'w', encoding='utf-8') as file:
        json.dump(sql_json, file, indent=2, ensure_ascii=False)
    return None


def get_params(sql):
    """Extracts parameters from a SQL query.

    The parameters in SQL query are enclosed in double curly brackets.

    Parameters
    ----------
    sql : str
          SQL query to extract parameters from.
    Returns
    -------
    List of dict
    """
    # TODO: exclude parameters in comments
    param_pattern = '({{.+?>.+?}})'
    params = set(re.findall(param_pattern, sql))

    params = [param_parser(p) for p in params]

    return params


def replace(sql, params_dict):
    """Replaces parameters in SQL query with values from `params_dict.

    Useful for quick checking of SQL query.

    Parameters
    ----------
    sql : str
        SQL query or path to SQL query.
    params_dict : dict
        Dictionay of param_name:value.
    Returns
    -------
    str
        SQL query with parameters enclosed in double curly bracket replaced
        by the corresponding value from `params_dict`
    """
    if sql.endswith('.sql'):
        with open(sql, encoding='utf-8') as file:
            sql = file.read()

    params = get_params(sql)
    for param in params:
        name = param['name']
        rep = param['replace']
        param_type = param['type']
        param_default = param.get('default', None)
        value = param_default or params_dict.get(name, None)
        if value is None:
            raise ValueError(
                f'Parameter {name} must be included in params_dict')
        if param_type == 'number':
            value = str(value)
        elif param_type == 'date':
            value = f"date('{value}')"
        elif param_type == 'string':
            value = "'" + value + "'"
        else:
            raise ValueError("Invalid type " + param_type)
        sql = re.sub(rep, value, sql)
    return sql


def param_parser(param):
    """Parses parameters (enclosed in double curly bracket in the query)

    The `param` must have the format `{{name<type<default}}`,
    for example `{{country<numeric<1}} or `{{country<numeric}}` (the default
    value is optional.)
    The function returns a dictionnary with parameter name, type, replace,
    and default (if any).

    Parameters
    ----------
    param : str
        Format as '{{name<type<default}}' where the default part is optional.
    
    Returns
    -------
    dict
    """
    param_exploded = re.sub('({{)|(}})', '', param).split('>')
    if len(param_exploded) < 2:
        err_mess = f'Parameters {param} is not following the right format'
        raise ValueError(err_mess)
    param_name = param_exploded[0]
    param_type = param_exploded[1]
    param_default = param_exploded[2] if len(param_exploded) > 2 else None
    param_dict = {'name': param_name, 'type': param_type, 'replace': param}
    if param_default is not None:
        if param_type == 'number':
            try:
                param_default = int(param_default)
            except ValueError:
                param_default = float(param_default)
        param_dict['default'] = param_default

    return param_dict
