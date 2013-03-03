import os
import json, datetime
import tempfile
from . import VAR_PATH

SESSION_JSON = 'session.json'
MODEL_JSON = 'model.json'

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
	
	def start(self):
		self.state = State.STARTING
		self.save()
	
	def stop(self):
		self.state = State.STOPPING
		self.save()
