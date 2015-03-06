#!/usr/bin/env python
import isilon
import argparse
import json
import logging
from os.path import expanduser
import getpass
import os
import sys

fqdn = "192.168.167.101"
username = "root"
password = "a"


def main():

    parser = argparse.ArgumentParser(description='Report on user quotas')
    parser.add_argument('--file',  action='append', dest='files', default=[], help='file with list of users')
    parser.add_argument('--user',  action='append', dest='users', default=[], help='comma delimited list of users')
    parser.add_argument('--threshold', type=int, dest='threshold', default=-1, help='Threshold 0<t<100')
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
        if os.path.isfile(file):
            with open(file) as f:
                users = users + [line.rstrip('\n') for line in f]
    
    #If still no users read in current user username
    if len(users) == 0:
        users.append(getpass.getuser())
    
        
    
    #Initialize an api instance for platform api commands
    api = isilon.API(fqdn,username,password,secure=False)
    api.session.connect()
    if not args.quiet:
        print("Username Used(MB) Limit(MB) Capacity      Share")
    
    return_code=1
    for u in users:
        for q in api.platform.quota(persona="USER:" + u,type='user'):
            pcnt = 100.0 * q['usage']['logical'] / q['thresholds']['hard'] 
            if pcnt > args.threshold:                
                return_code=0
                
                if not args.quiet:
                    print('{0:8} {1:7} {2:8}  %{3:3} {4}'.format(u,q['usage']['logical']/(1024**2), q['thresholds']['hard']/(1024**2), pcnt, q['path']))
    
    exit(return_code)
    

            
            
    



if __name__ == "__main__":
    main()