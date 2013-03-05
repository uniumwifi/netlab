import os
import urlparse
import requests
import errno
import getpass
import string
import json

class NetLab(object):
	def __init__(self, url):
		self.__base = url
		
	def __url(self, path):
		return urlparse.urljoin(self.__base, path)
	
	def list(self):
		r = requests.get(self.__url('/sessions'))
		return r.json()
	
	def clear(self):
		requests.delete(self.__url('/sessions'))
	
	def view(self, id):
		session = requests.get(self.__url('/sessions/%s' % id))
		doc = requests.get(self.__url('/sessions/%s/doc' % id))
		return {
			'session': session.json(),
			'doc': doc.json()
		}

	def create(self, yaml, envs, envfiles):
		if not os.path.exists(yaml):
			raise IOError(errno.ENOENT, "File not found", yaml)
		for f in envfiles:
			if not os.path.exists(f):
				raise IOError(errno.ENOENT, "File not found", f)
			
		env = {}
		for e in envs:
			(k, v) = e.split('=', 1)
			env[k] = v
		
		data = {
			'user': getpass.getuser(),
			'yaml': os.path.abspath(yaml),
			'env': env,
			'envfiles': map(os.path.abspath, envfiles)
		}
		headers = {'content-type': 'application/json'}
		r = requests.post(self.__url('/sessions'), headers=headers, data=json.dumps(data))
		return r.json()
	
	def delete(self, id):
		r = requests.delete(self.__url('/sessions/%s' % id))
	
	def start(self, id):
		r = requests.post(self.__url('/sessions/%s/start' % id))
		return r.json()
	
	def stop(self, id):
		r = requests.post(self.__url('/sessions/%s/stop' % id))
		return r.json()
	