import os
import json, datetime
import tempfile, re
import yaml
from . import VAR_PATH
from env import Environment
import tool

SESSION_JSON = 'session.json'
DOC_JSON = 'doc.json'

class CustomEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, datetime.datetime):
			return obj.isoformat()
		return super(CustomEncoder, self).default(obj)
	
class State(object):
	INIT = 'init'
	STARTING = 'starting'
	RUNNING = 'running'
	STOPPING = 'stopping'
	STOPPED = 'stopped'

class Session(object):
	def __init__(self, id, user, yaml, state):
		self.id = id
		self.user = user
		self.yaml = yaml
		self.state = state
		
	@staticmethod
	def Path(id):
		return os.path.join(VAR_PATH, id, SESSION_JSON)
	
	@property
	def path(self):
		return Session.Path(self.id)
		
	def dump(self):
		return {
			'id': self.id,
			'state': self.state,
			'user': self.user,
			'yaml': self.yaml
		}
		
	def save(self):
		with open(self.path, 'w') as fp:
			json.dump(self.dump(), fp, cls=CustomEncoder)
	
	@classmethod
	def Create(Class, user, yaml):
		dir = tempfile.mkdtemp(prefix='', dir=VAR_PATH)
		id = os.path.basename(dir)
		session = Class(id, user, yaml, State.INIT)
		session.save()
		session.__read_yaml()
		return session

	@classmethod
	def Load(Class, id):
		path = Class.Path(id)
		with open(path, 'r') as fp:
			data = json.load(fp)
			return Class(data['id'],
						 data['user'],
						 data['yaml'],
						 data['state'])
	
	def start(self, dry=False):
		env = Environment(tool.factory(dry))
		
		self.state = State.STARTING
		self.save()
		
		doc = self.__load_doc()

		#for node in self.doc.nodes:
		#	vm = self.vm_tbl[node.type](self.env, node)
		#	vm.start()
		#	self.vms.append(vm)

		self.state = State.RUNNING
		self.save()
	
	def stop(self, dry=False):
		env = Environment(tool.factory(dry))

		self.state = State.STOPPING
		self.save()

		doc = self.__load_doc()

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
		
		print(contents)
	
		doc = yaml.load(contents)
		self.__save_doc(doc)

		import pprint
		pprint.pprint(doc)
		#for kwargs in doc.get('vlans', {}):
		#	model = Model.Model(kwargs)
		#	vlan = Vlan(self.env, model)
		#	self.vlans.append(vlan)
		#	
		#for kwargs in doc.get('segments', {}):
		#	segment = Model.Segment(kwargs)
		#	self.__create_bridge(segment)
		#
		#for kwargs in doc.get('nodes', {}):
		#	node = Model.Node(kwargs)
		#	for ifc in node.interfaces.values():
		#		if ifc.plug:
		#			self.__create_bridge(ifc)
		#	self.nodes.append(node)
	
	def __load_doc(self):
		path = os.path.join(VAR_PATH, self.id, DOC_JSON)
		with open(path, 'r') as fp:
			return json.load(fp)
	
	def __save_doc(self, doc):
		path = os.path.join(VAR_PATH, self.id, DOC_JSON)
		with open(path, 'w') as fp:
			json.dump(doc, fp, cls=CustomEncoder)
