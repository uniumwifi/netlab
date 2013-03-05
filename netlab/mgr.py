#!/usr/bin/env python

import sys, os, shutil
import argparse, logging
import bottle
from . import VAR_PATH
from session import Session
from doc import Document

LOG_PATH = '/var/log/netmgr.log'

@bottle.route('/sessions')
def sessions_list():
	logging.info("sessions_list()")
	ls = os.listdir(VAR_PATH)
	return { 'keys': ls }

@bottle.route('/sessions', method='POST')
def sessions_new():
	kwargs = bottle.request.json
	logging.info("sessions_new(): %s" % kwargs)
	session = Session(**kwargs)
	return { 'id': session.id }

@bottle.route('/sessions', method='DELETE')
def sessions_clear():
	logging.info("sessions_clear()")
	ls = os.listdir(VAR_PATH)
	for entry in ls:
		shutil.rmtree(os.path.join(VAR_PATH, entry))

@bottle.route('/sessions/<id>')
def sessions_get(id):
	logging.info("sessions_get(%s)" % id)
	return bottle.static_file(Session.JSON_NAME, root=os.path.join(VAR_PATH, id))

@bottle.route('/sessions/<id>/doc')
def sessions_doc_get(id):
	logging.info("sessions_get(%s)" % id)
	return bottle.static_file(Document.JSON_NAME, root=os.path.join(VAR_PATH, id))

@bottle.route('/sessions/<id>', method='DELETE')
def sessions_delete(id):
	logging.info("sessions_delete(%s)" % id)
	# TODO: check that 'id' does NOT have slashes (/) or updirs (..)
	path = os.path.join(VAR_PATH, id)
	shutil.rmtree(path)

@bottle.route('/sessions/<id>/start', method='POST')
def sessions_start(id):
	kwargs = bottle.request.json
	logging.info("sessions_start(%s): %s" % (id, kwargs))
	session = Session.Load(id)
	session.start(**kwargs)
	return { 'status': 'starting' }

@bottle.route('/sessions/<id>/stop', method='POST')
def sessions_stop(id):
	logging.info("sessions_stop(%s)" % id)
	session = Session.Load(id)
	session.stop()
	return { 'status': 'stopping' }

@bottle.route('/sessions/<id>/console', method='POST')
def sessions_console(id):
	logging.info("sessions_console(%s)" % id)
	return { 'status': 'ok' }


def init_logging(options):
	# NOTE: this call can only be done ONCE
	# and it MUST be the 1st call into the logging module for it to work
	logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)-15s %(message)s',
						filename=options.log,
						filemode='w')

	console = logging.StreamHandler()
	if options.quiet:
		console.setLevel(logging.ERROR)
	else:
		if options.verbose == 1:
			console.setLevel(logging.INFO)
		elif options.verbose >= 2:
			console.setLevel(logging.DEBUG)
		else:
			console.setLevel(logging.WARN)
	logging.getLogger().addHandler(console)

def parse_args():
	parser = argparse.ArgumentParser(description='NetLab Manager')
	parser.add_argument('-v', '--verbose', action='count', default=0,
						help='Increase verbosity, can be specified multiple times')
	parser.add_argument('-q', '--quiet', action='store_true', default=False,
						help='Be really quiet')
	parser.add_argument('-L', '--log', default=LOG_PATH,
						help='Specify the logfile')
	return parser.parse_args()

def main():
	if os.getuid() != 0:
		sys.exit('netmgr must be run as root.')
		
	if not os.path.exists(VAR_PATH):
		os.makedirs(VAR_PATH)

	args = parse_args()

	init_logging(args)

	logging.info("Starting")
	
	bottle.run(host='localhost', port=999, debug=True)

	logging.info("Shutdown")
	logging.shutdown()
	
