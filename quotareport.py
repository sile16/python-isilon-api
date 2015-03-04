#!/usr/bin/env python
import isilon
import argparse
import json
import logging
from os.path import expanduser
import getpass

fqdn = "192.168.167.101"
username = "root"
password = "a"


def main():

    parser = argparse.ArgumentParser(description='Report on user quotas')
    parser.add_argument('--file',  action='append', dest='files', default=[], help='file with list of users')
    parser.add_argument('--user',  action='append', dest='users', default=[], help='comma delimited list of users')
    parser.add_argument('--threshold', type=int, dest='threshold', help='Threshold 0<t<100')
    parser.add_argument('--quiet', action='store_true', dest='quiet',help='quiet')
   
    users = []
   
    args = parser.parse_args()
    
    #Read in Users from files
    for file in args.files:
        with open(file) as f:
            users = users + [line.rstrip('\n') for line in f]
    
    #Read in Users from users params
    for u in args.users:
        users = users + u.split(',')
        
    #if still no users, read in from file in homedir
    if len(users) == 0:
        #Import from home 
        file = expanduser("~/.quotareport-users")
        with open(file) as f:
            users = users + [line.rstrip('\n') for line in f]
    
    if len(users) == 0:
        users.append(getpass.getuser())
    
        
    
    #Initialize an api instance for platform api commands
    api = isilon.API(fqdn,username,password,secure=False)
    api.session.connect()
    
    print("Username Used(MB) Limit(MB) Capacity Share")
    for u in users:
        for q in api.platform.quota(persona="USER:" + u,type='user'):
            print('{0:8} {1:8} {2:9} {3}'.format(u,q['usage']['logical']/(1024**2), q['thresholds']['hard']/(1024**2),q['path']))
    

            
            
    



if __name__ == "__main__":
    main()