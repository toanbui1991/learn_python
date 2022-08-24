"""Module to interact with AWS - Wrapper around boto3 most common use-case.

Functions
---------
    get_ssm_parameter :
        Reads parameters from AWS SSM. Allows recursive parameters reads.

Classes
-------
    GrabS3 :
        Wrapper class around `boto3.s3` client. Provide functionalities to read
        and write files, list the keys, and delete objects.

"""
import io
import json
import sys

import boto3
import pandas as pd

_cached_ssm = {}


def _is_master(params):
    """Check if a SSM parameter is a parent parameter
    """
    if isinstance(params, list):
        for p in params:
            for k in ['path', 'safe', 'sub']:
                if k not in p:
                    return False
    else:
        return False
    return True


def get_ssm_parameter(param_name, recursive=True, region_name='ap-southeast-1'):
    """Recursively reads parameter from AWS SSM.
    
    The SSM client is cached, and retrieved for the same regions.

    param_name : str
        The name of parameter to read from SSM.
    recursivce : bool
        Wether to get the parameters recursively (only for Master parameters).
        Default True.
    region_name : str
        The name of the region associated with the client. 
        Default: 'ap-southeast-1'.

    Returns
    -------
    dict or list : The parameter reads from AWS SSM.

    """
    # Reads ssm from cache if possible.
    if region_name in _cached_ssm:
        ssm = _cached_ssm[region_name]
    else:
        # Creates a new ssm client, and caches it.
        ssm = boto3.client('ssm', region_name=region_name)
        _cached_ssm[region_name] = ssm
    params = json.loads(
            ssm.get_parameter(Name=param_name, WithDecryption=True)['Parameter']['Value'])
    if recursive and _is_master(params):
        final_params = {}
        for param in params:
            final_params[param['sub']] = get_ssm_parameter(
                param['path'], recursive=True, region_name=region_name)
    else:
        final_params = params
    return final_params


class GrabS3:
    """Wrapper class around S3 boto3 client.

    A GrabS3 object provides functionality for the common operations with
    Amazon S3. The authentification are retrieved from the AWS CLI.

    Attributes
    ----------
    bucket : str
        Name of the bucket.
    region_name : str
        Name of the region associated with the client.

    Examples
    --------
    >>> s3 = GrabS3('grab-bpa-datastore')
    >>> keys = s3.yield_keys(prefix='staging', suffix=('02.csv', '03.csv'))
    >>> keys # is a generator object. Use list(keys) to return a list.
    >>> df_list = []

    Read a list of keys in csv format.

    >>> for key in keys:
    ...     df_list.append(s3.read_csv(key, encoding='utf-8'))

    Read arbitrary file in `io` object.

    >>> f = s3.download(key='akey/to/download')

    Delete a list of objects.

    >>> s3.delete_objects(keys=['akey/todelete', 'anotherkey/todelet'])

    """
    def __init__(self, bucket, region_name='ap-southeast-1'):
        """Instantiates a GrabS3 object.

        Parameters
        ----------
        bucket : str
            Name of the bucket.
        region_name : str, optional
            Name of the region associated with the client. 
            Default: 'ap-southeast-1'.

        """
        self._s3 = boto3.client('s3', region_name=region_name)
        self.bucket = bucket


    def __repr__(self):
        return f"GrabS3(bucket='{self.bucket}')"


    def yield_keys(self, prefix='', suffix=''):
        """Yield keys in an S3 bucket.

        Generator that yields keys from the S3 bucket. Only keys that match
        the prefix and suffix (if provided) are returned. Largely inspired from 
        https://alexwlchan.net/2019/07/listing-s3-keys/.
        
        Parameters
        ----------
        prefix : str or tuple of str, optional
            Only fetch objects whose keys start with these prefixes.
        suffix : str or tuple of str, optional
            Only fetch objects whose keys end with these suffixes.

        Returns
        -------
        Generator of bucket keys.

        """
        kwargs = {'Bucket': self.bucket}
        if isinstance(prefix, str):
            prefixes = (prefix, )
        else:
            prefixes = prefix
        paginator = self._s3.get_paginator('list_objects_v2')
        for key_prefix in prefixes:
            kwargs['Prefix'] = key_prefix
            for page in paginator.paginate(**kwargs):
                try:
                    contents = page['Contents']
                except KeyError:
                    continue
                for obj in contents:
                    key = obj['Key']
                    if key.endswith(suffix):
                        yield key


    def download(self, key):
        """Download a S3 object as `io_BytesIO`.

        Parameters
        ----------
        key : str
            Key of the object to download.

        Returns
        -------
        `_io.BytesIO` object.

        """
        obj = self._s3.get_object(Bucket=self.bucket, Key=key)
        file_obj = io.BytesIO(obj ['Body'].read())
        return file_obj


    def read_csv(self, key, **kwargs):
        """Read a csv S3 object as a `pandas.DataFrame`.

        Parameters
        ----------
        key : str
            Key of the object to read.
        **kargs : 
            Additional keyword parameters passed to `pandas.read_csv`.

        Returns
        --------
        `pandas.DataFrame`

        """
        f = self.download(key)
        df = pd.read_csv(f, **kwargs)
        return df


    def read_excel(self, key, **kwargs):
        """Read an Excel S3 object as a `pandas.DataFrame`

        Parameters
        ----------
        key : str
            Key of the object to read.
        **kargs : 
            Additional keyword parameters passed to `pandas.read_excel`.

        Returns
        --------
        `pandas.DataFrame`

        """
        f = self.download(key)
        df = pd.read_excel(f, **kwargs)
        return df


    def delete_objects(self, keys):
        """Delete an S3 object.

        Parameters
        ----------
        key : str
            Key of the object to delete
        
        Returns
        -------
        None.

        """
        if isinstance(keys, str):
            keys = (keys, )
        objects = [{'Key': key} for key in keys]
        self._s3.delete_objects(Bucket=self.bucket, Delete={'Objects':objects})


    def upload(self, file, file_name):
        """Uploads a binary file to a S3 bucket.

        Parameters
        ----------
        file : Byte
            The file to upload on S3.
        file_name : str
            The filename, including prefix.
        
        Returns
        -------
        None. The file is uploaded on S3.

        """
        self._s3.put_object(Body=file, Bucket=self.bucket, Key=file_name)


    def write_csv(self, df, file_name, **kwargs):
        """Writes a `pandas.DataFrame` into a bucket as a csv file.

        Parameters
        ----------
        df : `pandas.DataFrame`
            The data to upload to S3.
        file_name : str
            The filename, including its prefix.
        **kwargs :
            Additional keyword parameters passed to `pd.DataFrame.to_csv`.
        
        Returns
        -------
        None. The DataFrame is uploaded on S3.
        
        """
        output = io.BytesIO()
        output.write(df.to_csv(**kwargs).encode('utf-8'))
        self.upload(output.getvalue(), file_name)


    def write_excel(self, df, file_name, date_format='YYYY-MM-DD', 
                    datetime_format='YYYY-MM-DD HH:MM:SS', **kwargs):
        """Writes a `pandas.DataFrame` into a bucket as a Excel file.

        Parameters
        ----------
        df : `pandas.DataFrame`
            The data to upload to S3.
        file_name : str
            The filename, including its prefix.
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
        None. The DataFrame is uploaded on S3.
        
        """
        output = io.BytesIO()
        writer = pd.ExcelWriter(
            output, engine='xlsxwriter', date_format=date_format,
            datetime_format=datetime_format
        )
        df.to_excel(writer, **kwargs)
        writer.save()
        self.upload(output.getvalue(), file_name)
