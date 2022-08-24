"""Module to interact with internal BPA API's.

Classes
-------
    Message :
        Utility class to represent a request-response cycle to API's. You
        should never directly instantiate a `Message` object.
    BatMan :
        Class used to send requests to BatMan, and check the status.

"""
import asyncio
import base64
import datetime
import json
import os
import reprlib
import time
import urllib
from collections import Counter, Mapping, namedtuple

import aiohttp
import numpy as np
import pandas as pd
import requests
from aiohttp import web

SERVERS = {
    'staging': 'https://staging.grab-bat.net',
    'vn': 'https://vn-data.grab-bat.net',
    'id': 'https://id-data.grab-bat.net',
    'sg': 'https://sg-data.grab-bat.net',
    'my': 'https://my-data.grab-bat.net',
    'ph': 'https://ph-data.grab-bat.net',
    'kh': 'https://kh-data.grab-bat.net',
    'th': 'https://th-data.grab-bat.net'
}


COUNTRIES = {
    'vietnam': 'vn',
    'indonesia': 'id',
    'singapore': 'sg',
    'malaysia': 'my',
    'philippines': 'ph',
    'cambodia': 'kh',
    'thailand': 'th'
}


RUNNING_STATUS = ['running']
COMPLETE_STATUS = ['success', 'failed', 'error']
FAILED_STATUS = ['failed', 'timeout', 'invalid response', 'error']
SUCCESS_STATUS = ['success']
MIN_DELAY = 5
REQUEST_TYPES = ['report', 'source', 'job']


class Message:
    """Class to represent a request-response cycle to Batman API.

    Attributes
    ----------
    type : {'source', 'report', 'job'}
        Type of the request.
    id : str
        Report or source ID.
    data : dict
        Request data.
    status : str
        Request status.
    status_code : int
        Response status code
    response : dict
        Response.
    created_at : float
        Time of creation of the request.

    """
    def __init__(self, type, id, data, status, status_code, response):
        """Instantiate a Message object.

        Parameters
        ----------
        type : {'source', 'report'}
            Type of the request.
        id : str
            Report or source ID.
        data : dict
            Request data.
        status : str
            Request status.
        status_code : int
            Response status code
        response : dict
            Response.
        
        Returns
        -------
        A `Message` object.

        """
        self.type = type
        self.id = id
        self.data = data
        self.status = status
        self.status_code = status_code
        self.response = response
        self.created_at = time.time()


    def __repr__(self):
        return f'<{self.type}_id={self.id}, status={self.status}>'


    def is_complete(self):
        """Check if the request is complete.
        """
        return self.status in COMPLETE_STATUS


    def is_running(self):
        """Check if the request is still running.
        """
        return self.status not in COMPLETE_STATUS


    @property
    def identifier(self):
        """Return the request identifier.

        """
        return self.response.get('identifier', None)


    @property
    def output_name(self):
        """Return request output_name. 

        A request identifier is a UUID genereated by BatMan for each request
        and is used as a prefix for the filename.
        
        """
        try:
            return self.response.get('data', None).get('outputName', None)
        except AttributeError:
            return None
    

class BatMan:
    """Class used to send requests to BatMan API.

    Attributes
    ----------
    url : str
        URL of BatMan server.
    requests : list of `Message` objects.
        Requests sent to BatMan

    Examples
    --------

    >>> mytoken = 'jdoij19djimp9283yrqmcnp'  # must be copied from BatMan UI
    >>> batman = BatMan('staging', mytoken)
    >>> data1 = {'sourceNamePostfix': 'test1', 'other_param': 'somevalue'}
    >>> data2 = {'sourceNamePostfix': 'test2', 'other_param': 'someothervalue'}

    Send 2 requests to BatMan. 

    >>> batman.send_request(request_type='source', request_id=1, data=data1)
    >>> batman.send_request(request_type='source', request_id=1, data=data2)

    Update requests status every 30 seconds for maximum 600 seconds.

    >>> batman.update_status_until_complete(
            delay=30, timeout=600, verbose=True)


    """
    def __init__(self, server, token):
        """Instantiate a BatMan object.

        A BatMan object can send requests (for source or report) to BatMan and
        check the status of these requests. 

        Parameters
        ----------
        server : str
            Country Name, 'Staging', or 2-letters country abbreviation. 
        token : str
            Token obtained through BatMan UI.
        
        Returns
        -------
        A BatMan object.

        """
        self._token = token
        server=server.lower()
        server = COUNTRIES.get(server, server)
        self.url = SERVERS[server]
        self.requests = []


    def _headers(self):
        """Headers to be included in requests to Batman.
        """
        return {'x-access-token': self._token}
    

    def _url(self, request_type,  request_id):
        """Construct URL 
        """
        pieces = (self.url, 'event', f'{request_type}s', str(request_id))
        return '/'.join(s.strip('/') for s in pieces)


    def _status_url(self, request_type, request_id, identifier):
        """URL to check source status.
        """
        pieces = (
            self.url, 'event', f'{request_type}s', str(request_id), 'status', 
            identifier
        )
        return '/'.join(s.strip('/') for s in pieces)


    def send_request(self, request_type, request_id, data=None):
        """Send a request to Batman.

        Parameters
        ----------
        request_type : {'report', 'source'}
            The type of request to send.
        request_id : int
            Id of the request.
        data : dict
            Parameters sent with the request.
        
        Returns
        -------
        None. The request and response are appended to the `request` attribute.

        """
        if request_type not in REQUEST_TYPES:
            raise ValueError(f'`request_type` must be one of {REQUEST_TYPES}')
        url = self._url(request_type, request_id)
        resp = requests.post(url, headers=self._headers(), data=data)
        try:
            content = json.loads(resp.content)
        except ValueError:
            content = {}
        status_code = resp.status_code
        status = 'running' if content.get('status') == 'running' else 'failed'
        self.requests.append(
            Message(
                request_type, request_id,  data, status, status_code, 
                content
            )
        )


    def update_status(self):
        """Update status for all running requests.

        """
        for request in self.requests:
            if request.is_running():
                request_id = request.id
                identifier = request.identifier
                if identifier is None:
                    continue
                request_type = request.type
                url = self._status_url(request_type, request_id, identifier)
                response = requests.get(url, headers=self._headers())
                try:
                    status = json.loads(response.content)['status'].lower()
                except (ValueError, AttributeError):
                    raise ValueError('invalid response.')
                request.status = status.lower()


    def update_status_until_complete(self, delay, timeout, verbose=False):
        """Update requests status until all requests are completed or failed.

        Parameters
        ----------
        delay : float
            Delay in seconds between call to API. If `delay` is less MIN_DELAY,
            then MIN_DELAY is used.
        timeout : float
            Time in seconds before timeout.
        verbose : bool
            If `True`, then the progress is printed.
        
        Returns
        -------
        None. Update `status` of `requests`.  

        """
        delay = max(delay, MIN_DELAY)
        start_time = time.time()
        if verbose:
            print(f'Starting status update with a delay of {delay} seconds')

        while True:
            if verbose:
                print('Updating status...')
            self.update_status()
            if verbose:
                n_req_run = len(
                    [req for req in self.requests if req.is_running()])
                print(f'    {len(self.requests)-n_req_run} complete requests')
                print(f'    {n_req_run} running requests')
            if self.is_complete():
                if verbose:
                    print('All requests are completed.')
                break
            if (time.time()-start_time) > timeout:
                if verbose:
                    n_req_run = len(
                        [req for req in self.requests if req.is_running()])
                    print('Timeout.')
                    print(f'    {len(self.requests)-n_req_run} complete requests')
                    print(f'    {n_req_run} running requests')
                break
            time.sleep(delay)


    def is_complete(self):
        """Return True if all requests are completed (successfully or not)
        """
        return all([req.is_complete() for req in self.requests])


    def resend_failed_requests(self, timeout=None):
        """Resend failed or timeout requests.

        Failed requests are resent to BatMan API. If `timeout` is larger than
        zero, then requests which are not completed after `timeout` seconds are
        considered as failed and resent.

        Parameters
        ----------
        timeout : float
            Time in seconds to consider a running requests as failed.

        """
        if timeout is not None and timeout > 0:
            now = time.time()
            for req in self.requests:
                is_timeout = now - req.created_at > timeout
                if (req.status in RUNNING_STATUS) and is_timeout:
                    req.status = 'timeout'
            for req in self.requests:
                if req.status in FAILED_STATUS:
                    self.send_request(req.type, req.id, req.data)


def _is_valid_url_part(x):
    """Check if x can be used as a valid url part.
    
    Only alphanumeric, `-` or `_` characters are excepted.
    
    Parameters
    ----------
        x : str
    
    Returns
    -------
        bool
        True if `x` is not an empty string and has only alphanumeric, '-` or 
        `_` characters. False otherwise.
    
    """
    if len(x) == 0:
        return False
    valid_chars = ['_', '-']
    for letter in x:
        if letter.isalnum() or letter in valid_chars:
            continue
        else:
            return False
    return True



def _valid_structure(body, struct):
    """Check if a dictionary follow the structure.

    Copied from https://stackoverflow.com/a/45812573.

    Parameters
    ----------
    struct : dict
        A dictionary with elements are types
    body : dict
        A dictionary
    
    Returns
    -------
    bool. `True` if body follows the same structure as struct
    """
    if isinstance(struct, dict) and isinstance(body, dict):
        # struct is a dict of types or other dicts
        return all(k in body and _valid_structure(body[k], struct[k]) 
                   for k in struct)
    if isinstance(struct, list) and isinstance(body, list):
        # struct is list in the form [type or dict]
        return all(_valid_structure(c, struct[0]) for c in body)
    elif isinstance(struct, type):
        # struct is the type of conf
        return isinstance(body, struct)
    else:
        # struct is neither a dict, nor list, not type
        return False

class ServiceMessage:
    """A class to represent a single message to BPA Service API.

    Attributes
    ----------
    url : str
        The url to send the message to.
    body : dict or str
        Body of the message. The actual format depends on the `message_type`.
    status : str
        Status of the message.
    response : dict
        Response from BPA Service API.
    response_code : int
        Code of the response.
    created_at : str
        Timestamp when the message is created (this is not the time when 
        the message is sent.).
    """
    def __init__(self, url, body):
        self.url = url
        self.body = body
        self.status = 'pending'
        self.response = dict()
        self.response_code = None
        self.created_at = time.time()
    

    def __str__(self):
        return f'<ServiceMessage, status="{self.status}">'
    

    def __repr__(self):
        return f'ServiceMessage(url={self.url}, body={self.body})'


class ServiceAPI:
    """Class to interact with the BPI Service API.

    Atributes
    ---------
    base_url : str
        The base url to send request to.
    message_type : str {'sms', 'app', 'email'}
        Type of message to send.
    template_name : str
        Name of the template or None if we send full message.
    messages : list
        List of `<ServiceMessage>`

    Examples
    --------
    >>> service = ServiceAPI('email')

    Add 3 messages. The messages are not yet sent. For email, recipient_type
    and recipient_id are free fields (do use meaningful names as their are 
    stored in log database). For sms or app, recipient_type must be either
    'passenger' or 'driver' and recipient_id is the `partner_user_safe_id` of
    the recipient.

    >>> service.add_message(
    ...     recipient_type='myself', 
    ...     recipient_id=2, 
    ...     body={
    ...         'from':'tibor.frossard@grab-bat.net', 
    ...         'to': 'tibor.frossard@grabtaxi.com', 
    ...         'body': {'html':'Test email'}, 
    ...         'subject': 'Test'}
    ... )
    >>> service.add_message(
    ...     recipient_type='myself@gmail', 
    ...     recipient_id=2, 
    ...     body={
    ...         'from':'tibor.frossard@grab-bat.net', 
    ...         'to': 'tibor.frossard@gmail.com', 
    ...         'body': {'html':'Test email'}, 
    ...         'subject': 'Test'}
    ... )
    >>> for _ in range(10):
    ...     service.add_message(
    ...         recipient_type='forbidden', 
    ...         recipient_id=2, 
    ...         body={
    ...             'from':'tibor.frossard@grab-bat.net', 
    ...             'to': 'khoa.luu@grabtaxi.com', 
    ...             'body': {'html':'Test email'}, 
    ...             'subject': 'Test'})

    Inspect the messages queue before sending.

    >>> service.to_df().to_clipboard(excel=True)

    Send the messages asyncronously. Only the message to 
    tibor.frossard@grabtaxi.com is sent.

    >>> service.send_messages(verbose=True)
    Sending 12 email...
        email #04 sent. API response: forbidden
        email #02 sent. API response: forbidden
        email #07 sent. API response: forbidden
        email #09 sent. API response: forbidden
        email #08 sent. API response: forbidden
        email #03 sent. API response: forbidden
        email #10 sent. API response: forbidden
        email #06 sent. API response: forbidden
        email #05 sent. API response: forbidden
        email #11 sent. API response: forbidden
        email #12 sent. API response: forbidden
        email #01 sent. API response: success

    """
    MESS_TYPES = ('email', 'app', 'sms')
    STATUS_MAPPING = {
        200: 'success',
        204: 'success',
        400: 'invalid',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'invalid_template',
        429: 'api_limit',
        500: 'server_error'
    }
    TIMEOUT = aiohttp.ClientTimeout(total=120)
    MAX_CONCURRENCY = 10
    APP_INBOX_STRUCT = {
        'title': str,
        'message': {
            'content': str
        },
        'category': {'text': str}
    }
    APP_PUSH_STRUCT = {
        'title': str
    }
    EMAIL_STRUCT = {
        'subject': str,
        'body': {'html': str},
        'from': str,
        'to': str
    }
    SMS_STRUCT = {
        'content': str
    }
   
    def __init__(self, message_type, template_name=None):
        """Instantiate a ServiceAPI object.

        The authentication is read from the environment variables `API_USER` 
        and `API_PASS`. Use `setx API_USER my_user_name` on the command line
        to set the environment variables (you might need to restart the command
         line afterwards.) 

        Parameters
        ----------
        message_type : str {'email', 'app', 'sms'}
            Type of message to send.
        template_name : str
            Name of the template to use. If `None` (default), then no 
            template is used, and the full message needs to be provided.

        Returns
        -------
        A `ServiceAPI` object.

        """
        self._base_url = 'https://bpa-api.grab-bat.net'
        if message_type not in self.__class__.MESS_TYPES:
            raise ValueError(
                f'"message_type" must be one of {self.__class__.MESS_TYPES}')
        self._message_type = message_type
        # TODO Check if template_name is valid
        self._template_name = template_name
        self._messages = []
        user = os.environ.get('API_USER')
        password = os.environ.get('API_PASS')
        if user is None or password is None:
            raise OSError(
            '"API_USER" and "API_PASS" must be set as environment variables.')
        self._token = (
            base64
            .b64encode(f'{user}:{password}'.encode('utf-8'))
            .decode('utf-8')
        )


    def __str__(self):
        status = Counter(mess.status for mess in self.messages) 
        if len(status) > 0:
            str_status = (
                ' (' + ', '.join(f'{v} {k}' for k, v in status.items()) + ')'
                )
        else:
            str_status = ''
        return (f'<{self.message_type.capitalize()} client '
                f'with {len(self.messages)} messages{str_status}>')


    def __repr__(self):
        return f'ServiceAPI({self.message_type}, {self.template_name})'


    @property
    def message_type(self):
        """Get or set message_type.

        The message_type can only be modified when the queue is empty.

        """
        return self._message_type


    @message_type.setter
    def message_type(self, value):
        if self.queue_size() > 0:
            raise AttributeError(
                'readonly attribute when the message queue is non-empty.'
            )
        self._message_type = value


    @property
    def template_name(self):
        """Get or set the current template_name.

        The template_name can only be modified when the message queue is empty.

        """
        return self._template_name


    @template_name.setter
    def template_name(self, value):
        if self.queue_size() > 0:
            raise AttributeError(
                'readonly attribute when the message queue is non-empty.'
            )
        self._template_name = value


    @property
    def messages(self):
        """Get the list of messages from the message queue.

        The messages cannot be modified directly. Use the `add_message`
        method to add a new message. If you need to modify or remove a message
        from the queue create a new `ServiceAPI` instance.

        """
        return self._messages


    @messages.setter
    def messages(self, value):
        raise AttributeError(
            'readonly attribute. Use `add_message` method to add messages.'
        )
    
    @property
    def base_url(self):
        """Get the base_url.

        The base_url cannot be modified directly. 

        """
        return self._base_url


    @base_url.setter
    def base_url(self, value):
        raise AttributeError(
                'readonly attribute'
            )


    def _validate_body(self, body):
        """Validate the body of the message based on message_type and template.

        Raise a ValueError exception in case the body is not valid and return
        `None` otherwise.

        """
        if not isinstance(body, Mapping):
            raise TypeError('`body` must be a dict or mapping.')
        if self.template_name is not None:
            if 'parameters' not in body:
                raise ValueError(
                    '`body` must have a "parameters" key for template.')
        elif self.message_type == 'sms':
           if not _valid_structure(body, self.__class__.SMS_STRUCT):
               raise ValueError(
            f'"body" must follow the structure: {self.__class__.SMS_STRUCT}')
        elif self.message_type == 'email':
            if not _valid_structure(body, self.__class__.EMAIL_STRUCT):
               raise ValueError(
            f'"body" must follow the structure: {self.__class__.EMAIL_STRUCT}')
        elif self.message_type == 'app':
            keys = set(body.keys()).intersection(['push', 'inbox'])
            if len(keys) == 0:
                raise ValueError(
                        '`body` must have a "push" or "body" key.')
            if 'push' in keys:
                if not _valid_structure(body['push'], 
                                        self.__class__.APP_PUSH_STRUCT):
                    msg = (
                        f'"body" must follow the structure: '
                        f'{self.__class__.APP_PUSH_STRUCT}')
                    raise ValueError(msg)
            if 'inbox' in keys:
                if not _valid_structure(body['inbox'], 
                                        self.__class__.APP_INBOX_STRUCT):
                    msg = (
                        f'"body" must follow the structure: '
                        f'{self.__class__.APP_INBOX_STRUCT}')
                    raise ValueError(msg)


    def _url(self, recipient_type, recipient_id):
        """Create URL.

        """
        recipient_id = str(recipient_id)
        recipient_type = str(recipient_type)
        if not _is_valid_url_part(recipient_id):
            raise ValueError('"recipient_id" is not a valid URL part.')
        if not _is_valid_url_part(recipient_id):
            raise ValueError('"recipient_type" is not a valid URL part.')
        if self.template_name is None:
            url_comp = [
                self.base_url, 'message', self.message_type, recipient_type,
                recipient_id
            ]
        else:
            url_comp = [
                self.base_url, 'message', 'template', self.message_type, 
                self.template_name, recipient_type, recipient_id
            ]
        return '/'.join(url_comp)


    def _headers(self):
        """Headers to be included in the http requests to BPA Service API.
        """
        return {'Authorization': f'Basic {self._token}'}

    

    def queue_size(self):
        """Number of messages in the queue.

        """
        return len(self.messages)


    def add_message(self, recipient_type, recipient_id, body):
        """Add a message to the queue.

        The message is not yet sent, it is simply added to the queue.

        Parameters
        ----------
        recipient_type : str
            Type of recipient. For email this is a free field for logging
            purpose but it is recommended to use a meaningful value. 
            For example: 'driver', 'passenger', 'merchant', 'external'.
        recipient_id : str
            Id of the recipient. For email this is a free field for logging
            purpose, but it is recommended to use a meaningful value.
            For example: driver_id, passenger_id, merchant_id.
        body : dict or str
            Body of the message. The format of the body depends on the type
            of message.

        Returns
        -------
        None. The message is added to the message queue.

        """
        if (self.message_type in ('sms', 'app') 
                and recipient_type not in ('passenger', 'driver')):
            msg = (f'"recipient_type" must be "passenger" or "driver" '
                   f'for {self.message_type}')
            raise ValueError(msg)
        self._validate_body(body)
        url = self._url(str(recipient_type), str(recipient_id)) 
        self.messages.append(ServiceMessage(url, body))

    async def _send_message(self, mess, mess_ix, semaphore, verbose):
        """Send a single message
        """
        cls = self.__class__
        l = len(str(self.queue_size())) + 1
        async with semaphore:
            async with aiohttp.ClientSession(
                headers=self._headers(), timeout=cls.TIMEOUT) as session:
                try:
                    async with session.post(mess.url, json=mess.body) as resp:
                        response = await resp.text()
                        try:
                            mess.response = json.loads(response)
                        except json.decoder.JSONDecodeError:
                            mess.response = response
                        mess.response_code = resp.status
                        mess.status = cls.STATUS_MAPPING.get(
                            resp.status, 'unknown')
                except aiohttp.ClientError:
                    mess.status = 'server_error'
                except asyncio.TimeoutError:
                    mess.status = 'timeout_error'
                  
                if verbose:
                    print(
                        f'    {self.message_type} #{str(mess_ix).zfill(l)} sent.',
                        f'API response: {mess.status}', sep=' ')

    def send_messages(
        self, status=('pending', 'server_error', 'timeout_error', 'api_limit'), 
        verbose=False):
        """Send messages concurrently to BPA Service API.

        Only messages with the corresponding status are sent.

        Parameters
        ----------
        status : str or container of str
            Only messages with these status are sent to BPA Service API.
        verbose : bool
            Whether to print the progress

        Returns
        -------
        None. The messages are sent to BPA Service API, and the responses are 
        recorded in the corresponding message.

        """
        if isinstance(status, str):
            status = (status, )
        messages = [mess for mess in self.messages if mess.status in status]
        n_messages = len(messages)
        if verbose:
            print(f'Sending {n_messages} {self.message_type}...')
        if n_messages != 0:
            semaphore = asyncio.Semaphore(self.__class__.MAX_CONCURRENCY)
            loop = asyncio.get_event_loop()
            tasks = asyncio.gather(
                *(self._send_message(m, i, semaphore, verbose) 
                  for i,m in enumerate(messages, 1))
            )
            loop.run_until_complete(tasks)

    
    def to_df(self):
        """Generate a DataFrame out of the message queue.

        Returns
        -------
        `pandas.DataFrame`

        """
        if self.queue_size() == 0:
            return pd.DataFrame()
        df = pd.DataFrame([mess.body for mess in self.messages])
        df['message_type'] = self.message_type
        df['template_name'] = self.template_name
        df['url'] = [mess.url for mess in self.messages]
        df['response_code'] = [mess.response_code for mess in self.messages]
        df['status'] = [mess.status for mess in self.messages]
        date_fmt = '%Y-%m-%d %H:%M:%S'
        df['created_at'] = [
            datetime.datetime.fromtimestamp(mess.created_at).strftime(date_fmt) 
            for mess in self.messages
        ]
        return df


    def yield_templates(self, name=None):
        """Yield existing templates from BPA Service API.

        Parameters
        ----------
        name : str
            Use to filter templates with similar name. If `None`, then all
            templates for the instance `message_type` are returned.

        Returns
        -------
        An iterator over the templates.

        """
        params = {'page':1, 'pagesize':50}
        if name is not None:
            params['name'] = name
        url_parts = [self.base_url, 'template', 'message', self.message_type]
        url = '/'.join(url_parts)
        more_pages = True
        while more_pages:
            resp = requests.get(url, headers=self._headers(), params=params)
            content = json.loads(resp.content)
            templates = content.get('data', None)
            if templates is not None:
                for temp in templates:
                    yield temp
            params['page'] = content.get('page', 0) + 1
            more_pages = content.get('morePages', False)


    def publish_template(self, template_name, template, override=False):
        """Publish a template on BPA Service API.

        If an existing template exists with the same name, then it is 
        overriden if `override` is set to `True`.

        Parameters
        ----------
        template_name : str
            Name of the template.
        template : dict
            Dictionary with the keys
                template str : the template to create
                defaults dict : default values for the template and message
                                parameters.
                parametersDefault str
        override : bool
            If `True`, then the template with same name is overriden. If 
            `False`, a ValueError is raised.
        
        Return
        ------

        """
        if self.queue_size == 0:
            raise ValueError(
                'A template cannot be published when the message queue is not empty.'
            )
        # Raise exception if template already exists when override is False
        if not override:
            for t in self.yield_templates(template_name):
                if t is not None and template_name == t['name']:
                    raise ValueError(
                        f'Template "{template_name}" already exist.')
        url_parts = [
            self.base_url,'template', 'message', self.message_type, 
            template_name]
        url = '/'.join(url_parts)
        resp = requests.put(url, headers=self._headers(), json=template)
        if resp.status_code == 204:
           self.template_name = template_name
        return resp
    

    def delete_template(self, template_name):
        """Permanently delete a template

        Parameters
        ----------
        template_name : str
            The name of the template to delete
        
        Returns
        -------
        `None` if the template is successfully deleted, the response otherwise.
        """
        url_parts = [
            self.base_url,'template', 'message',  self.message_type, template_name]
        url = '/'.join(url_parts)
        resp = requests.delete(url, headers=self._headers())
        if resp.status_code == 200:
            return None
        else:
            return resp
    

class RampartFile:
    """Class to represent a file to upload to Rampart

    """
    def __init__(self, file_id, file, recipient, process, folder, name, batch):
        self.file_id = file_id
        self.content = file
        self.recipient = recipient
        self.process = process
        self.folder = folder
        self.name = name
        self.batch = batch
        self.status = 'pending'
        self.response = None
        self.upload_id = None
        self.upload_name = None
        self.link = None
        self.key = None
        self.type = None

    def __repr__(self):
        args = (self.file_id, self.recipient, self.process, self.folder, 
                self.name, self.batch)
        return f'<RampartFile{reprlib.repr(args)}>'
    

class Rampart:
    """Class to upload/delete file on Rampart

    Attributes
    ----------
    files : List of <RampartFile> objects
        List of files to upload.
    
    Examples
    --------

    >>> r = Rampart()

    Add all files from a folder to the upload file list. 

    >>> folder = 'tests'
    >>> for f, f_id  in enumerate(os.listdir(folder)):
    ...     if not f.startswith('__'):
    ...         with open(os.path.join(file_loc, f), 'rb') as file:
    ...             r.add_file(
    ...                 f_id, file.read(), 'tibor.frossard@grabtaxi.com', 
    ...                 'process_name', 'folder_name', f, 'batch_name')
    
    Add files from inmemory Byte-like object.
    
    >>> r.add_file('r_another', r'somerandombytes', 'tibor.frossard@grabtaxi.com', 
                   'another_process', 'new_folder', 'somebytes.txt', 
                   'test_batch')
    
    Review the files to be uploaded.

    >>> df_files = r.to_df()
    >>> df_files.to_clipboard(excel=True)
    
    Upload the files. By default only files with 'pending' status are uploaded.
    Use `Rampart.RETRY_STATUS` to include also failed uploads from previous 
    upload.

    >>> r.upload(verbose=True)  # Print upload progress
     
    """
    MAX_CONCURRENCY = 10
    TIMEOUT = aiohttp.ClientTimeout(total=600)
    STATUS_MAPPING = {
        200: 'success',
        204: 'success',
        400: 'invalid',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'invalid_template',
        429: 'api_limit',
        500: 'server_error'
    }
    RETRY_STATUS = ('pending', 'server_error', 'timeout_error', 'api_limit')


    def __init__(self):
        """Instantiate a Rampart object.

        In order to be instantiate properly a Rampart object needs to read 
        the API_USER and API_PASS from environment variables.


        """
        user = os.environ.get('API_USER')
        password = os.environ.get('API_PASS')
        if user is None or password is None:
            raise OSError(
            '"API_USER" and "API_PASS" must be set as environment variables.')
        self._user = user
        self._password = password
        self._files = dict()
        self._base_url = 'https://bpa-api.grab-bat.net/'
        self._bucket = 'bpa-api-resources'


    @property
    def files(self):
        """Get list of files.

        Readonly attribute.
        """
        return self._files
    

    @files.setter
    def files(self, value):
        raise AttributeError(
            'readonly attribute. Use `add_file` method to add files.')


    @property
    def base_url(self):
        """Get base_url.

        Readonly attributes.
        """
        return self._base_url

    
    @base_url.setter
    def base_url(self, value):
        raise AttributeError('readonly attribute.')


    @property
    def bucket(self):
        """Get bucket.

        Readonly attributes.
        """
        return self._bucket


    @bucket.setter
    def bucket(self, value):
        raise AttributeError('readonly attribute.')


    def add_file(self, file_id, file, recipient, process, folder, name, batch):
        """Add a file to file list.

        The file is not uploaded yet. Use `upload` method to upload all files.

        Parameters
        ----------
        file_id : str
            A unique ID.
        file : Byte-like object
            The content of the file to upload.
        recipent : str
            The email adress of the recipient.
        process : str
            The identifier of the related process.
        folder : str
            The logical grouping of the file.
        name : str
            The name of the file.
        batch : str
            A batch reference number.
        
        Return
        ------
        None. The files are uploaded.
        """
        f_id = len(self._files) + 1
        file_id = str(file_id)
        if file_id in self._files:
            raise ValueError(f'file_id "{file_id}" already exists.')
        self._files[file_id] = RampartFile(
            f_id, file, recipient, process, folder, name, batch)


    def _auth(self):
        """Authenfication
        """
        return aiohttp.BasicAuth(self._user, self._password)


    def _url(self):
        return self._base_url + 'file'


    async def _upload_file(self, file, semaphore, verbose):
        """Upload a file to Rampart and register the response.

        The RampartFile is modified inplace to record the response.

        Parameters
        ----------
        file : <RampartFile>
            The file to send. The response is recorded in the response 
            attribute of the RampartFile itself, hence modifying it.
        Semaphore : `<async.Semaphore>`
            Semaphore to restrict the number of concurrent uploads.
        verbose : bool
            Whether to show upload progress.
        
        Return
        ------
        Coroutine.

        """
        l = len(str(len(self._files))) # For display of status only.
        cls = self.__class__
        async with semaphore:
            async with aiohttp.ClientSession(auth=self._auth(), 
                                             timeout=cls.TIMEOUT) as session:
                params = {
                    'recipient': file.recipient,
                    'process': file.process,
                    'folder': file.folder,
                    'name': file.name,
                    'batch': file.batch
                    }
                data = aiohttp.FormData()
                data.add_field('files', file.content, filename='file', 
                               content_type='multipart/form-data')
                try:
                    async with session.post(
                            self._url(), data=data, params=params) as resp:
                        response = await resp.text()
                        try:
                            file.response = json.loads(response)
                        except json.decoder.JSONDecodeError:
                            file.response = response
                        file.response_code = resp.status
                        status_map = cls.STATUS_MAPPING
                        file.status = status_map.get(resp.status, 'unknown')
                        try:
                            result = file.response['result'][0]
                        except (KeyError, TypeError, IndexError):
                            pass
                        else:
                            file.upload_name  = result.get('name')
                            file.upload_id = result.get('fileId')
                            file.link = result.get('link')
                            file.key = np.base_repr(file.upload_id, 36).lower()
                            file.type = file.upload_name.split('.')[-1]
                except aiohttp.ClientError as err:
                    file.status = 'server_error'
                    file.response = err
                except asyncio.TimeoutError as err:
                    file.status = 'timeout_error'
                    file.response = err
                if verbose:
                    print(
                        f'    File #{str(file.file_id).zfill(l)} uploaded.',
                        f'API response: {file.status}', sep=' ')


    def upload(self, status='pending', verbose=False):
        """Upload all files concurrently.

        The maximum number of concurrent upload is set as a class attribute
        `MAX_CONCURRENCY`. Only the files with the corresponding status are 
        uploaded. 
        Once the file is uploaded then the receivers can directly see and 
        download it.

        Parameters
        ----------
        status : str or container of str
            Only the files with the corresponding status are sent.
        verbose : bool
            Whether to show progress.
        
        Returns
        -------
        None. The files are uploaded.

        """
        if isinstance(status, str):
            status = (status,)
        files = [f for _, f in self._files.items() if f.status in status]
        n_files = len(files)
        if n_files > 0:
            if verbose:
                print(f'Sending {n_files} files...')
            loop = asyncio.get_event_loop()
            semaphore = asyncio.Semaphore(self.__class__.MAX_CONCURRENCY)
            future = asyncio.gather(
                *(self._upload_file(f, semaphore, verbose) for f in files)
            )
            loop.run_until_complete(future)
        else:
            if verbose:
                print('No file to upload')


    async def _delete_file(self, file_id, semaphore):
        cls = self.__class__
        async with semaphore:
            async with aiohttp.ClientSession(auth=self._auth(), 
                                             timeout=cls.TIMEOUT) as session:
                url = self.base_url +  'file/' + str(file_id)
                async with session.delete(url) as resp:
                    response = await resp.text()
                    return response


    def delete_files(self, file_ids):
        """Deletes files on Rampart

        Parameters
        ----------
        files_ids : Iterable
            Rampart file_id to delete. These are the IDs sent by the Rampart
            API.
        
        Returns
        -------
        """
        loop = asyncio.get_event_loop()
        semaphore = asyncio.Semaphore(self.__class__.MAX_CONCURRENCY)
        future = asyncio.gather(
            *(self._delete_file(f_id, semaphore) for f_id in file_ids)
        )
        res = loop.run_until_complete(future)
        return res


    def to_df(self):
        """Export files list to a DataFrame

        Returns
        -------
        <pandas.DataFrame>
        """
        df = pd.DataFrame([dict(**vars(f), **{'ext_file_id': k}) for k, f in self._files.items()])
        del df['file_id']
        df.rename(columns={'ext_file_id': 'file_id'}, inplace=True)
        
        return df
