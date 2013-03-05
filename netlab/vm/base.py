import os
import string
import shutil
import logging

global_vars = {
	'VM_DIR'         : '$(WORK_DIR)',
	'VM_NODE'        : '$(VM_DIR)/nodes/$(name)',
	'VM_BASE'        : '$(VM_DIR)/base/$(rootfs|hash)',
	'VM_ROOT'        : '$(VM_NODE)/root',
	'VM_OVERLAY'     : '$(VM_NODE)/overlay',
	'VM_HTMP'        : '$(VM_NODE)/tmp',
	'VM_GTMP'        : '/host/tmp',
	'VM_MNT'         : '$(VM_ROOT)/host/$(mnt.name)',
}

class VirtualMachine:
	def __init__(self, env, node, vars):
		self.node = node

		new_vars = {}
		new_vars.update(node)
		new_vars.update(global_vars)
		new_vars.update(vars)
		
		self.env = env.extend(new_vars)
	
	def start_interfaces(self):
		for ifc in self.node.interfaces.values():
			if ifc.plug:
				env = self.env.extend(ifc=ifc)
				if ifc.plug == '$ADMIN':
					net = 'ADMIN_TAP'
				else:
					net = 'ifc.net.name'
				logging.warn('%s/%s: %s', self.node.name, ifc.name, ifc.tap)
				env.run('ip link add $(ifc.tap)')
				env.run('brctl addif $(ifc.net) $(ifc.tap)')
	
	def stop_interfaces(self):
		for ifc in self.node.interfaces.values():
			if ifc.plug:
				env = self.env.extend(ifc=ifc)
				if ifc.plug == '$ADMIN':
					net = 'ADMIN_TAP'
				else:
					net = 'ifc.net.name'
				try:
					env.run('brctl delif $(ifc.tap)')
					env.run('ip link del $(ifc.net) $(ifc.tap)')
				except Exception as e:
					logging.error(e)

	def prepare_overlay(self):
		self.env.run('mkdir -p $(VM_OVERLAY)')
		for overlay in self.node.overlays.values():
			root = self.env.resolve(overlay.path)
			logging.info('Creating overlay: %s', root)
			for path, dirs, files in os.walk(root):
				relpath = os.path.relpath(path, root)
				for filename in files:
					src = os.path.join(path, filename)
					dst = os.path.join(self.env.get('VM_OVERLAY'), relpath, filename)
					self.process_file(src, dst)

	"""
	Prepare config files that are specified in the <network>.yaml file.
	Each config file has a target path along with the actual contents.
	"""
	def prepare_config(self, root='$(VM_OVERLAY)'):
		root = self.env.resolve(root)
		for cfg in self.node.config:
			for (path, contents) in cfg.items():
				logging.debug('Preparing %s', path)
				if path.startswith('/'): path = path[1:]
				self.write_file([root, path], self.env.resolve(contents))
	
	def process_file(self, src, dst):
		dir = os.path.dirname(dst)
		if not os.path.exists(dir):
			self.env.run('mkdir -p $(dir)', dir=dir)
			
		if os.path.islink(src):
			logging.debug('Copying symlink %s -> %s', src, dst)
			
			linkto = os.readlink(src)
			if not os.path.exists(linkto):
				os.symlink(linkto, dst)
			return
	
		with open(src) as f:
			contents = f.read()
		
		if all(c in string.printable for c in contents) and contents.find('!!JINJA_IGNORE!!') == -1:
			# only try to expand text files
			logging.debug('Preparing %s -> %s', src, dst)
			contents = self.env.resolve(contents)
			mode = 'w'
		else:
			logging.debug('Copying %s -> %s', src, dst)
			mode = 'wb'
			
		self._write_file(dst, mode, contents)
		shutil.copystat(src, dst)

	def write_file(self, path_parts, contents):
		path = os.path.join(*path_parts)
		dir = os.path.dirname(path)
		if not os.path.exists(dir):
			self.env.run('mkdir -p $(dir)', dir=dir)
		
		self._write_file(path, 'w', contents)
	
	def _write_file(self, path, mode, contents):
		with open(path, mode) as f:
			f.write(contents)
			if mode == 'w':
				f.write('\n')
