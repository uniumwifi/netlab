#!/usr/bin/env python

from distutils.core import setup

setup(
	name='netlab',
	version='1.0',
	description='Network Laboratory',
	author='Frank Laub',
	packages=['netlab'],
	requires=[
	],
	scripts=[
		'bin/netmgr',
		'bin/netlab',
	],
	data_files=[
	]
)
