import collections

class Model(dict):
	__seqno = 0
	
	def __init__(self, initialdata={}):
		self.id = self.__unique_id()
		super(Model, self).__init__(initialdata)

	def __getattr__(self, key):
		return self[key]

	def __setattr__(self, key, value):
		self[key] = value

	def load_tree(self, name, Class):
		dict = self.get(name, {})
		for k, v in dict.items():
			dict[k] = Class(self, k, v)
		self[name] = dict
	
	def load_list(self, name, Class):
		cur = self.get(name, [])
		new = []
		for i, item in enumerate(cur):
			new.append(Class(self, i, item))
		self[name] = new

	@classmethod
	def __unique_id(self):
		self.__seqno += 1
		return self.__seqno

class Item(Model):
	def __init__(self, parent, name, data):
		Model.__init__(self, data)
		self.parent = parent
		self.name = name
		
	#def __repr__(self):
	#	return '%s(name=%s)' % (self.__class__.__name__, self.name)
	
class Document(Model):
	def __init__(self, data):
		Model.__init__(self, data)
		self.load_tree('profiles', Profile)
		self.load_tree('bridges', Bridge)
		self.load_tree('nodes', Node)

class Profile(Item):
	pass

class Bridge(Item):
	def __init__(self, parent, name, data):
		Item.__init__(self, parent, name, data)
		self.load_list('ports', Port)

class Port(Item):
	def __init__(self, parent, name, data):
		Item.__init__(self, parent, name, data)

class Node(Item):
	def __init__(self, parent, name, data):
		Item.__init__(self, parent, name, data)
		self.load_tree('interfaces', Interface)

class Interface(Item):
	def __init__(self, parent, name, data):
		Item.__init__(self, parent, name, data)

