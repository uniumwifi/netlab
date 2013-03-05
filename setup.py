#!/usr/bin/env python

from distutils.core import setup

setup(
	name='netlab',
	version='1.0',
	description='Network Laboratory',
	author='Frank Laub',
	packages=['netlab', 'netlab.vm'],
	requires=[
	],
	scripts=[
		'bin/netmgr',
		'bin/netlab',
	],
	data_files=[
	]
)
