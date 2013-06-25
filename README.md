python-isilon-api
=================

An unofficial python library to make Isilon API calls. This library is incomplete, 
not fully tested, and not supported by EMC. I only plan to fill in the features as 
I need them.  Use at your own risk.

This is a library I created in order to make a copy tool with the goal 
of learning the API.  That said, it does work in my environment and
may be useful to others working with the API. 

####Tested with:

- OneFS 7.0.2.1
- Python 2.7.3
- HTTP Requests 1.2.3
- Paramiko 1.10.1 (SSH support in order to do file clones)

API Features
============
- Automatic Session/Connection management
- Effecient resuse of HTTP connections
- Automatic handling of paged directory listing using resume tokens
- Some basic error handling of sessions

cp.py Features
==============
- Copies or clones a source directory to a target directory
- Multithreaded
- Intelligently connects to multiple nodes in the cluster
- Applies ACLs to target files
- Can run in verify mode to only compare ACLS



    


    
    
    
    
