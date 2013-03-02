#!/usr/bin/env python

import argparse
import lib
import pprint

DEFAULT_URL = 'http://localhost:999'

def do_list(args):
	lab = lib.NetLab(args.url)
	r = lab.list()
	pprint.pprint(r)

def do_clear(args):
	# TODO: double check user with a prompt
	lab = lib.NetLab(args.url)
	lab.clear()

def do_create(args):
	lab = lib.NetLab(args.url)
	r = lab.create(args.file)
	pprint.pprint(r)

def do_view(args):
	lab = lib.NetLab(args.url)
	r = lab.view(args.session)
	pprint.pprint(r)

def do_delete(args):
	lab = lib.NetLab(args.url)
	r = lab.delete(args.session)
	pprint.pprint(r)

def do_start(args):
	lab = lib.NetLab(args.url)
	r = lab.start(args.session)
	pprint.pprint(r)

def do_stop(args):
	lab = lib.NetLab(args.url)
	r = lab.stop(args.session)
	pprint.pprint(r)

def main():	
	parser = argparse.ArgumentParser(description='NetLab command line utility')

	base_parser = argparse.ArgumentParser(add_help=False)
	base_parser.add_argument('-u', '--url', default=DEFAULT_URL,
							 help='Connection URL')
	base_parser.add_argument('-v', '--verbose', action='count', default=0,
							 help='Increase verbosity, can be specified multiple times')
	base_parser.add_argument('-q', '--quiet', action='store_true', default=False,
							 help='Be really quiet')
	
	item_parser = argparse.ArgumentParser(add_help=False, parents=[base_parser])
	item_parser.add_argument('-s', '--session', required=True,
							 help='Session identifer')
	
	commands = parser.add_subparsers(title='commands')

	cmd_list = commands.add_parser('list', parents=[base_parser])
	cmd_list.set_defaults(func=do_list)

	cmd_clear = commands.add_parser('clear', parents=[base_parser])
	cmd_clear.set_defaults(func=do_clear)

	cmd_create = commands.add_parser('create', parents=[base_parser])
	cmd_create.set_defaults(func=do_create)
	cmd_create.add_argument('-f', '--file', required=True,
							help='Specify yaml descriptor file')
	
	cmd_view = commands.add_parser('view', parents=[item_parser])
	cmd_view.set_defaults(func=do_view)

	cmd_delete = commands.add_parser('delete', parents=[item_parser])
	cmd_delete.set_defaults(func=do_delete)

	cmd_start = commands.add_parser('start', parents=[item_parser])
	cmd_start.set_defaults(func=do_start)

	cmd_stop = commands.add_parser('stop', parents=[item_parser])
	cmd_stop.set_defaults(func=do_stop)

	args = parser.parse_args()
	args.func(args)
