import json
import logging
import time
from pprint import pprint

from .exceptions import ( ObjectNotFound )



class Namespace(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, session):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.session = session
        self.namespace_url = '/namespace'
                  
        #initialize session timeout values
        self.timeout = 0
    
    def api_call(self,method, url,**kwargs):
        '''add the namespace prefix to the api call'''
        return self.session.api_call(method, self.namespace_url + url,**kwargs)
        
    def api_call_resumeable(self,object_name,method,url,**kwargs):
        '''add the namespace prefix to the api call'''
        return self.session.api_call_resumeable(object_name,method,self.namespace_url + url,**kwargs)
           
    def accesspoint(self):
        r = self.api_call("GET", "")
        
        data = r['namespaces']
        
        #move all the name, value pairs into an actual dictionary for easy use.
        results = {}
        for x in data:
            results[ x['name'] ] = x['path']
        return results

        
    
    def accesspoint_create(self,name,path):
        data['path'] = path
        r = self.api_call("PUT",  '/' + name.strip('/'), data=json.dumps(data) )
    
    def accesspoint_delete(self,name):
        r = self.api_call("DELETE",  '/' + name.strip('/') )
 
    def accesspoint_setacl(self,name,acl):
        self.acl_set('/' + name,acl,nsaccess=True)
 
    def accesspoint_getacl(self,name):
        return self.acl('/' + name,nsaccess=True)
    
    
    def acl(self,path,nsaccess=False):
        '''get acl'''       
        options = "?acl"
        if nsaccess:
            options += "&nsaccess=true"
        return self.api_call("GET", path + options)

    def acl_set(self,path,acls,nsaccess=False):
        '''set acl'''
        options = "?acl"
        if nsaccess:
            options += "&nsaccess=true"
        acls['authoritative'] = "acl"
        r = self.api_call("PUT", path + options,data=json.dumps(acls))
   
    
    def metadata(self,path):
        '''get metadata'''        
        options = "?metadata"
        
        data = self.api_call("GET", path + options)
        if not 'attrs' in data:
            return None
        data = data['attrs']
        
        #move all the name, value pairs into an actual dictionary for easy use.
        results = {}
        for x in data:
            #print(x)
            results[ x['name'] ] = x['value']
        return results
        
    def metatdata_set(self,path,metadata):
        pass
        
                    
    def file_copy(self,src_path, dst_path, clone=False):
        '''Copy a file''' 
        options=""
        if clone:
            options="clone=true"
                
        else:
            #Do a full file copy
            headers = { "x-isi-ifs-copy-source" :  "/namespace" + src_path }
            
        r = self.api_call("PUT", self.namespace_url + dst_path + options, headers=headers)


    def dir(self,path):
        '''Get directory listing'''        
        for item in self.api_call_resumeable("children","GET", path,params={'detail':'type'}):
            yield item
        
        return
        
        
        
    def is_dir(self,path):
        metadata = self.metadata(path)
        if 'type' in metadata and metadata['type'] == "container" :
            return True
        return False

        
    def dir_create(self,path,recursive=True):
        '''Create a new directory'''  
        headers = { "x-isi-ifs-target-type" : "container" }   
        options=""
        if(recursive):
            options = "?recursive=true"    
        r = self.api_call("PUT", self.namespace_url + path + options, headers=headers)
    
    
    def dir_delete(self,path):
        '''delete a directory'''  
        options=""
        r = self.api_call("DELETE", self.namespace_url + path + options)

 
        
        
