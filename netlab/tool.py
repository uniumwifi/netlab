import time
import subprocess

def create(dry):
	if dry:
		return DryTool()
	else:
		return Tool()

class DryTool(object):
	def sleep(self, secs):
		print('sleep(%s)' % secs)

	def run(self, cmd, bg, cwd, ignore):
		pass

	def run_output(self, cmd):
		pass

class Tool(object):
	def sleep(self, secs):
		time.sleep(secs)
	
	def run(self, cmd, bg, cwd, ignore):
		args = {
			'stdout'    : subprocess.PIPE,
			'stderr'    : subprocess.PIPE,
			'cwd'       : _cwd,
			'close_fds' : True,
		}
		
		p = subprocess.Popen(cmd, **args)
		try:
			if bg:
				# TODO: spin thread to read stdout & stderr
				pass
			else:
				stdout, stderr = p.communicate()
				for line in stdout.splitlines():
					logging.info(line.rstrip())
				for line in stderr.splitlines():
					logging.error(line.rstrip())
			if not ignore and p.returncode:
				raise subprocess.CalledProcessError(p.returncode, cmd)
			return p
		finally:
			if p and not bg:
				p.stdout.close()
				p.stderr.close()

	def run_output(self, cmd):
		p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		return p.communicate()[0]
