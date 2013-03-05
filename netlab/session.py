import os, stat
import json, datetime
import tempfile, re
import logging
import yaml
import tool
from . import VAR_PATH
from env import Environment
from doc import Document, Persist
from vm.uml import UserModeLinux

DeviceRegistry = {
	'uml': UserModeLinux
}

class State(object):
	INIT = 'init'
	STARTING = 'starting'
	DRY = 'dry'
	RUNNING = 'running'
	STOPPING = 'stopping'
	STOPPED = 'stopped'

class EnvFile(Persist):
	JSON_NAME = 'env.json'

	def __init__(self, id, env=None):
		self.id = id
		self.env = env

class Session(Persist):
	JSON_NAME = 'session.json'

	def __init__(self, user, yaml, env, envfiles):
		self.id = self.__next_id()
		self.user = user
		self.yaml = yaml
		self.state = State.INIT

		self.__save_env(env, envfiles)
		self.__read_yaml()

		self.save()

	def __next_id(self):
		for i in xrange(100):
			try:
				os.makedirs(os.path.join(VAR_PATH, str(i)), 0755)
				return i
			except Exception as e:
				pass

	@property
	def __dir(self):
		return os.path.join(VAR_PATH, str(self.id))
	
	def new_env(self, dry=False):
		user_env = EnvFile.Load(self.id)
		new_env = Environment(tool.create(dry))
		new_env.update(user_env.env, WORK_DIR=self.__dir)
		return new_env
	
	def start(self, dry=False):
		#env = self.new_env(dry)
		env = self.new_env(True)

		self.state = State.STARTING
		self.save()
		
		doc = Document.Load(self.id)

		for node in doc.nodes.values():
			device = DeviceRegistry[node.type](env, node)
			logging.info('starting %s...', node.name)
			device.start()

		if dry:
			self.state = State.DRY
		else:
			self.state = State.RUNNING
		self.save()
	
	def stop(self):
		dry = (self.state == State.DRY)
		env = Environment(tool.create(dry))

		self.state = State.STOPPING
		self.save()

		doc = Document.Load(self.id)

		for node in doc.nodes.values():
			device = DeviceRegistry[node.type](env, node)
			logging.info('stopping %s...', node.name)
			device.stop()

		self.state = State.STOPPED
		self.save()
	
	def __save_env(self, env, envfiles):
		new_env = {}
		for f in envfiles:
			with open(f) as fp:
				file_env = json.load(fp)
				new_env.update(file_env)
		new_env.update(env)

		EnvFile(self.id, new_env).save()
		
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
		
		doc = Document(self, yaml.load(contents))
		doc.save()
	