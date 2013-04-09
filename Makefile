install:
	@python setup.py install > /dev/null
	
netmgr: install
	scripts/run_root netmgr -v
