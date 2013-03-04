import os, stat
import json, datetime
import tempfile, re
import yaml
from . import VAR_PATH
from env import Environment
from doc import Document, Persist
import tool

class State(object):
	INIT = 'init'
	STARTING = 'starting'
	RUNNING = 'running'
	STOPPING = 'stopping'
	STOPPED = 'stopped'
	
class Session(Persist):
	JSON_NAME = 'session.json'

	def __init__(self, user, yaml):
		dir = tempfile.mkdtemp(prefix='', dir=VAR_PATH)
		# allow everyone read access
		os.chmod(dir, os.stat(dir).st_mode |
				 stat.S_IRGRP | stat.S_IXGRP |
				 stat.S_IROTH | stat.S_IXOTH)

		self.id = os.path.basename(dir)
		self.user = user
		self.yaml = yaml
		self.net_id = 100
		self.state = State.INIT
		self.save()
		self.__read_yaml()

		env = self.new_env()
	
	@property
	def __dir(self):
		return os.path.join(VAR_PATH, self.id)
	
	def new_env(self, dry=False):
		return Environment(tool.create(dry)).extend(WORK_DIR=self.__dir)
	
	def start(self, dry=False):
		env = self.new_env(dry)

		self.state = State.STARTING
		self.save()
		
		doc = Document.Load(self.id)
		for node in doc.nodes.values():
			print node.index

		#for node in self.doc.nodes:
		#	vm = self.vm_tbl[node.type](self.env, node)
		#	vm.start()
		#	self.vms.append(vm)

		self.state = State.RUNNING
		self.save()
	
	def stop(self, dry=False):
		env = Environment(tool.create(dry))

		self.state = State.STOPPING
		self.save()

		doc = Document.Load(self.id)

		self.state = State.STOPPED
		self.save()
		
	def __yaml_include(self, m):
		base = os.path.dirname(self.yaml)
		path = os.path.join(base, m.group(1))
		with open(path) as f:
			return f.read()
	
	def __read_yaml(self):
		with open(self.yaml) as f:
			contents = f.read()
		
		pattern = re.compile('^\#include[\s]+([\S]+)[\s]*$', re.MULTILINE)
		contents = pattern.sub(self.__yaml_include, contents)
		
		#print(contents)
	
		doc = Document(self, yaml.load(contents))
		doc.save()

		import pprint
		pprint.pprint(doc)
	