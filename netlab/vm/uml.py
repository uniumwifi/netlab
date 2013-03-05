import os
import string
import logging
from base import VirtualMachine

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
	'UML_START2'       : 'umid=$(name) $(ifc_args) $(mnt_args) con=null ssl=null $(UML_CONSOLE)',
	'UML_CONSOLE'      : 'con0=null,fd:2 ssl0=fd:0,fd:1',
	'UML_MNT'          : '$(mnt_type)_$(mnt.name)=$(mnt.path)',
	'UML_OVERLAY'      : 'overlay_shadow=$(VM_OVERLAY)',
}

class UserModeLinux(VirtualMachine):
	def __init__(self, env, node):
		VirtualMachine.__init__(self, env, node, global_vars)

	def start(self):
		self.prepare_overlay()
		self.prepare_config()
		self.start_interfaces()

		tmux = self.env.get('TMUX_NEWW')
		cmd = self.env.get('UML_START',
						   ifc_args=string.join(self.prepare_ifargs()),
						   mnt_args=string.join(self.prepare_mounts()))
		args = tmux.split() + [ cmd ]

		self.env.run_args(args)
		
	def stop(self, phase):
		self.env.run('$(TMUX_KILL)')
		self.stop_interfaces()
		
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
