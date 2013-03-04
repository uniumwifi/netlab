import re
import logging
import platform
import jinja2

ENV_JSON = 'env.json'

# environment of expansion variables
global_vars = {
	# system stuff
	'MACHINE'          : platform.machine(),
	#'SCREEN'           : 'screen -t $(name) $(cmd)',
	#'SCREEN_CMD'       : 'screen -p $(name) -X $(cmd)',
	#'SCREENRC'         : '$(PWD)/scripts/.screenrc',
	#'NETLAB_DIR'       : '$(HOME)/.uml',
	#'NETLAB_LOG'       : '$(NETLAB_DIR)/netlab.log',

	# coco stuff
	#'DVL'              : '$(PWD)/..',
	#'DVL_UML_BIN'      : '$(DVL)/output/uml_$(MACHINE)_debug/bin',
	#'DVL_HOST_BIN'     : '$(DVL)/output/linux_$(MACHINE)_debug/bin',
	#'DVL_OPENWRT_BIN'  : '$(DVL)/output/openwrt_uml_$(MACHINE)_debug/bin',
	#'DVL_OPENWRT'      : '$(DVL)/vendor/openwrt',
	#'DVL_WIFISIM'      : '$(DVL_HOST_BIN)/wifi_simd',
	#'MNT'              : '$(PWD)/mnt',
	#'GDVL'             : '/mnt/devel',
	#'GBIN'             : '$(GDVL)/output/openwrt_uml_$(MACHINE)_debug/bin',
	#'PY_CDL'           : '$(GDVL)/projects/gunis/r2ri/cdl/scapy/cdl.py',
	#'PY_TTNT'          : '$(GDVL)/projects/gunis/r2ri/ttnt/scapy/ttnt.py',
}

class Environment(object):
	# $(x), where x can be alphanumeric or underscore characters
	pattern = re.compile('\$\(([\w\.]+)\)')
	
	def __init__(self, tool, vars=global_vars):
		self.tool = tool
		self.vars = vars
		self.env = jinja2.Environment('{%', '%}', '$(', ')')
		self.env.filters['resolve'] = self.resolve
		self.env.filters['hash'] = self.hash

	def update(self, _vars={}, **kwargs):
		self.vars.update(_vars, **kwargs)
	
	def extend(self, _vars={}, **kwargs):
		new_vars = {}
		new_vars.update(self.vars)
		new_vars.update(_vars)
		new_vars.update(**kwargs)
		return Environment(self.tool, new_vars)

	def run(self, _cmd, _force=False, _bg=False, _cwd=None, _ignore=False, **kwargs):
		cmd = self.resolve(_cmd, **kwargs)

		if _cwd:
			_cwd = self.resolve(_cwd, **kwargs)

		logging.info(cmd)
		self.tool.run(cmd.split(), _force, _bg, _cwd, _ignore)
		
	def run_args(self, _cmd_args, _force=False, _bg=False, _cwd=None, _ignore=False, **kwargs):
		cmd_args = []
		for x in _cmd_args:
			cmd_args.append(self.resolve(x, **kwargs))

		if _cwd:
			_cwd = self.resolve(_cwd, **kwargs)

		logging.info(cmd_args)
		self.tool.run(cmd_args, _force, _bg, _cwd, _ignore)
	
	def run_output(self, _cmd, **kwargs):
		cmd = self.resolve(_cmd, **kwargs)
		logging.info(cmd)
		return self.tool.run_output(cmd.split())

	def hash(self, symbol, **kwargs):
		value = self.resolve(symbol, **kwargs)
		path = os.path.normpath(value)
		hash = hashlib.sha1(path).hexdigest()
		#print 'hash: %s -> %s' % (path, hash)
		return hash
		
	def get(self, symbol, **kwargs):
		return self._resolve('$(%s)' % symbol, True, **kwargs)
	
	def resolve(self, symbol, **kwargs):
		return self._resolve(symbol, False, **kwargs)

	def _resolve(self, symbol, first, **kwargs):
		ctx = {}
		ctx.update(self.vars)
		ctx.update(**kwargs)
		if first:
			missing = self._find_undeclared(symbol, ctx)
		else:
			missing = set()
		return self._recurse(symbol, ctx)
	
	def _recurse(self, symbol, ctx):
		result = self.env.from_string(symbol).render(ctx)
		missing = self._find_undeclared(result, ctx)
		#print '_recurse: "%s" -> "%s": %s %s %s' % (symbol, result, missing, last, history)
		if not missing:
			return result
		if result == symbol: # nothing changed
			raise jinja2.UndefinedError('Undefined symbol(s) remain in "%s": %s' % (result, missing))
		# TODO: detect loops
		return self._recurse(result, ctx)

	def _find_undeclared(self, symbol, ctx):
		missing = set()
		errors = set()
		for match in self.pattern.finditer(symbol):
			item = match.group(1)
			if not self._lookup(ctx, item):
				errors.add(item)
			missing.add(item)
		if errors:
			raise jinja2.UndefinedError('Undefined symbol(s) in "%s": %s' % (symbol, errors))
		return missing
	
	def _lookup(self, ctx, key):
		parts = key.split('.')
		cur = ctx
		for part in parts:
			if not cur.has_key(part):
				return False
			cur = cur.get(part)
			if cur is None:
				return False
		return True
	