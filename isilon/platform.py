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
              

    def snap(self,name=""):
        r = self.api_call("GET",self.platform_url + "/snapshot/snapshots/" + name)
        data = r.json()
        if 'snapshots' in data:
            return r.json()['snapshots']
        return None
        

    def snap_create(self,name,path):
        '''Create snapshot'''      
        logging.info("Creating Snapshot")
        sessionjson = json.dumps({'name':name , 'path': path })
        r = self.api_call("POST", self.platform_url+ "/snapshot/snapshots",data=sessionjson)
         
        
    def snap_delete(self,name):
        '''Delete snapshot'''    
        logging.info("Deleting Snapshot")
        sessionjson = ""
        r = self.api_call("DELETE", self.platform_url+ "/snapshot/snapshots/" + name)
        
    def config(self):
        '''get Config'''
        r = self.api_call("GET", self.platform_url+"/cluster/config")
        return r.json()