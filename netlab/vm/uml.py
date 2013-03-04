import os
import re
import string
import time
import logging
import umlab
import subprocess
from . import VirtualMachine

global_vars = {
	'UML_DIR'          : '$(VM_DIR)/uml',
	'UML_NODE'         : '$(UML_DIR)/$(name)',
	'UML_COW'          : '$(UML_NODE)/root.cow',
	'UML_MCONSOLE'     : '$(UML_NODE)/mconsole',
	'UML_MCONSOLE_CMD' : 'uml_mconsole $(UML_MCONSOLE) $(cmd)',
	'UML_ETH_ARG'      : '$(ifc.name)=tuntap,$(ifc.tap),$(ifc.mac)',
	'UML_WIFI_ARG'     : '$(ifc.name)=wifi,$(ifc.bind)',
	'UML_ROOTFS'       : 'ubd0=$(UML_COW):$(rootfs)',
	'TMUX_NEWW'        : 'tmux new-window -n $(name)',
	'TMUX_KILL'        : 'tmux kill-window -t umlab:$(name)',
	'UML_START'        : '$(UML_START1) $(UML_START2)',
	'UML_START1'       : '$(vmlinux) $(vmargs) $(UML_ROOTFS) mem=$(memory) uml_dir=$(UML_DIR)',
	'UML_START2'       : 'umid=$(name) $(ifc_args) $(mnt_args) con=null ssl=null $(user_console) $(test_console)',
	'UML_USER_CONSOLE' : 'con0=null,fd:2 ssl0=fd:0,fd:1',
	'UML_TEST_CONSOLE' : 'con1=tty:$(tty)',
	'UML_MNT'          : '$(mnt_type)_$(mnt.name)=$(mnt.path)',
	'UML_OVERLAY'      : 'overlay_shadow=$(VM_OVERLAY)',
}

def init(env):
	env.update(global_vars)
	return UserModeLinux

class UserModeLinux(VirtualMachine):
	def __init__(self, env, node):
		VirtualMachine.__init__(self, env, node)

	def start(self):
		self.env.rmdir('$(UML_NODE)')
		
		self.prepare_overlay()
		self.prepare_config()
		self.start_interfaces()

		user_console = ''
		if self.env.options.interactive:
			user_console = self.env.get('UML_USER_CONSOLE')
		test_console = ''
		if self.env.options.test:
			test_console = self.env.get('UML_TEST_CONSOLE', tty=os.ttyname(self.node.slave))

		logging.warn('starting %s...', self.node.name)

		tmux = self.env.get('TMUX_NEWW')
		cmd = self.env.get('UML_START',
						   ifc_args=string.join(self.prepare_ifargs()),
						   mnt_args=string.join(self.prepare_mounts()),
						   user_console=user_console,
						   test_console=test_console)
		#self.env.system(cmd, _bg=True)
		args = tmux.split() + [ cmd ]
		logging.info(args)
		if not self.env.options.dry_run:
			process = subprocess.Popen(args, stderr = subprocess.PIPE)
			time.sleep(0.5)
			process.poll()
			if process.returncode != None:
				if process.returncode == 0:
					# see http://redmine.coco.sea/projects/root/wiki/UmLab
					logging.error('new terminal exited prematurely: were the UML instances built?')	
				else:
					logging.error('VM failed to run: return code is %s' % process.returncode)
				logging.error('stderr: %s' % process.stderr)
		
	def stop(self, phase):
		logging.warn('stopping %s...', self.node.name)
		
		if phase == 0:
			for i in range(3):
				logging.info('trying to stop')
				self.env.system('$(TMUX_KILL)', _ignore=True)
		elif phase == 1:
			self.stop_interfaces()
			self.env.rmdir('$(UML_NODE)')
		
	def prepare_ifargs(self):
		if_args = []
		for ifc in self.node.interfaces.values():
			env = self.env.extend(ifc=ifc)
			if ifc.plug:
				if_args.append(env.get('UML_ETH_ARG'))
			if ifc.bind:
				if_args.append(env.get('UML_WIFI_ARG'))
		return if_args

	def prepare_mounts(self):
		mnt_args = [
			self.env.get('UML_OVERLAY')
		]
		for mnt in self.node.mounts.values():
			env = self.env.extend(mnt=mnt)
			path = env.resolve('$(mnt.path)')
			if not os.path.exists(path):
				os.makedirs(path)
			mnt_args.append(env.get('UML_MNT', mnt_type='mnt'))
		return mnt_args
