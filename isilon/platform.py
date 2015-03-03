import json
import requests
import httplib
import logging
import time


class Platform(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, session):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.session = session
        self.api_call = session.api_call
        self.platform_url = '/platform/1'
        
    def _override(params,overrides):
        '''copy overrides into params dict, so user can specify additional params not specifically layed out'''
        for (k,v) in overides:
            params[k] = v
        return params


    def snapshot(self,name="",**kwargs):
        '''Get a list of snaps, refer to API docs for other key value pairs accepted as params '''        
        data = self.api_call("GET",self.platform_url + "/snapshot/snapshots/" + name,params=kwargs)
        if 'snapshots' in data:
            return data['snapshots']
        return None

    def snapshot_create(self,name,path,**kwargs):
        '''Create snapshot'''      
        data = self.override({'name':name , 'path': path }, kwargs)
        return self.api_call("POST", self.platform_url+ "/snapshot/snapshots",data=data.dumps())
  
    def snapshot_modify(self,name,**kwargs):
        '''Create snapshot'''      
        data = self.override({'name':name , kwargs)
        return self.api_call("PUT", self.platform_url+ "/snapshot/snapshots",data=data.dumps())
  
    def snapshot_delete(self,name,**kwargs):
        '''Delete snapshot'''
        if name = "":
            #This will delete all sanpshots, lets fail and make a seperate func just for that
            raise IsilonLibraryError("Empty name field for snapshot delete, use snapshot_delete_all to delete all snaps")
        return self.api_call("DELETE", self.platform_url+ "/snapshot/snapshots/" + name,params=kwargs)


    def snapshot_delete_all(self,**kwargs):
        return self.api_call("DELETE", self.platform_url+ "/snapshot/snapshots/",params=kwargs)
           
    def quota(self, path, **kwargs):
        '''get quotas'''
        
        return 


       
    def config(self):
        '''get Config'''
        return self.api_call("GET", self.platform_url+"/cluster/config")
        


        