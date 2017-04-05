import os
import logging
import cgi
import json
import sys

from ..http import Request, Response
from ..call import Router, Call
from ..decorators import _property
from ..exception import CallError, Redirect, CallStop, AccessDenied


logger = logging.getLogger(__name__)


class BaseServer(object):
    """all servers should extend this and implemented the NotImplemented methods,
    this ensures a similar interface among all the different servers

    A server is different from the interface because the server is actually responsible
    for serving the requests, while the interface will translate the requests to
    and from endpoints itself into something the server backend can understand
    """
    controller_prefix = ''
    """the controller prefix you want to use to find your Controller subclasses"""

    #interface_class = None
    """the interface that should be used to translate between the supported server"""

    backend_class = None
    """the supported server's interface, there is no common interface for this class.
    Basically it is the raw backend class that the BaseServer child is translating
    for endpoints compatibility"""

    request_class = Request
    """the endpoints.http.Request compatible class that should be used to make
    Request() instances"""

    response_class = Response
    """the endpoints.http.Response compatible class that should be used to make
    Response() instances"""

    router_class = Router
    """the endpoints.call.Router compatible class that hadnles translating a request
    into the Controller class and method that will actual run"""

    call_class = Call
    """the endpoints.call.Call compatible class that should be used to make a
    Call() instance"""

    @_property
    def backend(self):
        return self.create_backend()

    @_property
    def router(self):
        return self.create_router()

    def __init__(self, controller_prefix='', **kwargs):
        if controller_prefix:
            self.controller_prefix = controller_prefix
        else:
            self.controller_prefix = os.environ.get('ENDPOINTS_PREFIX', '')

#         classes = (n[0] for n in inspect.getmembers(Foo) if n[0].endswith("_class"))
#         for k in classes:
#             if k in kwargs:
#                 setattr(self, k, kwargs[k])

        for k, v in kwargs.items():
            if k.endswith("_class"):
                setattr(self, k, v)

    def create_backend(self, **kwargs):
        return self.backend_class(**kwargs)

    def create_request(self, raw_request, **kwargs):
        """convert the raw interface raw_request to a request that endpoints understands"""
        raise NotImplementedError()

    def create_response(self, **kwargs):
        """create the endpoints understandable response instance that is used to
        return output to the client"""
        return self.response_class()

    def create_call(self, raw_request, **kwargs):
        """create a call object that has endpoints understandable request and response
        instances"""
        req = self.create_request(raw_request, **kwargs)
        res = self.create_response(**kwargs)
        rou = self.create_router(**kwargs)
        c = self.call_class(req, res, rou)
        return c

    def create_router(self, **kwargs):
        kwargs.setdefault('controller_prefix', self.controller_prefix)
        r = self.router_class(**kwargs)
        return r

    def handle_request(self):
        raise NotImplementedError()

    def serve_forever(self):
        try:
            while True: self.handle_request()
        except Exception as e:
            logger.exception(e)
            raise

    def serve_count(self, count):
        try:
            handle_count = 0
            while handle_count < count:
                self.handle_request()
                handle_count += 1
        except Exception as e:
            logger.exception(e)
            raise

