#!/usr/bin/env python
import isilon
import logging
import argparse
import threading
import Queue
import json 
import time   
import httplib
import pprint
import collections

pp = pprint.PrettyPrinter(indent=4)
            
#httplib.HTTPConnection.debuglevel = 1
logging.basicConfig()  
logging.getLogger().setLevel(logging.INFO)

#Temporary snap name: should be unique
temp_snap = "tmp_snap_Rc9uHOSob50f"
 
class ThreadWorker(threading.Thread):
    """Threaded Folder Discovery and Copy"""
    def __init__(self, url, username, password, queue, clone, sleep, verify,stats):
        threading.Thread.__init__(self)
        self.url = url
        self.username = username
        self.password = password
        self.queue = queue
        self.clone = clone
        self.sleep = sleep
        self.verify = verify
        self.stats = stats
        
            
        
    def walk(self, workitem):
        for inode in self.api.namespace.dir(workitem['src']):             
            src = workitem['src'] + "/" + inode['name']
            dst = workitem['dst'] + "/" + inode['name']
            new_work = {"src": src, "dst": dst, "type": inode['type'] }
            self.queue.put(new_work)  
        

    def run(self):
        #Spawn thread API connections over a period of seconds to get a different IP from SmartConnect
        time.sleep(self.sleep)
        self.api = isilon.API(self.url, self.username, self.password)
        
        #The API lib will automatically make SSH connections as needed
        #However, connect SSH explicitly to spread out SSH connections over time
        #to avoid connection problems of trying to connect too many too quickly
        if self.clone:
            self.api.session.connect_SSH()
                
        while True :
            #grabs new work item from queue
            workitem = self.queue.get()
            logging.debug(workitem)
            
            if self.verify:
                if workitem['type'] == "container":
                    #This is a directory, scan it for more files/directories
                    self.walk(workitem)             
            
                #Compare ACLS for both objects and containers
                acl_src = self.api.namespace.acl(workitem['src'])
                try:
                    acl_dst = self.api.namespace.acl(workitem['dst'])
                    #The ACL is a list, so we have to sort them first before compare
                    acl_src['acl'] = sorted(acl_src['acl'])
                    acl_dst['acl'] = sorted(acl_dst['acl'])
                    
                    if acl_src != acl_dst:
                        self.stats['acl_error'] += 1
                        logging.error("ACL doesn't match: %s" % workitem['src'])       
                        pp.pprint(acl_src)
                        pp.pprint(acl_dst)
                    else:
                        self.stats['match'] += 1
                        
                except isilon.ObjectNotFound:
                    self.stats['missing'] += 1
                    logging.error("Destination file not found")
            else:
                    
                if workitem['type'] == "container":
                    #This is a directory, so create a new directory then scan it for more files/directories
                    self.api.namespace.dir_create(workitem['dst'])
                    self.walk(workitem)       
                    self.stats['folders'] +=1
                else:
                    self.api.namespace.file_copy(workitem['src'],workitem['dst'],clone=self.clone)
                    self.stats['files'] +=1
            
                #Apply ACLS for both objects and containers
                acls = self.api.namespace.acl(workitem['src'])
                self.api.namespace.acl_set(workitem['dst'], acls)
                
         
            #signal to queue job is done
            self.queue.task_done()
           

def main():

    parser = argparse.ArgumentParser(description='Create a copy of a directory')
    parser.add_argument('src',  help='source directory, full path starting with /ifs')
    parser.add_argument('dst',  help='destination directory, full path starting with /ifs')
    parser.add_argument('-i', required=True, dest='url', help='IP or DNS name of the cluster')
    parser.add_argument('-u', required=True, dest='username',help='API Username')
    parser.add_argument('-p', required=True, dest='password',help='API Password')
    parser.add_argument('-t', required=False, dest='threadcount', type=int, help='Thread Count, default=16', default=16)
    parser.add_argument('-c', action='store_true', dest='clone', help='Use sparse cloning technology')
    parser.add_argument('-v', action='store_true', dest='verify', help='Verify ACLS only, do not copy or clone')

    args = parser.parse_args()
    #Strip trailing slashes on paths
    args.dst = args.dst.rstrip('/')
    args.src = args.src.rstrip('/')
    
    logging.info(args)
    
    #Initialize an api instance for platform api commands
    api = isilon.API(args.url,args.username,args.password,secure=False)
    
    #make sure the paths provided map to an available access point
    src_ap = args.src.split('/')[1]
    dst_ap = args.dst.split('/')[1]
    
    if src_ap not in api.namespace.accesspoint():
        logging.error("AccessPoint not found: %s", src_ap)
        exit()
    
    if src_ap != dst_ap:
        logging.error("Source accesspoint: %s and destination accesspoint: %s must be the same.",src_ap,dst_ap)
        exit()
        
        
    
    
    #check if destination directory already exists
    try:
        api.namespace.is_dir(args.dst)
    except isilon.ObjectNotFound:
        #This is good we want the this to be not found unless we are verifying
        if args.verify:
            logging.error("Cannot find destination path")
            exit()
    else:
        if not args.verify:
            logging.error("Destination path already exists")
            exit()
    
    #check that source path exists and is a directory
    try:
        if not api.namespace.is_dir(args.src):
            logging.error("Source path is not a directory")
            exit()
    except isilon.ObjectNotFound:
        logging.error("Source path is not found")
        exit()
    
    #Check for old bad snaps and delete
    try:
        api.platform.snapshot(temp_snap)
        api.platform.snapshot_delete(temp_snap)
    except isilon.ObjectNotFound:
        pass
        
    #Create new snap
    api.platform.snapshot_create(temp_snap, args.src)
    
    #Put the first folder into the queue
    queue = Queue.Queue()
    queue.put( {"src": args.src + "/.snapshot/" + temp_snap , "dst": args.dst , "type":"container"} )
    
    #find out the cluster node count
    config = api.platform.config()
    node_count = len(config['devices'])
    logging.info("Node Count: %d" % node_count)
    logging.info(config['onefs_version']['version'])
    
    #If node count is more than thread count we don't want to wait more than 1 second per thread spawn
    spawn_time = min(node_count,args.threadcount)
    
    #Also, max of 5 SSH session per second to avoid connection problems
    if args.clone:
        spawn_time = max( args.threadcount / 5 , spawn_time)
    
    #spawn a pool of worker threads
    stats=[]
    for i in range(args.threadcount):
        #Calculate sleep amount so we can spawn maximum threads in shortest amount of time while still going across all nodes
        sleep = spawn_time * (i / float(args.threadcount))
        stats.append(collections.defaultdict(int))
        t = ThreadWorker( args.url, args.username, args.password , queue, args.clone , sleep, args.verify,stats[i])
        t.setDaemon(True)
        t.start()
       
    #Wait for all work items to complete
    queue.join()
    
    #Clean up snapshot
    api.platform.snapshot_delete(temp_snap)
    
    
    #sum all our stats form all threads
    totals = collections.defaultdict(int)
    for item in stats:
        for key in item:
            totals[key] += item[key]
    
    #Print Stats:
    print("\nStats:")
    for key in totals:
        print("%s : %d" % (key, totals[key]))  
    print("")
    
    
 
if __name__ == "__main__":
    main()
