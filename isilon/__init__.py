import session
import namespace
import platform

from .exceptions import ObjectNotFound, APIError, ConnectionError

class API(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, *args, **kwargs):
        
        self.session = session.Session(*args, **kwargs)
        self.namespace = namespace.Namespace(self.session)
        self.platform = platform.Platform(self.session)
        
        
 
        
        
