install:
	python setup.py install > /dev/null
	
daemon: install
	./run_root netlabd
	
