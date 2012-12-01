#!/usr/bin/env python3

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
		'bin/netlabd',
		'bin/netlab',
	],
	data_files=[
	]
)
