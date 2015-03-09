import json
import requests
import httplib
import logging
import time
from pprint import pprint
import sys
import socket

from .exceptions import ( ConnectionError, ObjectNotFound, APIError, IsilonLibraryError )


class GenToIter(object):
    ''' Converts a generator object into an iterator so we can use len(results)
    we do this by passing the total as the first result from our generator function.
    Also, makes the actual API call on init rather than on the 
    first next() as with a generator'''
    
    def __init__(self,gen):
        self.gen=gen
        self.length=gen.next()
            
    def __iter__(self):
        return self
    
    def next(self):
        return self.gen.next()
   
    def __len__(self):
        return self.length


class Session(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, fqdn, username, password, secure=True, port = 8080, services=('namespace','platform')):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.ip = socket.gethostbyname(fqdn)
        self.port = port
        self.username = username
        self.password = password
        self.services = services
        self.url= "https://" + self.ip + ':' + str(port)
        self.session_url = self.url + '/session/1/session'
        
        #disable invalid security certificate warnings
        if(not secure):
            requests.packages.urllib3.disable_warnings()
        
        #Create HTTPS Requests session object
        self.s = requests.Session()
        self.s.headers.update({'content-type': 'application/json'})
        self.s.verify = secure
        
        #initialize session timeout values
        self.timeout = 0
        self.r = None
        
    
    def log_api_call(self,r,lvl):
        
        self.log.log(lvl, "===========+++ API Call=================================================================")
        self.log.log(lvl,"%s  %s , HTTP Code: %d" % (r.request.method, r.request.url, r.status_code))
        self.log.log(lvl,"Request Headers: %s" % r.request.headers)
        self.log.log(lvl,"Request Data : %s" % (r.request.body))
        self.log.log(lvl,"")
        self.log.log(lvl,"Response Headers: %s " % r.headers )
        self.log.log(lvl,"Response Data: %s" % (r.text.strip()))
        self.log.log(lvl,"=========================================================================================")

    def debug_last(self):
        if self.r:
            self.log_api_call(self.r,logging.ERROR)

    def api_call(self,method,url,**kwargs):
        
        #check to see if there is a valid session 
        if time.time() > self.timeout:
            self.connect()        
        
        #incoming API call uses a relative path
        url = self.url + url
        
        if len(url) > 8198:      
            self.log.exception("URL Length too long: %s", url)
        
        #make actual API call
        r = self.s.request(method,url,**kwargs)
        self.r = r
                 
        #check for authorization issue and retry if we just need to create a new session
        if r.status_code == 401:
            #self.bad_call(r)
            logging.info("Authentication Failure, trying to reconnect session")
            self.connect()
            r = self.s.request(method,url,**kwargs)
            self.r = r
        
        
        if r.status_code == 404:      
            self.log_api_call(r,logging.INFO)
            raise ObjectNotFound()
        elif r.status_code == 401:
            self.log_api_call(r,logging.ERROR)
            raise APIError("Authentication failure")
        elif r.status_code > 204:
            self.log_api_call(r,logging.ERROR)
            message = "API Error: %s" % r.text
            raise APIError(message)
        else:
            self.log_api_call(r,logging.DEBUG)
        
        
        #if type json lets return the json directly
        if 'content-type' in r.headers:
            if 'application/json' == r.headers['content-type']:
                return r.json()
        
        return r.text
            
            
            
    def api_call_resumeable(self,method,url,**kwargs):
        ''' Returns a generator, lists through all objects even if it requires multiple API calls '''
        def _api_call_resumeable(method,url,**kwargs):
            #initialize state for resuming    
            object_name = None
            resume=None
            total = sys.maxint
            
            #Make First API Call
            try:
                data = self.api_call(method, url, **kwargs)
            except ObjectNotFound:
                yield 0
                return
        
        	#Find the object name we are going to iterate, it should be the only array at the top level
            for k,v in data.items():
                if isinstance(v,list):
                    if not object_name is None:
                        #found two arrays... also this will break this logic
                        raise IsilonLibraryError("two arrays found in resumeable api call")
                    object_name = k
                    
            if object_name is None:
                #we can't find the object name, lets throw an exception because this shouldn't happen:
                raise IsilonLibraryError("no array found in resumable api call")
        
        	
            if 'total' in data:
                total = data['total']
            else:
            	if 'resume' in data and data['resume']:
            		total = sys.maxint
            	else:
            		total = len(data[object_name])
      	
            yield total
        
            
        
            #We will loop through as many api calls as needed to retrieve all items
            while True:
                
                if object_name in data:    
                    for obj in data[object_name]:
                        yield obj
                else:
                    raise IsilonLibraryError("expected data object is missing")
                            
                #Check for a resume token, is it valid, if so api call the next set of results, else break
                if 'resume' in data and data['resume']:
                    kwargs['params'] = {'resume': data['resume'] }
                    data = self.api_call(method, url, **kwargs) 
                else:
                    break

            #no more resume tokens          
            return #end of _api_call_resumeable
        
        results = GenToIter(_api_call_resumeable(method,url,**kwargs))
        #for queries that should return a few results just return a list so that full indexing works
        if len(results) < 10:
        	return list(results)
        else:
        	return results
      

    def connect(self):
        
        #Get an API session cookie from Isilon
        #Cookie is automatically added to HTTP requests session
        logging.debug("--> creating session")
        sessionjson = json.dumps({'username': self.username , 'password': self.password , 'services': self.services})
        
        r = self.s.post(self.session_url,data=sessionjson) 
        if r.status_code != 201 :
            #r.raise_for_status()
            self.log_api_call(r,logging.ERROR)
            raise ConnectionError(r.text)
            
        #Renew Session 60 seconds prior to our timeout
        self.timeout = time.time() + r.json()['timeout_absolute'] - 60
        logging.debug("New Session created! Current clock %d, timeout %d" % (time.time(),self.timeout))
        return True

         