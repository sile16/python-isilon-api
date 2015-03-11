#API Usage Example
#==========
#To use: Modify the fqdn, username, and password


import isilon
import time
import logging

def main():
	fqdn = '192.168.167.101'  #change to your cluster
	username = 'root'
	password = 'a'
	
	#httplib.HTTPConnection.debuglevel = 1
	logging.basicConfig()  
	logging.getLogger().setLevel(logging.CRITICAL)
	logging.captureWarnings(True)


	#connect, secure=False allows us to bypass the CA validation
	api = isilon.API(fqdn, username, password, secure=False)

	# not necessary as it will connect automatically on auth failure
	# but this avoids the initial attempt failure
	print("Connecting")
	api.session.connect()
	
	
		
	#Check for old bad snaps and delete
	print("Checking for older snaps")	
	if api.platform.snapshot('testsnap') :
		print("We found an existing testsnap, let's delete that...")
		api.platform.snapshot_delete('testsnap')
	
	 	
	#This shows how we can pass params directly to the API though specifically not called
	#out as a param for the snapshot_create function.  	
	print("create a snapshot on %s, to expire in 60 seconds" % testfolder )
	api.platform.snapshot_create("testsnap",testfolder,expires=int(time.time()+60))
	
	print("confirm test snapshot was created details:")
	print(api.platform.snapshot('testsnap'))

	print("Modify the snapshot expire time and rename to testsnap2")
	api.platform.snapshot_modify('testsnap',name='testsnap2',expires=int(time.time() + 120))
	
	print("Rename back testsnap")
	api.platform.snapshot_modify('testsnap2',name='testsnap')

	#debug last API call:
	api.session.debug_last()
	
	#list all snaps
	print('\nListing of All Snaps:')
	for snap in api.platform.snapshot(limit=2):
		print("Name: %s, Path: %s, Created: %s" % (snap['name'], snap['path'], time.ctime(snap['created']) ))

	#cleanup our testnsap
	api.platform.snapshot_delete('testsnap')


	print("list all quotas")
	for q in api.platform.quota():
		pcnt_used = 100 * q['usage']['logical'] / q['thresholds']['hard']
		print("Path %s  Persona: %s   Percent Used: %s" % (q['path'] , q['persona'], pcnt_used))
	
			
			
		 
if __name__ == "__main__":
    main()