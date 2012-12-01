#!/usr/bin/env python

import os
from paver.easy import *
from paver.setuputils import setup

setup(
	name='umlab',
	version='1.0',
	description='Network Laboratory',
	author='Frank Laub',
	author_email='flaub@cococorp.com',
	packages=[ 'umlab', 'umlab.vm' ],
	scripts=['bin/umlab'],
	data_files=[
		('/usr/sbin', ['bin/umlabd']),
		('/etc/supervisor/conf.d', ['cfg/umlabd.conf'])
	],
	requires=[
		'yaml',
		'ipaddr',
		'jinja2',
	]
)

def which(program):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file
	return None

@task
@needs('paver.setuputils.install')
def install(options, info):
	info('installing daemon...')
	if not which('supervisorctl'):
		sys.exit('Missing supervisor. Run apt-get install supervisor.')
	os.system('supervisorctl reload')
