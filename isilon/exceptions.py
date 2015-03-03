

class ObjectNotFound(RuntimeError):
    """The API has responsed with an HTTP 404 Object not found code"""
    
class APIError(RuntimeError):
    """This is an api level error"""
    
class ConnectionError(RuntimeError):
    """This is an api level error"""
    
class IsilonLibraryError(RuntmeError):
    """This is a library error, something that the library is trying to automate or protect"""

    