import unittest
import isilon
import ssl
import socket
import sys
import requests
import time

from requests.exceptions import SSLError
from isilon.exceptions import *

fqdn = '192.168.167.101'
user = 'root'
password = 'a'
testfolder = '/ifs/apitest_' + str(int(time.time()))
testsnap = 'apitest_snap' + str(int(time.time()))

class IsilonAPI(unittest.TestCase):

    

    def setUp(self):
        pass
        #self.api = isilon.API(fqdn,user,password,secure=False)

    
    
    def test_bad_ssl_cert(self):
        api = isilon.API(fqdn,user,password)
        self.assertRaises(requests.exceptions.SSLError,api.session.connect)
        
    def test_snap_change(self):
        #expire test snaps 60 seconds into the future
        expires = int(time.time()) + 60
        api = isilon.API(fqdn,user,password,secure=False)
        api.platform.snapshot_create(testsnap,"/ifs/data",expires=expires)
        self.assertGreater(len(api.platform.snapshot(testsnap)),0)
        self.assertGreater(len(api.platform.snapshot()),0)
        api.platform.snapshot_modify(testsnap,expires=expires+1)
        self.assertEqual(api.platform.snapshot(testsnap)[0]['expires'], expires+1)
        api.platform.snapshot_delete(testsnap)
        
    def test_snap_bad_query(self):
        api = isilon.API(fqdn,user,password,secure=False)
        if api.platform.snapshot("fakename123askksdfkasdfkas"):
            self.assertTrue(False)
        
    def test_empty_resumable_api_set(self):
        api = isilon.API(fqdn,user,password,secure=False)
        results = api.platform.hdfs_racks()
        self.assertEqual(len(results),0)
        for x in results:
            self.assertTrue(False)
        
    def test_snap_delete_all(self):
        api = isilon.API(fqdn,user,password,secure=False)
        self.assertRaises(IsilonLibraryError,api.platform.snapshot_delete,"")
        
    def test_file_creation(self):
        api = isilon.API(fqdn,user,password,secure=False)
        
        #Create some test files / folders
        api.namespace.dir_create(testfolder)
        self.assertTrue(api.namespace.is_dir(testfolder))
        
        for x in ('a','b'):
            subfolder = testfolder + '/' + x
            api.namespace.dir_create(subfolder)
            for y in range(1,10):
                api.namespace.file_create(subfolder + '/' + str(x) + str(y),"test_file")
        
        #namespace example
        dir_a = []
        dir_b = []
        
        gena = api.namespace.dir(testfolder + '/a', limit=2, sort='name', dir='ASC')
        genb = api.namespace.dir(testfolder + '/b', limit=2, sort='name',dir='DESC')
        while True:
            try:
                itema = gena.next()
                itemb = genb.next()
                dir_a.append(itema['name'])
                dir_b.append(itemb['name'])
            except StopIteration:
                break
                
        self.assertEqual(dir_a,[u'a1', u'a2', u'a3', u'a4', u'a5', u'a6', u'a7', u'a8', u'a9'])
        self.assertEqual(dir_b,[u'b9', u'b8', u'b7', u'b6', u'b5', u'b4', u'b3', u'b2', u'b1'])
        
        for x in ('a','b'):
            subfolder = testfolder + '/' + x
            for y in range(1,10):
                self.assertEqual(api.namespace.file(subfolder + '/' + str(x) + str(y)),"test_file")
                api.namespace.file_delete(subfolder + '/' + str(x) + str(y))
            
            api.namespace.dir_delete(subfolder)
            
    def test_access_points(self):
        api = isilon.API(fqdn,user,password,secure=False)
        
        #create and get listing again
        api.namespace.dir_create(testfolder)
        api.namespace.accesspoint_create(name='test_accesspoint',path=testfolder)

        self.assertEqual( api.namespace.accesspoint()['test_accesspoint'], testfolder)
        
        #test acls
        acl = api.namespace.accesspoint_getacl('test_accesspoint')
        api.namespace.accesspoint_setacl(name='test_accesspoint',acl=acl)
        
        #cleanup
        api.namespace.accesspoint_delete('test_accesspoint')
                        
    
        
       
        

if __name__ == '__main__':
    unittest.main()        
        
        
