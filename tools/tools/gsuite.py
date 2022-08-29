import copy
import functools
import io
import json
import mimetypes
import os
import random
import string
import time
from contextlib import contextmanager
from functools import partial
from itertools import groupby
from operator import itemgetter
from os.path import basename, dirname, normpath
from urllib.parse import parse_qs, urljoin, urlparse

import backoff
import googleapiclient.discovery
import googleapiclient.http
import pandas as pd
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from oauth2client.service_account import ServiceAccountCredentials


def colnum2str(n):
    """Transform a column index into the letter representation.
    """
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def colstr2num(col):
    """Transform a column letter into the index representation.
    """
    num = 0
    for c in col:
        if c in string.ascii_letters:
            num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return num


def url2id(url):
    """Returns the ID from a gdrive or gsheet url.
    """
    parsed_url = urlparse(url)
    # Returns id query parameter if exists
    qry = parsed_url.query
    if qry != '':
        parsed_qry = parse_qs(qry)
        if 'id' in parsed_qry:
            return ','.join(parsed_qry['id'])
    # Drop query parameters
    url = urljoin(url, parsed_url.path)
    last_part = basename(normpath(url))
    if last_part in ['view', 'edit']:
        return url2id(dirname(normpath(url)))
    else:
        return last_part


_sheet_services = {}  # Cache the Google Service
_drive_services = {}
_last_api_call = 0  # Last time the API was called
API_MIN_DELAY = 0.05  # Minimum delay between API calls
TRIES = 5  # Number of time to retries in case of HttpError
DELAY = 2  # Initial delay
BACKOFF = 3  # Exponential backoff
RAISE_ON_STATUS = (429, 502, 500)


def fatal_code(e):
    try:
        error_status = e.resp.status
    except AttributeError:
        return True
    return int(error_status) not in RAISE_ON_STATUS


def _delay_retry(func):
    """Decorator to delay and retry a function
    """
    global  _last_api_call
    time.sleep(max(0, API_MIN_DELAY - (time.time() - _last_api_call)))
    _last_api_call = time.time()
    @backoff.on_exception(
        backoff.expo, HttpError, max_tries=TRIES, giveup=fatal_code, base=DELAY, 
        factor=BACKOFF)
    def inner(*args, **kwargs):
        return func(*args, **kwargs)
    return inner


"""Monkey-patch `execute` method from `HttpRequest` object to include a 
minimum delay between API requests and to retry in case the selected error status.
"""
googleapiclient.http.HttpRequest.execute = _delay_retry(
    googleapiclient.http.HttpRequest.execute)


class GoogleSheet():
    """A class that represents a Googlesheet.

    A Googlesheet is represented by its metadata and its active sheet. Any
    requests (get_values, update, ...) are directed to the active sheet, 
    unless specified otherwise in the `range_` or `sheet_name` arguments. As a 
    Googlesheet is a dynamic object (it can be modified by a different user)
    the metadata are refreshed when data are requested if the elapsed time from
    last refresh is longer than `refresh_timeout` attribute.

    Attributes
    ----------
    metadata: dict
        Metadata of the Googlesheet.
    scopes : str
        Google Authentification scopes.
    num_retries : int
        Number of attempts when calling Google API.
    refresh_timeout: float
        Minumum time in seconds between 2 refresh of metadata for dynamic
        attributes.
    active_sheet : str
        Current active sheet (used when sheet name is omitted in the range
        arguments).
    id : str
        Sheet ID (retrieved from metadata).
    sheets : list of str
        Names of worksheets (retrieved from metadata).
    name : str
        Name of the Googlesheet (retrieved from metadata).
    active_shape : tuple
        Number of rows and columns of the active sheet.

    """
    DEF_SCOPES = ['https://spreadsheets.google.com/feeds',
                  'https://www.googleapis.com/auth/drive']
    MIN_REFRESH_TIMEOUT = 5

    def __init__(self, credentials, sheet_id=None, scopes=None, 
                 num_retries=3, refresh_timeout=10):
        """Object to represent a Google Sheet

        The actual object is wrapper around a sheet's
        `googleapiclient.discovery.Resource` object. It provides easy access
        to the most-used API call. If `sheet_id` is `None`, then a new 
        Googlesheet is created.

        Parameters
        ----------
        credentials : dict
            Dict of Google Credentials to be used for authentification.
        sheet_id : str, optional
            sheetId if accessing existing sheet. If `None` (default) then a new
            sheet is created. A newly created sheet is only visible to the
            credential's user until it is shared.
        scopes : iterable, optional
            Google authorization scope.
        num_retries : int, optional
            Number of attempts to call Google API before raising an exception.
        refresh_timeout : int, optional
            Time in seconds between 2 refresh of sheet metadata. If invalid or
            less than `GoogleSheet.MIN_REFRESH_TIMEOUT`, then the latter is used.

        Examples
        --------
        Open an existing sheet. The sheet must be shared to 
        `creds['client_email']` before.

        >>> sheet = GoogleSheet(
                creds, sheet_id='18aK01koZwea-re-xvmajPbKz1jjz5mtDyACo-7BrouE')
        >>> sheet.id
        '18aK01koZwea-re-xvmajPbKz1jjz5mtDyACo-7BrouE'
        >>> sheet.name
        'test2'
        >>> sheet.sheets
        ['test', 'another_sheet']
        >>> sheet.active_sheet  # default is first sheet.
        'test'
        >>> sheet.active_sheet = 'another_sheet'
        >>> sheet.active_sheet
        another_sheet

        Create a new Googlesheet. 

        >>> sheet = GoogleSheet(creds)
        >>> sheet.id
        '1dq35daf07ea-rIkNYa90=-dasdasdCo-g7Br1ouE'

        The sheet is only visible to `creds['client_email']`. It needs to be
        shared.

        >>> sheet.share('someone@grabtaxi.com', role='reader')

        Write data to the current active sheet.

        >>> sheet.update([[1, 2], [3, 4]], anchor_cell='B3')

        Add a new sheet.

        >>> sheet.add_sheet('new_sheet')

        Append data to 'new_sheet'.

        >>> sheet.append([[1, 4], [2, 3]], sheet_name = 'new_sheet')

        A sheet is iterable over the active sheet.

        >>> for s in sheet:
                print(s.get_values())

        Delete the sheet 'new_sheet'.

        >>> sheet.delete_sheet('new_sheet')

        Protect the sheet when working with it so nobody else can modify it
        during that time (except you and the owner).

        >>> with sheet.protect_range(warning_only=False) as s:
                val = s.get_values('B3:C4')
                newval = [[int(v) + 1 for v in row] for row in val]
                s.update(newval, anchor_cell='B3)

        If `warning_only=True`, the sheet can be modified, but a warning 
        windows popups when anyone is trying to modify the protected range.

        """
        if scopes is None:
            scopes = GoogleSheet.DEF_SCOPES
        self._scopes = scopes
        self._credentials = credentials
        self.num_retries = num_retries
        try:
            self.refresh_timeout = max(
                refresh_timeout, GoogleSheet.MIN_REFRESH_TIMEOUT)
        except TypeError:
            self.refresh_timeout = GoogleSheet.MIN_REFRESH_TIMEOUT
        # Hashable keys for saving service
        creds_id = tuple(sorted(credentials.values())) + tuple(scopes)
        try:
            self._service = _sheet_services[creds_id]
        except KeyError:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                self._credentials, scopes=self._scopes)
            self._service = googleapiclient.discovery.build(
                'sheets', 'v4', credentials=creds)
            _sheet_services[creds_id] = self._service
        if sheet_id is None:
            # Create a new sheet.
            req = self._service.spreadsheets().create(body={})
        else:
            req = self._service.spreadsheets().get(spreadsheetId=sheet_id)
        
        resp = req.execute(num_retries=self.num_retries)
        self._metadata = resp
        self._last_refresh = time.time()
        self.active_sheet = self.sheets[0]


    def __repr__(self):
        return f'GoogleSheet(credentials=..., sheet_id="{self.id}")'


    @property
    def metadata(self):
        """Sheet metadata.
        """
        self._update_metadata()
        return self._metadata


    @property
    def id(self):
        """SpreadsheetId.
        """
        return self._metadata['spreadsheetId']


    @property
    def name(self):
        """Sheet name (or title).
        """
        self._update_metadata()
        return self._metadata['properties']['title']


    @property
    def sheets(self):
        """List of sheetnames.
        """
        self._update_metadata()
        return [s['properties']['title'] for s in self._metadata['sheets']]


    @property
    def active_shape(self):
        """Number of rows and columns of the active sheet.
        """
        self._update_metadata(force=True)
        s_name = self.active_sheet
        for s in self._metadata['sheets']:
            if s['properties']['title'] == s_name:
                size = s['properties']['gridProperties']
                break
        return size['rowCount'], size['columnCount']


    def _update_metadata(self, force=False):
        """Update metadata if elapse time longer than refresh_timeout or 
        if force is `True`.
        """
        if force or (time.time() - self._last_refresh > self.refresh_timeout):
            req = self._service.spreadsheets().get(spreadsheetId=self.id)
            resp = req.execute(num_retries=self.num_retries)
            self._metadata = resp
            self._last_refresh = time.time()


    def __getitem__(self, key):
        """Return a new GoogleSheet with active_sheet set as the `key`.

        The key can be either an integer (starting at index 0), or the name of
        the sheet. A new object is returned, but the `_service` used is shared
        between the old and new instances.

        Parameters
        ----------
        key : str or int
            Name of the sheet or its position (0-based index).

        Returns
        -------
        A new `<GoogleSheet>` object with `key` as its `active_sheet`.

        """
        self._update_metadata()
        if not isinstance(key, str):
            key = self.sheets[key]
        if key not in self.sheets:
            raise LookupError(f'{key} is not a sheet')
        sheet = copy.copy(self)
        sheet._metadata = copy.deepcopy(self._metadata)
        sheet.active_sheet = key
        return sheet


    def __setattr__(self, name, value):
        """If attribute is active_sheet, then it checks if the sheet is an
        actual sheet.
        """
        if name == 'active_sheet':
            self._update_metadata()
        if name == 'active_sheet' and value not in self.sheets:
            raise ValueError(f'"{value}" is not a sheet.')
        self.__dict__[name] = value


    def _normalize_range(self, range_):
        """Default value for the range_ argument when None is provided, and 
        add sheetname with active_shape if sheet is not provided.
        """
        if range_ is None:
            range_ = self.active_sheet
        elif len(range_.split('!')) == 1 and (':' in range_):
            range_ = f'{self.active_sheet}!{range_}'
        return range_


    def _sheet_id(self, sheet_name):
        """List of sheetIds (not spreadsheetId).
        """
        if sheet_name is None:
            sheet_name = self.active_sheet
        for s in self._metadata['sheets']:
            if sheet_name == s['properties']['title']:
                sheet_id = s['properties']['sheetId']
                break
        return sheet_id


    def get_values(self, range_=None, render_as='FORMATTED_VALUE'):
        """Extract values of a range as a list of list.

        Empty rows or columns at the end are discarded. Empty rows at the 
        beginning are returned as empty lists. Empty columns on the left are
        return as list of ''. If `range_` is not provided or `None` then the 
        full sheet is read. If the sheetname is not provided in the `range_` 
        argument then the `active_sheet` is used.

        Parameters
        ----------
        range_ : str, optional
            Range to read in 'A1:B2' notation. The sheetname can also be 
            specified as 'Sheet2!A1:B2'. If the sheetname is not provided, 
            then the `active_sheet` is used. If `None` (default) then the full
            active sheet is read.
        render_as : {'FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA'}
            How to read the data. If 'FORMATTED_VALUE' then the value displayed
            to the user is returned. If 'UNFORMATTED_VALUE', then the actual 
            data is returned. If 'FORMULA', then the formula is returned.
        
        Returns
        -------
        List of list of str
            Data (as str) read from the Googlesheet.
        
        Examples
        --------
        >>> sheet.get_values()  # Returns all data from active sheet.
        >>> sheet.get_values(range_='C3:D10')  # Range from active_sheet.
        >>> sheet.get_values(range_='Sheet2!A1:B10')  # Range from other sheet.
        >>> sheet['Sheet2'].get_values()  # Specify the sheet.
        >>> sheet.get_values(range_='Sheet2')  # Same as above.

        """
        range_ = self._normalize_range(range_)
        req = self._service.spreadsheets().values().get(
            spreadsheetId=self.id, range=range_, valueRenderOption=render_as)
        return req.execute(num_retries=self.num_retries)['values']


    def get_values_as_df(self, range_=None, render_as='FORMATTED_VALUE',
                         header=True):
        """Extract values of a range as a `<pandas.DataFrame>`.
        
        Simple wrapper function around get_values.

        Parameters
        ----------
        range_ : str, optional
            Range to read in 'A1:B2' notation. The sheetname can also be 
            specified as 'Sheet2!A1:B2'. If the sheetname is not provided, 
            then the `active_sheet` is used. If `None` (default) then the full
            active sheet is read.
        render_as : {'FORMATTED_VALUE', 'UNFORMATTED_VALUE', 'FORMULA'}
            How to read the data. If 'FORMATTED_VALUE' then the value displayed
            to the user is returned. If 'UNFORMATTED_VALUE', then the actual 
            data is returned. If 'FORMULA', then the formula is returned.
        header : bool, optional
            Should the first row be considered as the DataFrame columns?
        
        Returns
        -------
        `<pandas.DataFrame>`
        """
        data = self.get_values(range_=range_, render_as=render_as)
        df = pd.DataFrame(data)
        if header:
            columns = df.iloc[0]
            df = df.iloc[1:].rename(columns=columns)
        df.fillna('', inplace=True)
        return df


    def update(self, data, anchor_cell='A1', input_type='USER_ENTERED'):
        """Sets values in a range of a spreadsheet.

        The `data` argument must be a table-like object (list of list of equal
        length, `<pandas.DataFrame>` or 2D `<numpy.Array>`). The data are 
        inserted row-wise, meaning that if `data` is a nested list, then each
        element of the list is considered as a row.

        Parameters
        ----------
        data : <pandas.DataFrame>, 2D <numpy.Array>, list of list
            Data to update into the spreadsheet. 
        anchor_cell : str, optional
            Where to update the data in the spreadsheet (top-left location).
        input_type : {'USER_ENTERED', 'RAW'}
            If 'USER_ENTERED' then the values are parsed as if the user typed
            them into the UI. If 'RAW', then the input are not parsed.
        
        Returns
        -------
        None. Update the data in the google sheet.

        Examples
        --------
        >>> data = [[1, 2], [3, 4]]
        >>> sheet.update(data)  # Update data in active sheet, in range 'A1:B2'
        >>> data = pd.DataFrame([[3, 4, 5], [6, 7, 8]], columns = ['A', 'B'])
        >>> sheet.update(data, anchor_cell='Sheet2!D4')
        """
        try:
            # For dataframe
            data = [data.columns.values.tolist()]+data.values.tolist()
        except AttributeError:
            try:
                data = data.tolist()  # For dataFrame or np.Array
            except AttributeError:
                pass  # Other
        nrow = len(data)
        ncols = {len(row) for row in data}
        if len(ncols) > 1:
            raise ValueError('data must be array-like.')
        ncol = ncols.pop()
        if len(anchor_cell.split('!')) > 1:
            sheet_name, anchor_cell = anchor_cell.split('!')
        else:
            sheet_name = self.active_sheet 
        col_letter = ''.join([l for l in anchor_cell if l.isalpha()])
        row_index = int(''.join([l for l in anchor_cell if l.isnumeric()]))
        row_last = row_index + nrow
        col_last = colnum2str(colstr2num(col_letter) + ncol)
        range_ = f'{sheet_name}!{anchor_cell}:{col_last}{row_last}'
        body = {
            'range': range_,
            'majorDimension': 'ROWS',
            'values': data 
        }
        req = self._service.spreadsheets().values().update(
            spreadsheetId=self.id, body=body, range=range_,
            valueInputOption=input_type
        )
        req.execute(num_retries=self.num_retries)


    def append(self, data, sheet_name=None, input_type='USER_ENTERED'):
        """Append data at the end the the sheet.

        When the data in the sheet is not a table then the exact location where
        the data is appended might be difficult to predict. It is therefore
        better to use this function only when the data in tabular form.

        Parameters
        ----------
        data : <pandas.DataFrame>, 2D <numpy.Array>, list of list
            Data to update into the spreadsheet.
        sheet_name : str, optional
            Which sheet to append the data to. If `None` (default) then the
            data is appended to the current active sheet.
        input_type : {'USER_ENTERED', 'RAW'}
            If 'USER_ENTERED' then the values are parsed as if the user typed
            them into the UI. If 'RAW', then the input are not parsed.

        Returns
        -------
        None. The data is appended to the sheet.
        """
        if sheet_name is None:
            sheet_name = self.active_sheet
        try:
            # For dataframe
            data = [data.columns.values.tolist()]+data.values.tolist()
        except AttributeError:
            try:
                data = data.tolist()  # For np.Array
            except AttributeError:
                pass  # Other
        body = {
            'range': sheet_name,
            'majorDimension': 'ROWS',
            'values': data
        }
        req = self._service.spreadsheets().values().append(
            spreadsheetId=self.id,
            range=sheet_name,
            valueInputOption=input_type,
            insertDataOption='OVERWRITE',
            includeValuesInResponse=False,
            body=body
        )
        req.execute(num_retries=self.num_retries)


    def delete_rows(self, start_index, end_index, sheet_name=None):
        """Delete entire rows from Googlesheet.

        Delete rows from `start_index` to `end_index` (inclusive). Index starts
        at 1 (as in Googlesheet UI). If the `sheet_name` is not specified then
        the rows are deleted from the current `active_sheet`.

        Parameters
        ----------
        start_index, end_index : int
            Rows with index between `start_index` and `end_index` (inclusive)
            are deleted. The indexes are starting from 1 (as in UI).
        sheet_name : str, optional
            Sheetname from which to delete rows. If `None` (default) then the
            rows are deleted from current `active_sheet`.

        Returns
        -------
        None. Rows are deleted from Googlesheet.

        """
        self._update_metadata()
        sheet_id = self._sheet_id(sheet_name)
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={
                'requests': [
                    {'deleteDimension': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': "ROWS",
                            'startIndex': int(start_index)-1,
                            'endIndex': int(end_index)
                            }
                    }}
                ]
            }
        )
        req.execute(num_retries=self.num_retries)


    def delete_batch_rows(self, rows_index, sheet_name=None):
        """Delete entire rows from Googlesheet.

        Delete rows with index `rows_index`. Row index starts at 1 (as in 
        Googlesheet UI). If the `sheet_name` is not specified then the rows are
        deleted from the current `active_sheet`. `rows_index` does not need to
        be consecutive indexes.

        Parameters
        ----------
       rows_index : iterable
            Indexes of row to delete. The indexes are starting from 1 
            (as in UI).
        sheet_name : str, optional
            Sheetname from which to delete rows. If `None` (default) then the
            rows are deleted from current `active_sheet`.

        Returns
        -------
        dict : 
            Mapping from old rows index to new rows index after the row
            deletion (deleted rows are mapped to `None`.)

        """
        self._update_metadata()
        sheet_id = self._sheet_id(sheet_name)
        rev_index = sorted([int(r) for r in rows_index], reverse=True)
        for s in self._metadata['sheets']:
            if s['properties']['sheetId'] == sheet_id:
                nrows = s['properties']['gridProperties']['rowCount']
                break
        old_rows_ix = [r for r in range(1, nrows + 1)]
        new_rows_ix = list(old_rows_ix)
        requests = []
        # Loop over chunk of consecutive indexes, and add a delete request.
        for _, g in groupby(enumerate(rev_index), lambda ix: -ix[0]-ix[1]):
            range_ixs = list(map(itemgetter(1), g))
            requests.append(
                {'deleteDimension': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': "ROWS",
                        'startIndex': min(range_ixs)-1,
                        'endIndex': max(range_ixs)
                        }
                    }
                }
            )
            # Keep track of deleted rows index.
            new_index = []
            for r in new_rows_ix:
                if r is None:
                    new_index.append(r)
                elif r < min(range_ixs):
                    new_index.append(r)
                elif r in range_ixs:
                    new_index.append(None)
                else:
                    new_index.append(r-len(range_ixs))
            new_rows_ix = new_index
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id, body={'requests': requests}
        )
        req.execute(num_retries=self.num_retries)
        self._update_metadata(force=True)
        return {o_ix:n_ix for o_ix, n_ix in zip(old_rows_ix, new_rows_ix)}
 

    @contextmanager
    def protect_range(self, range_=None, warning_only=True):
        """Context manager to protect range against other user modification.

        The range can be protected with a warning only or completely protected
        from any users modification (except from the spreadsheet owner).

        Parameters
        ----------
        range_ : str, optional
            Range to protect in 'A1:B2' notation. The sheetname can also be 
            specified as 'Sheet2!A1:B2'. If the sheetname is not provided, 
            then the `active_sheet` is used. If `None` (default) then the full
            active sheet is protected.
        warning_only : bool, optional
            If `true` (default) then the users are prompted a warning message
            when trying to modify the protected range, but still can modify
            it. If `false`, then any modification of the range is protected, 
            except from the sheet owner and credendential client email.
        
        Returns
        -------
        A `<GoogleSheet> object with active sheet set from `range_`.

        Examples
        --------
       >>> with sheet.protect_range(warning_only=False) as s:
       ...      # Only me and the sheet owner can modify the active_sheet.
       ...      # The protection is automatically released when exiting
       ...      # the `with` block
       ...      val = s.get_values()
       ...      # Increment each value
       ...      val2 = [[int(v) + 1 for v in row] for row in val]
       ...      s.update(val2)

        """
        
        try:
            protected_range_id = self.protect_range_permanent(
                range_=range_, warning_only=warning_only)
            yield self
        finally:
            if protected_range_id is not None:
                self.release_protected_range(protected_range_id)


    def protect_range_permanent(self, range_=None, warning_only=True):
        """Permanently protect a range against other user modification.

        The range can be protected with a warning only or completely protected
        from any users modification (except from the spreadsheet owner). The
        protection can be released using the `release_protected_range` method.

        Parameters
        ----------
        range_ : str, optional
            Range to protect in 'A1:B2' notation. The sheetname can also be 
            specified as 'Sheet2!A1:B2'. If the sheetname is not provided, 
            then the `active_sheet` is used. If `None` (default) then the full
            active sheet is protected.
        warning_only : bool, optional
            If `true` (default) then the users are prompted a warning message
            when trying to modify the protected range, but still can modify
            it. If `false`, then any modification of the range is protected, 
            except from the sheet owner and credendential client email.
        
        Returns
        -------
        The id the of the newly created protected range.

        """
        self._update_metadata(force=True)
        range_grid = self._range_to_index(range_=range_)
        request = {
            "addProtectedRange": {
                "protectedRange": {
                    "range": range_grid,
                    "description": "Protected by BPA",
                    "warningOnly": warning_only
                }
            }
        }
        if not warning_only:
            request['addProtectedRange']['protectedRange']['editors'] = {
                'users': [self._credentials['client_email']],
                'domainUsersCanEdit': False,
                'groups': []
            }
        body = {'requests': [request]}
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id, body=body
        )
        resp = req.execute(num_retries=self.num_retries)
        if resp is not None:
            protected_range_id = resp['replies'][0][
                'addProtectedRange']['protectedRange']['protectedRangeId']
        else:
            protected_range_id = None
        return protected_range_id


    def release_protected_range(self, protected_range_id):
        """Releases a range protection

        Parameters
        ----------
        protected_range_id : int
            The id of the protected range to release. Usually taken from the
            response of `protect_range_permanent` method.
        
        Returns
        -------
        None. The protection is released.
        
        """
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={
                'requests': [{
                    'deleteProtectedRange': {
                        'protectedRangeId': protected_range_id
                    }
                }]
            }
        )
        req.execute(num_retries=self.num_retries)


    def delete_sheet(self, sheet_name=None):
        """Delete a sheet from the spreadsheet.

        If the current active_sheet is delete, then the new active_sheet is
        set as the first sheet.

        Parameters
        ----------
        sheet_name: str, optional
            Sheetname to delete. If `None` (default) then the active sheet
            is deleted.

        Returns
        -------
        None. The sheet is deleted.

        Examples
        --------
        >>> sheet.delete()  # Delete active sheet.
        >>> sheet.delete('another sheet')  # Delete another shet.

        """
        sheet_id = self._sheet_id(sheet_name)
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={
                'requests': [{
                    'deleteSheet': {
                        'sheetId': sheet_id
                    }
                }]
            }
            )
        res = req.execute(num_retries=self.num_retries)
        self._update_metadata(force=True)
        # If active sheet is deleted, then new active sheet is the first one.
        if self.active_sheet == sheet_name:
            self.active_sheet = self.sheets[0]


    def add_sheet(self, sheet_name, row_count=1000, col_count=26):
        """Add a new sheet in the spreadsheet.

        The size of the new sheet can be specified with the `row_count` and
        `col_count` arguments.

        Parameters
        ----------
        sheet_name : str
            Name of the sheet to add.
        row_count, col_count : int, optional
            Number of rows and columns in the new sheet.

        Returns
        -------
        sheet_id : int
            sheetId of the newly added sheet.

        Examples
        --------
        >>> sheet.add_sheet('new_sheet')  # Add 'new_sheet' with default size.
        >>> sheet.add_sheet('another_sheet', 10, 5)  # Specify the dimension.
        
        """
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={
                "requests": [{
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": { 
                                "rowCount": row_count,
                                "columnCount": col_count
                            }
                        }
                    }
                }]
            }
        )
        resp = req.execute(num_retries=self.num_retries)
        self._update_metadata(force=True)
        sheet_id = resp['replies'][0]['addSheet']['properties']['sheetId']
        return sheet_id


    def share(self, email, role='writer', send_notif=False):
        """Share the Googlesheet to another user.

        Parameters
        ----------
        email : str
            Email adress to which the file is shared with.
        role : {'writer', 'reader', 'owner', 'organizer', 'fileOrganizer', 
                'commenter'}
            Role granted when sharing the document.
        send_notif : bool
            Whether an email notification is sent.
        
        Returns
        -------
        None. The document is shared.
        
        Examples
        --------
        >>> sheet.share('someone@grabtaxi.com', role='reader', send_notif=True)
        
        """
        drive = GoogleDrive(self._credentials)
        drive.share(self.id, email=email, role=role, 
                    send_notif=send_notif)


    def rename(self, new_name):
        """Rename the sheet

        Parameters
        ----------
        new_name : str
            The new spreadsheet name.
        
        Returns
        -------
        None. The spreadsheet name is modified.
        
        """
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={
                "requests": [{
                "updateSpreadsheetProperties": {
                    "properties": {"title": new_name},
                    "fields": "title",
                    }
                }]    
            }
        )
        req.execute(num_retries=self.num_retries)
        self._update_metadata(force=True)


    def format_range(self, format, range_=None):
        """Changes format of a range.

        Parameters
        ----------
        format : dict
            The format to apply. See https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/cells#CellFormat
            for representation of the format.
        range_ : str, optional
            Range to protect in 'A1:B2' notation. The sheetname can also be 
            specified as 'Sheet2!A1:B2'. If the sheetname is not provided, 
            then the `active_sheet` is used. If `None` (default) then the full
            active sheet is protected.
        
        Returns
        -------
        None. The new format is applied to the sheet.

        """
        self._update_metadata(force=True)
        range_grid = self._range_to_index(range_=range_)
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body={
                "requests": [{
                    "repeatCell": {
                        'range': range_grid,
                        'cell': {
                            'userEnteredFormat': format
                        },
                        'fields': 'userEnteredFormat'
                    }
                }]
            }
        )
        req.execute(num_retries=self.num_retries)
        self._update_metadata(force=True)


    def add_validation_from_list(
        self, values, range_=None, input_message=None, is_strict=True, 
        is_custome_ui=True):
        """Adds a data validation on a range
        
        Parameters
        ----------
        values : Iterable
            The allowed values for the data validation.
        range_ : str, optional
            The range to apply data validation in 'A1:B2' notation. The 
            sheetname can also be specified as 'Sheet2!A1:B2'. If the sheetname
            is not provided, then the `active_sheet` is used. If `None` 
            (default) then the data validation is applied to the full active
            sheet.
        input_message: str
            The message the user sees if they edit the range.
        is_strict: boolean
            if True value of validation cell can only one of element in values
        is_custome_ui: bolean
            if True validation cell will have boox form if user hoover at validation cell.
        
        Returns
        -------
        None. The data validation is added to the corresponding range
        
        """
        self._update_metadata(force=True)
        range_grid = self._range_to_index(range_=range_)
       
        options = [{"userEnteredValue": op} for op in values] 
        request = [
            {
                "setDataValidation": {
                    "range": range_grid,
                    "rule": {
                        "condition": {
                            "type": "ONE_OF_LIST",
                            "values": options
                        },
                    "inputMessage": input_message,         
                    "strict": is_strict,
                    "showCustomUi" : is_custome_ui
                    }
                }
            }
        ]
        req = self._service.spreadsheets().batchUpdate(
            spreadsheetId=self.id,
            body= {"requests": request}
        )
        req.execute(num_retries=self.num_retries)
        self._update_metadata(force=True)

    
    def _range_to_index(self, range_):
        """Transform a range into the corresponding indices.
        """
        range_ = self._normalize_range(range_)
        if len(range_.split('!')) < 2:
            sheet_name = self.active_sheet
            start_col_ix = None
            start_row_ix = None 
            end_col_ix = None
            end_row_ix = None
        else:
            sheet_name, range_ = range_.split('!')
            top_left, bottom_right = range_.split(':')
            top_left_row = ''.join([l for l in top_left if l.isnumeric()])
            top_left_col = ''.join([l for l in top_left if l.isalpha()])
            bottom_right_row = ''.join([l for l in bottom_right if l.isnumeric()])
            bottom_right_col = ''.join([l for l in bottom_right if l.isalpha()])
            
            if len(top_left_col) == 0:
                start_col_ix = None
            else:
                start_col_ix = colstr2num(top_left_col) - 1
            if len(top_left_row) == 0:
                start_row_ix = None
            else:
                start_row_ix = int(top_left_row) - 1
            if len(bottom_right_row) == 0:
                end_row_ix = None
            else:
                end_row_ix = int(bottom_right_row)
            if len(bottom_right_col) == 0:
                end_col_ix = None
            else:
                end_col_ix = colstr2num(bottom_right_col)

        sheet_id = self._sheet_id(sheet_name)
        range_grid = {
            "sheetId": sheet_id,
            "startRowIndex": start_row_ix,
            "endRowIndex": end_row_ix,
            "startColumnIndex": start_col_ix,
            "endColumnIndex": end_col_ix,
        }
        range_grid = {k:v for k,v in range_grid.items() if v is not None}
        return range_grid


class GoogleDrive():
    """Google Drive class.

    A GoogleDrive instance is using `googleapiclient.discovery.Resource` for
    querying Google API.

    Attributes
    ----------
    scopes : str
        Google Authentification scopes.
    num_retries : int
        Number of attempts when calling Google API  before raising an 
        exception.
    

    """
    DEF_SCOPES = ['https://spreadsheets.google.com/feeds',
                  'https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials, scopes=None, num_retries=3):
        """Create an instance of GoogleDrive.

        A GoogleDrive instance allows the user to easily manipulate files from
        a Google Drive (personal or shared). 

        Parameters
        ----------
        credentials : dict
            Dict of Google Credentials
        scopes : iterable, optional
            Google authorization scopes.
        num_retries : int, optional
            Number of attempts when calling Google API  before raising an 
            exception.
        
        Examples
        --------
        >>> drive = GoogleDrive(creds)
        >>> drive.list_children_id(
        ...     parent_ids='1GHFMwSvRg5NKw5zUNa1XQRQLZ-8362fQ')
        >>> drive.get_metadata('1GHFMwSvRg5NKw5zUNa1XQRQLZ-8362fQ')
        >>> drive.create_folder(
        ...     'a new test folder', '1GHFMwSvRg5NKw5zUNa1XQRQLZ-8362fQ')

        Download a file as a `<_io.BytesIO>` object.

        >>> f = drive.download('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')
        >>> f.read().decode('utf-8')  # text files
        >>> pd.read_excel(f)  # excel file

        Upload a file from a `<_io.BytesIO>` object.

        >>> newf = io.BytesIO(b'some new files')
        >>> f = io.BytesIO(b'this is some bytes')
        >>> file_id = drive.upload(
        ...     f, parent_id='1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW', 
        ...     name='upload_test.txt',mimetype='text/plain')
    
        """
        if scopes is None:
            self.scopes = list(GoogleDrive.DEF_SCOPES)
        else:
            self.scopes = list(scopes)
        
        self._credentials = credentials
        creds_id = tuple(sorted(credentials.values())) + tuple(self.scopes)
        # Reads the service from cache if it exists.
        try:
            self._service = _drive_services[creds_id]
        except KeyError:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(
                self._credentials, scopes=self.scopes)
            self._service = googleapiclient.discovery.build(
                'drive', 'v3', credentials=creds, cache_discovery=False)
            _drive_services[creds_id] = self._service
        self.num_retries = num_retries


    def __repr__(self):
        return f'GoogleDrive(credentials=...)'


    def get_metadata(self, file_id, fields=None):
        """Get file metadata.

        Parameters
        ----------
        file_id : str
            FileId from which metadata is returned.
        field : str, optional
            Comma separated list of fields to return. If `None` (default) then
            "kind", "id", "name", "mimeType" fields are returned.
        
        Returns
        -------
        dict of fields.

        Examples
        --------
        >>> drive.get_metadata('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')
        >>> drive.get_metadata(
        ...     '1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW', fields='kind,parents')
        """
        req = self._service.files().get(
            fileId=file_id, fields=fields, supportsAllDrives=True)
        return req.execute(num_retries=self.num_retries)


    def list_children_id(self, parent_id, drive_id=None):
        """ Get a list of all children fileId's of a folder.

        When `parent_id` is in a shared drive, then `drive_id` must also be
        provided. Otherwise, for folder in personal Google Drive, `drive_id`
        must be `None`.

        Parameters
        ----------
        parent_id : str
            The fileId from which to get the children.
        drive_id : str, optional
            driveId of a Team Drive. Must only be provided for Team Drive.
        
        Returns
        -------
        list of fileId.

        Examples
        --------
        >>> drive.list_children_id('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')

        """
        query = f'"{parent_id}" in parents and trashed = false'
        fields = 'files(id)'
        if drive_id is None:
            req = self._service.files().list(q=query, fields=fields)
        else:
            req = self._service.files().list(
                q=query, fields=fields, corpora='drive', driveId=drive_id,
                includeItemsFromAllDrives=True, supportsAllDrives=True)
        result = req.execute(num_retries=self.num_retries)
        return [ids['id'] for ids in result['files']]


    def list_children(self, parent_id, fields='id,name,mimeType', 
                      drive_id=None):
        """ Get a list of all children files's metadata from a folder.

        When `parent_id` is in a shared drive, then `drive_id` must also be
        provided. Otherwise, for folder in personal Google Drive, `drive_id`
        must be `None`.

        Parameters
        ----------
        parent_id : str
            The fileId from which to get the children.
        fields : str
            Comma separated list of fields to request.
        drive_id : str, optional
            driveId of a Team Drive. Must only be provided for Team Drive.
        
        Returns
        -------
        list of dict.

        Examples
        --------
        >>> drive.list_children('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')

        """
        query = f'"{parent_id}" in parents and trashed = false'
        fields = 'files(' + '),files('.join(fields.split(',')) + ')'
        if drive_id is None:
            req = self._service.files().list(q=query, fields=fields)
        else:
            req = self._service.files().list(
                q=query, fields=fields, corpora='drive', driveId=drive_id,
                includeItemsFromAllDrives=True, supportsAllDrives=True)
        result = req.execute(num_retries=self.num_retries)
        return result['files']

        
    def get_or_create_folder(self, folder_name, parent_id, drive_id=None, 
                             delay=1, unique_constraint=False):
        """Create a new folder if it does not exist and return its id.

        If one or more folders (file with mimeType 
        'application/vnd.google-apps.folder') with `folder_name` already exist
        then their `id` are returned. Otherwise a folder is created and its 
        `id` is returned. If `unique_constraint` is set to `True` then a
        `ValueError` is raised.

        Parameters
        ----------
        folder_name : str
            Name of the folder to create.
        parent_id : str
            FileId of the parent folder for the newly created folder.
        drive_id : str, optional
            driveId of a Team Drive. Must only be provided for Team Drive.
        delay : numeric
            Time in seconds to wait after creating a folder. Useful to avoid
            latency issue. If `None` or negative, then no delay is applied.
        unique_constraint : bool
            If `True`, then an error is raised if multiple files with the same
            names are retrieved.

        Returns
        -------
        tuple of str : 
        fileId's of the existing folders or the newly created folder.

        """
        mime_type = 'application/vnd.google-apps.folder'
        children = self.list_children(
            parent_id=parent_id, fields='id,name,mimeType', drive_id=drive_id)
        existing_folder_id = [f['id'] for f in children 
                              if f['name'] == folder_name 
                              and f['mimeType'] == mime_type]
        if len(existing_folder_id) == 0:
            # Create a new folder
            new_id = self.create_folder(
                folder_name=folder_name, parent_id=parent_id)
            if delay is not None and delay > 0:
                time.sleep(delay)
            return [new_id]
        else:
            if unique_constraint and len(existing_folder_id) > 1:
                raise ValueError('Multiple folder with the same name.')
            return existing_folder_id


    def create_folder(self, folder_name, parent_id):
        """Create a new folder in a Google Drive.

        Parameters
        ----------
        folder_name : str
            Name of the folder to create.
        parent_id : str
            FileId of the parent folder for the newly created folder.

        Returns
        -------
        str : fileId of the newly created folder.

        Examples
        --------
        >>> parent_id = '1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW'
        >>> new_f_id = drive.create_folder('a new folder', parent_id=parent_id)
        >>> new_f_id in drive.get_children_id(file_id=parent_id)
        True

        """
        file_metadata = {'name': folder_name, 'parents': [parent_id],
                         'mimeType': 'application/vnd.google-apps.folder'}
        req = self._service.files().create(body=file_metadata, fields='id', 
                                           supportsAllDrives=True)
        return req.execute(num_retries=self.num_retries)['id']


    def delete_file(self, file_id):
        """ Permanently delete a file from a GoogleDrive.

        Parameters
        ----------
        file_id : str
            FileId to delete.
        
        Returns
        -------
        None. The file is deleted.

        Examples
        --------
        Delete all files from a folder

        >>> files_id = drive.get_children_id(
        ...     '1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')
        >>> for file_id in files_id:
        >>>     drive.delete(file_id) 
        
        """
        req = self._service.files().delete(
            fileId=file_id, supportsAllDrives=True)
        req.execute(num_retries=self.num_retries)


    def share(self, file_id, email, role='writer', send_notif=False):
        """Share a file.

        Parameters
        ----------
        file_id : str
            FileId to share.
        email : str
            Email adress to which the file is shared with.
        role : {'writer', 'reader', 'owner', 'organizer', 'fileOrganizer', 
                'commenter'}
            Role granted when sharing the document.
        send_notif : bool
            Whether an email notification is sent.
        
        Returns
        -------
        None. The file is shared.
        
        Examples
        --------
        >>> drive.share('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW', 
        ...     'someone@grabtaxi.com', 'reader')

        """
        user_permissions = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        req = self._service.permissions().create(
            fileId=file_id, body=user_permissions, 
            sendNotificationEmail=send_notif, supportsAllDrives=True)
        req.execute(num_retries=self.num_retries)


    def download(self, file_id):
        """Download a file as a `<_io.BytesIO>` object.

        Parameters
        ----------
        file_id : str
            FileId of the file to download.
        
        Returns
        -------
        `<_io.BytesIO object>`.

        Examples
        --------
        >>> f = drive.download('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')
        >>> data = pd.read_excel(f)  # For excel file
        >>> data = pd.read_csv(f)  # For csv file
        >>> data = f.read().decode('utf-8)  # For text file

        Write the downloaded file to local disk.

        >>> with open('my new file.xlsx', 'wb') as newfile:
        ...     newfile.write(f.read())
        
        """
        req = self._service.files().get_media(fileId=file_id)  
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, req)
        done = False
        while done is False:
            _, done = downloader.next_chunk()  
        fh.seek(0)
        return fh


    def download_file(self, file_id, file_path):
        """Download a file to local location.

        Parameters
        ----------
        file_id : str
            FileId of the file to download.
        file_path : str
            Path to save the downloaded file
        
        Returns
        -------
        No return.

        Examples
        --------
        >>> f = drive.download('1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')
        
        """
        file_name = self.get_metadata(file_id, fields = 'name')['name']
        req = self._service.files().get_media(fileId=file_id)  
        fh = io.FileIO(f'{file_path}{file_name}', mode='w')
        downloader = MediaIoBaseDownload(fh, req)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))


    def upload(self, file, parent_id, name, mimetype, override=False):
        """Upload a file-like object to a Drive.

        Parameters
        ----------
        file : a file-like object
            File to upload
        parent_id : str
            FileId of the folder location for the upload.
        name : str
            Name of the file in GoogleDrive
        mimetype : str
            MimeType of the file to upload.

        Examples
        --------
        >>> f = io.BytesIO(b'some bytes.')
        >>> drive.upload(f, '1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW', 
        ...     'newfile.txt', 'text/plain')

        """
        if override:
            parent_metadata = self.get_metadata(parent_id)
            list_children_id = self.list_children_id(
                parent_id,
                drive_id=parent_metadata['driveId'])
            for obj_id in list_children_id:
                obj_metadata = self.get_metadata(obj_id)
                if obj_metadata['name'] == name:
                    self.delete_file(obj_id)
        body = {'name': name, 'mimeType': mimetype,
                'parents': [parent_id]}
        media = MediaIoBaseUpload(
            file, mimetype=mimetype, chunksize=1024*1024, resumable=True)
        req = self._service.files().create(
            body=body, media_body=media, fields='id', supportsAllDrives=True)
        res = req.execute(num_retries=self.num_retries)
        return res['id']


    def upload_file(self, filename, parent_id, name=None, mimetype=None, 
                    override=False):
        """Upload a file from local disk to google drive.

        Parameters
        ----------
        filename : str
            Name of the file to upload, including extension.
        parent_id :
            FileId of the folder location for the upload.
        name : str, optional
            Name of the file in GoogleDrive once upload. If `None` (default)
            then the name is taken from the base name of `filename`.
        mimetype : str, optional
            MimeType of the file to upload. If `None` (default), then the
            mimeType is guessed.
        
        Examples
        --------
        >>> drive.upload_file(
        ...     'mylocalfile.txt', '1tTom6OwYfscn3sRfZZ6YjAuM7mka4mpW')

        """
        if name is None:
            name = os.path.basename(filename)
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(name)
        if mimetype is None:
            mimetype = 'application/octet-stream'
        with open(filename, 'rb') as file:
            res = self.upload(file, parent_id, name, mimetype, override)
        return res


    def write_csv(self, df, parent_id, file_name, **kwargs):
        """Write a `pandas.DataFrame` into a Google as an csv file.
        
        Parameters
        ----------
        df : `pandas.DataFrame`
            DataFrame to write, including headers.
        parent_id : str
            File_id of the folder.
        file_name : str
            Name of the csv file.
        **kargs : 
            Additional keyword parameters passed to `pandas.to_csv`.
        
        Returns
        -------
        str : File id of the csv file.

        """
        output = io.BytesIO()
        output.write(df.to_csv(**kwargs).encode('utf-8'))
        file_id = self.upload(
            output, parent_id, file_name, 'text/csv')
        return file_id


    def write_excel(self, df, parent_id, file_name, date_format='YYYY-MM-DD', 
                    datetime_format='YYYY-MM-DD HH:MM:SS', **kwargs):
        """Write a `pandas.DataFrame` into a Google as an excel file.

        Parameters
        ----------
        df : `pandas.DataFrame`
            DataFrame to write, including headers.
        parent_id : str
            File_id of the folder.
        file_name : str
            Name of the Excel file.
        date_format : str, optional
            Format string for dates written into Excel file, passed to
            `pd.ExcelWriter`,  default 'YYYY-MM-DD'.
        datetime_format : str, optional
            Format string for datetime objects written into Excel file, passed
            to `pd.ExcelWriter`, default 'YYY-MM-DD HH:MM:SS'.
        **kwargs : 
            Additional keyword parameters passed to `pandas.to_excel`.
        
        Returns
        -------
        str : File id of the Excel file.

        """
        output = io.BytesIO()
        writer = pd.ExcelWriter(
            output, engine='xlsxwriter', date_format=date_format,
            datetime_format=datetime_format
        )
        df.to_excel(writer, **kwargs)
        writer.save()
        file_id = self.upload(
            output, parent_id, file_name, 'application/vnd.ms-excel')
        return file_id


    def read_excel(self, file_id, **kwargs):
        """Read an Excel file into a `pandas.DataFrame`
        
        Parameters
        ----------
        file_id : str
            File id to read.
        **kargs : 
            Additional keyword parameters passed to `pandas.read_excel`.
        
        Returns
        -------
        `pandas.DataFrame`

        """
        f =  self.download(file_id)
        df = pd.read_excel(f, **kwargs)
        return df


    def read_csv(self, file_id, **kwargs):
        """Read csv file into a `pandas.DataFrame`
        
        Parameters
        ----------
        file_id : str
            File id to read.
        **kargs : 
            Additional keyword parameters passed to `pandas.read_csv`.
        
        Returns
        -------
        `pandas.DataFrame`

        """
        f =  self.download(file_id)
        df = pd.read_csv(f, **kwargs)
        return df


    def copy(self, file_id, new_parent_id):
        """Copy an existing file to another location.

        The file is not actually copied. The `new_parent_id` is simpled added
        to the list of parents of the file. This means that both files have
        the same ID and hold a reference to the same object, and if one file is 
        modified, then the changes are also reflected to the other file.

        Parameters
        ----------
        file_id : str
            File id to copy.
        new_parent_id :
            Folder Id of the new location.
        
        Returns
        -------
        None. The file is copied.


        """
        req = self._service.files().update(
            fileId=file_id, addParents=new_parent_id,
            supportsAllDrives=True,
            fields='id')
        req.execute(num_retries=self.num_retries)


    def move(self, file_id, new_parent_id, previous_parents):
        """Move a file to a new location.

        Parameters
        ----------
        file_id : str
            File ID to move.
        new_parent_id : str
            Folder ID to move the file to.
        previous_parents : str
            Comma-separated list of parent IDs to remove.

        Returns
        -------
        None. The file is moved.

        """
        req = self._service.files().update(
            fileId=file_id, addParents=new_parent_id, 
            removeParents=previous_parents, 
            supportsAllDrives=True,
            fields='id, parents')
        req.execute(num_retries=self.num_retries)


    def rename(self, file_id, new_name):
        """Rename of file or folder.

        Parameters
        ----------
        file_id :
            File ID to rename.
        new_name : str
            New name of the file.
        
        Returns
        -------
        None. The file is renamed.

        """
        body = {'name': new_name}
        req = self._service.files().update(
            fileId=file_id, 
            body=body,
            supportsAllDrives=True,
            fields='id, name')
        req.execute(num_retries=self.num_retries)
