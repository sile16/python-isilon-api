import isilon
import logging
import argparse
import pprint


def main():
    parser = argparse.ArgumentParser(description='list api docs')
    parser.add_argument('-url', dest='url',  default='', help='filter only paths with this string in it')
    parser.add_argument('-method',  dest='method', default='get', help='method')
    parser.add_argument('-v', action='store_true',dest='verbose',default=False,help='verbose')
  
    args = parser.parse_args()

    api = isilon.API("192.168.167.101","root","a", secure=False)
    pp = pprint.PrettyPrinter(indent=4)

    data = api.session.api_call("GET","/platform/1/?describe&list&all")

    all_keys = {}

    for dir in data['directory']:

        if not args.url or args.url == dir:
            
            data1 = api.session.api_call("GET","/platform" + dir + "?describe&json")

           # print(data1)
            if not data1 is None:
                for k in data1:  
                    all_keys[k] = True
    
    
            all_args = dir + '  Props: '
            if (not data1 is None):
                for key in data1:
                    if args.method .upper() in key.upper() and 'properties' in data1[key]:
                        print(key)
                        if args.verbose:
                            pp.pprint(data1[key])
                        
                        for prop in data1[key]['properties']:
                            
                            all_args = all_args + prop + ', '
                            
                        print(all_args)
        
    print('')
    print("Available keys %s" % str(all_keys))

if __name__  == '__main__':
    main()
    
