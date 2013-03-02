install:
	@python setup.py install > /dev/null
	
netmgr: install
	./run_root netmgr -v
