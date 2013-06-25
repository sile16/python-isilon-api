import json
import logging
import time
from pprint import pprint
import paramiko

from .exceptions import ( ObjectNotFound )



class Namespace(object):

    '''Implements higher level functionality to interface with an Isilon cluster'''

    def __init__(self, session):
        self.log = logging.getLogger(__name__)
        self.log.addHandler(logging.NullHandler())
        self.session = session
        self.api_call = session.api_call
        self.namespace_url = '/namespace'
                  
        self.last_page = True
        self.entries = {}
        self.index = 0
        self.resume = ""

        #initialize session timeout values
        self.timeout = 0
   
    def accesspoint(self):
        r = self.api_call("GET", self.namespace_url)
        data = r.json()['namespaces']
        
        #move all the name, value pairs into an actual dictionary for easy use.
        results = {}
        for x in data:
            results[ x['name'] ] = x['path']
        return results

        
    
    def accesspoint_create(self,name,path):
        data['path'] = path
        r = self.api_call("PUT", self.namespace_url + '/' + name.strip('/'), data=json.dumps(data) )
    
    def accesspoint_delete(self,name):
        r = self.api_call("DELETE", self.namespace_url + '/' + name.strip('/') )
 
    def accesspoint_setacl(self,name,acl):
        self.acl_set('/' + name,acl,nsaccess=True)
 
    def accesspoint_getacl(self,name):
        return self.acl('/' + name,nsaccess=True)
    
    
    def acl(self,path,nsaccess=False):
        '''get acl'''       
        options = "?acl"
        if nsaccess:
            options += "&nsaccess=true"
        r = self.api_call("GET", self.namespace_url + path + options)
        return r.json()

    def acl_set(self,path,acls,nsaccess=False):
        '''set acl'''
        options = "?acl"
        if nsaccess:
            options += "&nsaccess=true"
        acls['authoritative'] = "acl"
        r = self.api_call("PUT", self.namespace_url + path + options,data=json.dumps(acls))
   
    
    def metadata(self,path):
        '''get metadata'''        
        options = "?metadata"
        
        r = self.api_call("GET", self.namespace_url + path + options)
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
        
    def metatdata_set(self,path,metadata):
        pass
        
                    
    def file_copy(self,src_path, dst_path, clone=False):
        '''Copy a file''' 
        if clone:
            #We have to use SSH until they add it into the Api
            
            if self.session.ssh == None:
                self.session.connect_SSH()
                
            try:    
                stdin, stdout, stderr = self.ssh.exec_command("cp -c \"%s\" \"%s\"" % (src_path,dst_path) )
                #Read output stream to wait for command completion
                stdout.read()
            except paramiko.SSHException, e:
                time.sleep(.001)
                try:
                    self.session.ssh.close()
                except:
                    pass
                
                #raise Exception
                raise(e)                            
        else:
            #Do a full file copy
            headers = { "x-isi-ifs-copy-source" :  "/namespace" + src_path }
            options=""
            r = self.api_call("PUT", self.namespace_url + dst_path + options, headers=headers)

    def dir(self,path,resume=None):
        '''Get directory listing'''
        #Reset variables for iteration
        self.last_page = True
        self.index=0
        
        options = "?detail=type"
        
        if resume:
            options = options + ( "&resume=%s" % resume)
        r = self.api_call("GET", self.namespace_url + path + options)
        
        
        data = r.json()
        
        #Check for a resume token for mutliple pages of results
        if 'resume' in data:
            self.resume = data['resume']
            self.path = path
            self.last_page = False
        
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
            if self.last_page :
                raise StopIteration               
            else:
                #We need to request the next page of results
                self.dir(self.path,resume=self.resume)
        self.index +=1
        return self.entries[self.index - 1]

        
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

 
        
        
