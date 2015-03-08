import json
import requests
import httplib
import logging
import time

from .exceptions import ( ObjectNotFound, IsilonLibraryError )

class Platform(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''
    def __init__(self, session):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.session = session
        self.platform_url = '/platform/'
        
        
    def _override(self,params,overrides):
        '''copy overrides into params dict, so user can specify additional params not specifically layed out'''
        for (k,v) in overrides.items():
            params[k] = v
        return params

    def api_call(self,method, url,**kwargs):
        '''add the platform prefix to the api call'''
        return self.session.api_call(method, self.platform_url + url,**kwargs)
        
    def api_call_resumeable(self,method,url,**kwargs):
        '''add the namespace prefix to the api call'''
        return self.session.api_call_resumeable(method,self.platform_url + url,**kwargs)
        
    def snapshot(self,name="",**kwargs):
        '''Get a list of snaps, refer to API docs for other key value pairs accepted as params '''
        #if a specific name is specified we want to return a single object
        if name:
            try:
                data =  self.api_call("GET","1/snapshot/snapshots/" + name,params=kwargs)
            except ObjectNotFound:
                return []
                
            if 'snapshots' in data:
                return data['snapshots']
            return []
        
        #else we are going to return a generator function          
        return self.api_call_resumeable("GET","1/snapshot/snapshots/" + name, params=kwargs)
        
    def snapshot_create(self,name,path,**kwargs):
        '''Create snapshot'''      
        data = self._override({'name':name , 'path': path }, kwargs)
        return self.api_call("POST", "1/snapshot/snapshots", data=json.dumps(data) )

    def snapshot_modify(self,orig_name,**kwargs):
        '''Modify snapshot'''      
        return self.api_call("PUT", "1/snapshot/snapshots/" + orig_name ,data=json.dumps(kwargs))
  
    def snapshot_delete(self,name,**kwargs):
        '''Delete snapshot'''
        if name == "":
            #This will delete all sanpshots, lets fail and make a seperate func just for that
            raise IsilonLibraryError("Empty name field for snapshot delete, use snapshot_delete_all to delete all snaps")
        return self.api_call("DELETE", "1/snapshot/snapshots/" + name,params=kwargs)

    def snapshot_delete_all(self,**kwargs):
        return self.api_call("DELETE", "1/snapshot/snapshots/",params=kwargs)
      
    
    def quota(self,**kwargs):
        '''Get a list of quotas, refer to API docs for other key value pairs accepted as params '''
        options={'resolve_names' : True}     
        #else we are going to return a generator function          
        return self.api_call_resumeable('GET','1/quota/quotas/', params=self._override(options,kwargs))

    def hdfs_racks(self,**kwargs):
        return self.api_call_resumeable('GET','1/protocols/hdfs/racks',params=kwargs)

       
    def config(self):
        '''get Config'''
        return self.api_call("GET", "1/cluster/config")
        


        