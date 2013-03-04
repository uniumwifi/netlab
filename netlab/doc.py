import os
import random
import logging
import ipaddr
import jsonpickle
from . import VAR_PATH, NET_START

class Model(dict):
	def __init__(self, initialdata={}):
		#self.update(initialdata)
		super(Model, self).__init__(initialdata)

	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			# turn KeyError into None
			return None
	
	def __setattr__(self, key, value):
		self[key] = value
		
	def load_dict(self, ctx, name, Class):
		seq = self.get(name, [])
		d = {}
		for i, v in enumerate(seq):
			k = v['name']
			d[k] = Class(ctx, self, i, k, v)
		self[name] = d
	
	def load_list(self, ctx, name, Class):
		seq = self.get(name, [])
		new = []
		for i, item in enumerate(seq):
			new.append(Class(ctx, self, i, item))
		self[name] = new
		
class IndexedItem(Model):
	def __init__(self, parent, index, data):
		Model.__init__(self, data)
		self.parent = parent
		self.index = index

class NamedItem(IndexedItem):
	def __init__(self, ctx, parent, index, name, data):
		IndexedItem.__init__(self, parent, index, data)
		self.name = name

class Persist(object):
	def save(self):
		with open(self.__path, 'w') as fp:
			fp.write(jsonpickle.encode(self))

	@classmethod
	def Load(Class, id):
		with open(Class.Path(id), 'r') as fp:
			return jsonpickle.decode(fp.read())

	@classmethod
	def Path(self, id):
		return os.path.join(VAR_PATH, str(id), self.JSON_NAME)
	
	@property
	def __path(self):
		return self.Path(self.id)
		
class Context(object):
	def __init__(self, session):
		self.seq_tap = 0
		self.seq_net = 0
		self.seq_admin = 0
		self.session = session
		self.networks = {}
	
	def alloc_tap(self):
		ret = 'tap-%s-%d' % (self.session.id, self.seq_tap)
		self.seq_tap += 1
		return ret
	
	def alloc_net(self, name):
		seq = self.networks.get(name)
		if not seq:
			seq = self.seq_net
			self.seq_net += 1
			self.networks[name] = seq
		return 'net-%s-%d' % (self.session.id, seq)
	
	def alloc_admin(self, node):
		ret = ipaddr.IPv4Network('10.8.%d.%d/24' % (NET_START + self.session.id, node.index + 10))
		logging.warn('%s: %s', node.name, ret)
		return ret

	def alloc_mac(self, ipaddr):
		# Don't think that we have to worry about explicitly assigning MAC addresses
		# with purely virtual networks (UML seems to assign them random MAC addresses).
		# However in networks with a mix of virtual and physical devices it's
		# important to keep MAC addresses consistent.
		#
		# Among other things if the MACs change ARP will get confused for physical
		# routers connected to virtual hosts when the network is brought back up.
		# There are also somewhat mysterious "Acceptance check failed" errors with
		# multicast on Cisco routers connected to the source which seem to be related
		# to MAC addresses changing.
		x = map(int, str(ipaddr.ip).split('.'))
		mac = [ 0x02, 0xCC, x[0], x[1], x[2], x[3] ]
		return ':'.join(map(lambda x: '%02x' % x, mac))
	
class Document(Model, Persist):
	JSON_NAME = 'doc.json'
	
	def __init__(self, session, data):
		Model.__init__(self, data)
		
		self.id = session.id
		
		ctx = Context(session)
		
		self.load_dict(ctx, 'vlans', NamedItem)
		self.load_dict(ctx, 'segments', Segment)
		self.load_dict(ctx, 'nodes', Node)

class Segment(NamedItem):
	def __init__(self, ctx, parent, index, name, data):
		NamedItem.__init__(self, ctx, parent, index, name, data)
		self.net = ctx.alloc_net(self.plug)

class Node(NamedItem):
	def __init__(self, ctx, parent, index, name, data):
		NamedItem.__init__(self, ctx, parent, index, name, data)
		
		# set default values
		self.profile = data.get('profile', 'coco')
		self.vmargs = data.get('vmargs', '')
		self.config = data.get('config', {})
		self.memory = data.get('memory', '64M')

		self.load_dict(ctx, 'mounts', NamedItem)
		self.load_dict(ctx, 'overlays', NamedItem)
		self.load_dict(ctx, 'interfaces', Interface)
		
		self.dsdv_enabled = any([
			ifc for ifc in self.interfaces.values() if ifc.dsdv_mode
		])
		self.ospf_enabled = any([
			ifc for ifc in self.interfaces.values() if ifc.ospf
		])
		self.bgp_enabled = any([
			ifc for ifc in self.interfaces.values() if ifc.bgp
		])

class Interface(NamedItem):
	def __init__(self, ctx, parent, index, name, data):
		NamedItem.__init__(self, ctx, parent, index, name, data)

		if self.plug == '$ADMIN':
			self.ipaddr = ctx.alloc_admin(self.parent)
		else:
			self.ipaddr = ipaddr.IPNetwork(data.get('ip', '0.0.0.0'))

		self.ports = data.get('ports', [])
		self.pim = data.get('pim', True)
		self.igmp = data.get('igmp', True)
		self.mac = data.get('mac', ctx.alloc_mac(self.ipaddr))
		self.tap = ctx.alloc_tap()
		self.net = ctx.alloc_net(self.plug)
