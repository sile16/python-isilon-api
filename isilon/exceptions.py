

class ObjectNotFound(RuntimeError):
    """The API has responsed with an HTTP 404 Object not found code, 
    suppressed for queries as None is returned instead"""
    
class APIError(RuntimeError):
    """This is an api level error"""
    
class ConnectionError(RuntimeError):
    """This is an api level error"""
    

    
class IsilonLibraryError(RuntimeError):
    
	"""This is a library error, something that the library is trying to automate or protect"""

    