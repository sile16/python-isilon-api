import json
import requests
import httplib
import logging
import time
from pprint import pprint
import paramiko
import sys
import socket

class API:

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, url, username, password, services="platform, namespace"):
        self.ip = socket.gethostbyname(url)
        self.url= "https://" + self.ip + ':8080'
        self.session_url = self.url + '/session/1/session'
        self.platform_url = self.url + '/platform/1'
        self.namespace_url = self.url + '/namespace'

        self.username = username
        self.password = password
        self.services = services
        
        #SSH stuff until file cloning is part of API
        self.ssh = None

        #Create HTTPS Requests session object
        self.s = requests.Session()
        self.s.headers.update({'content-type': 'application/json'})
        self.s.verify = False
        
        self.lastPage = True
        self.entries = {}
        self.index = 0
        self.resume = ""

        #initialize session timeout values
        self.timeout = 0
        
    
    def badCall(self,r):
        logging.error("===========Bad API Call=================================================================")
        logging.error("%s  %s , HTTP Code: %d" % (r.request.method, r.request.url, r.status_code))
        logging.error("Request Headers: %s" % r.request.headers)
        logging.error("Request Data : %s" % (r.request.body))
        logging.error("")
        logging.error("Response Headers: %s " % r.headers )
        logging.error("Response Data: %s" % (r.text.strip()))
        logging.error("=========================================================================================")



    def apiCall(self,method,url,**kwargs):
        
        #check to see if there is a valid session 
        if time.time() > self.timeout:
            self.sessionCreate()        

        if len(url) > 8198:
            logging.error("URL Length too long: %s", url)
            return

        r = self.s.request(method,url,**kwargs) 
          
        #check for authorization issue and retry if we just need to create a new session
        if r.status_code == 401:
            #self.badCall(r)
            logging.warning("Authentication Failure, trying to reconnect session")
            try:
                
                if(self.sessionCreate()):
                    r = self.s.request(method,url,**kwargs)
                else:
                    logging.error("Unable to reconnect")
                    return r
            except:
                logging.error("Exception raised during reconnect")
                logging.error(sys.exc_info())
                return r
                   
        if r.status_code > 204 and r.status_code != 404:
            self.badCall(r)
        
        logging.debug("===========Good API Call=================================================================")
        logging.debug("%s URL: %s , HTTP Code: %d" % (r.request.method, r.request.url, r.status_code))
        logging.debug("Request Headers: %s" % r.request.headers)
        logging.debug("Request Data: %s" % r.request.body)
        logging.debug("")
        logging.debug("Response Headers : %s" % r.headers)
        logging.debug("Response Data: %s" % r.text.strip())  
        logging.debug("=========================================================================================")
        
        return r

    def sessionCreate(self):
        
        #Get an API session cookie from Isilon
        #Cookie is automatically added to HTTP requests session
        logging.debug("--> creating session")
        sessionjson = json.dumps({'username': self.username , 'password': self.password , 'services': ['platform', 'namespace']})
        
        r = self.s.post(self.session_url,data=sessionjson) 
        if r.status_code != 201 :
            #r.raise_for_status()
            self.badCall(r)
            return False
            
        #Renew Session 60 seconds prior to our timeout
        self.timeout = time.time() + r.json()['timeout_absolute'] - 60
        logging.debug("New Session created! Current clock %d, timeout %d" % (time.time(),self.timeout))
        return True

    def pfSnapGet(self,name):
        r = self.apiCall("GET",self.platform_url + "/snapshot/snapshots/" + name)
        if r.status_code == 404:
            return None
        return r.json()
        

    def pfSnapCreate(self,name,path):
        '''Create snapshot'''      
        logging.info("Creating Snapshot")
        sessionjson = json.dumps({'name':name , 'path': path })
        r = self.apiCall("POST", self.platform_url+ "/snapshot/snapshots",data=sessionjson)
         
        
    def pfSnapDelete(self,name):
        '''Delete snapshot'''    
        logging.info("Deleting Snapshot")
        sessionjson = ""
        r = self.apiCall("DELETE", self.platform_url+ "/snapshot/snapshots/" + name)
        
    def pfConfigGet(self):
        '''get Config'''
        r = self.apiCall("GET", self.platform_url+"/cluster/config")
        return r.json()
    
    def nsDirGet(self,path,resume=None):
        '''Get directory listing'''
        #Reset variables for iteration
        self.lastPage = True
        self.index=0
        
        options = "?detail=type"
        
        if resume:
            options = options + ( "&resume=%s" % resume)
        r = self.apiCall("GET", self.namespace_url + path + options)
        
        
        data = r.json()
        
        #Check for a resume token for mutliple pages of results
        if 'resume' in data:
            self.resume = data['resume']
            self.path = path
            self.lastPage = False
        
        #Make sure we have entries and save them into self.entries for iteration
        if 'children' in data:    
            self.entries = data['children']
        else:
            self.entries = []
            
        return self
        
    def __iter__(self):
        return self
        
    def next(self):
        if self.index >= len(self.entries) :
            if self.lastPage :
                raise StopIteration
                
            else:
                #We need to request the next page of results
                self.nsDirGet(self.path,resume=self.resume)
                
        self.index +=1
        return self.entries[self.index - 1]
        
            
       
        
    def nsAttributesGet(self,path):
        '''Get directory via HEAD method'''        
        r = self.apiCall("HEAD", self.namespace_url + path)
        if r.status_code == 404:
            return None
        return r.headers
    
    def nsAclGet(self,path):
        '''get acl'''       
        options = "?acl"
        r = self.apiCall("GET", self.namespace_url + path + options)
        if r.status_code == 404:
            return None
        return r.json()
        
    def nsMetadataGet(self,path):
        '''get metadata'''        
        options = "?metadata"
        r = self.apiCall("GET", self.namespace_url + path + options)
        if r.status_code == 404:
            return None
        data = r.json()
        if not 'attrs' in data:
            return None
        data = data['attrs']
        
        #move all the name, value pairs into an actual dictionary for easy use.
        results = {}
        for x in data:
            #print(x)
            results[ x['name'] ] = x['value']
        return results
        
    def nsAclSet(self,path,acls):
        '''set acl'''
        options = "?acl"
        acls['authoritative'] = "acl"
        r = self.apiCall("PUT", self.namespace_url + path + options,data=json.dumps(acls))
         
    def connectSSH(self):

        connected = False            
        
        #Paramiko doesn't like to spin up too many threads at once...  add a bunch of retries/looping until connected...
        while not connected:
            try:
                if self.ssh == None:
                    self.ssh = paramiko.SSHClient()
                    self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    
                #initialize SSH on first use
                self.ssh.connect(self.ip, username=self.username, password=self.password)
                connected = True
                
            except paramiko.SSHException:
                logging.warning("re-trying SSH Connection")
                time.sleep(.001)
                    
    def nsFileCopy(self,src_path, dst_path, clone=False):
        '''Copy a file''' 
        if clone:
            #We have to use SSH __BOOOOO__   until they add it into the Api
            
            if self.ssh == None:
                self.connectSSH()
            try:    
                stdin, stdout, stderr = self.ssh.exec_command("cp -c \"%s\" \"%s\"" % (src_path,dst_path) )
                #Read output stream to wait for command completion
                stdout.read()
            except paramiko.SSHException:
                time.sleep(.001)
                try:
                    self.ssh.close()
                except:
                    pass
                   
                self.nsFileCopy(src_path,dst_path,clone)
            
        else:
            #Do a full file copy
            headers = { "x-isi-ifs-copy-source" :  "/namespace" + src_path }
            options=""
            r = self.apiCall("PUT", self.namespace_url + dst_path + options, headers=headers)

        
    def nsExtAttribtutesGet(self,path):
        '''get ext attributes'''     
        options = "?metadata"
        r = self.apiCall("GET", self.namespace_url + path + options)
        if r.status_code == 404:
            return None
        return r.json()

        
    def nsDirCreate(self,path,recursive=True):
        '''Create a new directory'''  
        headers = { "x-isi-ifs-target-type" : "container" }   
        options=""
        if(recursive):
            options = "?recursive=true"
        
        r = self.apiCall("PUT", self.namespace_url + path + options, headers=headers)

 
        
        
