import isilon
import logging






api = isilon.API("192.168.167.101","root","a", secure=False)

data = api.session.api_call("GET","/platform/1/?describe&list&all")

all_keys = {}

for dir in data['directory']:
    if 'cloud' in dir:
        pass
        
    
    data1 = api.session.api_call("GET","/platform" + dir + "?describe&json")

        

   # print(data1)
    if not data1 is None:
        for k in data1:  
            all_keys[k] = True
    
    
    all_args = dir + '  Props: '
    if (not data1 is None) and 'GET_args' in data1 and 'properties' in data1['GET_args']:
        for prop in data1['GET_args']['properties']:
            all_args = all_args + prop + ', '
        
        print(all_args)
        
print(all_keys)
