import isilon
import logging






api = isilon.API("isilon2.lab.local","root","a", False)

r = api.session.api_call("GET","/platform/1/?describe&list&all")

data = r.json()

for dir in data['directory']:
    if 'cloud' in dir:
        pass
        
    
    r = api.session.api_call("GET","/platform" + dir + "?describe&json")

        
    data1 = r.json()
   # print(data1)
    
    all_args = dir + '  Props: '
    if (not data1 is None) and 'GET_args' in data1 and 'properties' in data1['GET_args']:
        for prop in data1['GET_args']['properties']:
            all_args = all_args + prop + ', '
        
        print(all_args)
