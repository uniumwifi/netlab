import urlparse
import requests

class NetLab(object):
	def __init__(self, url):
		self.__base = url
	
	def list(self):
		url = urlparse.urljoin(self.__base, '/sessions')
		r = requests.get(url)
		return r.json()
	
	def clear(self):
		url = urlparse.urljoin(self.__base, '/sessions')
		requests.delete(url)
	
	def view(self, id):
		url = urlparse.urljoin(self.__base, '/sessions/%s' % id)
		r = requests.get(url)
		return r.json()

	def create(self, yaml):
		url = urlparse.urljoin(self.__base, '/sessions')
		payload = { 'yaml': yaml }
		r = requests.post(url, params=payload)
		return r.json()
	
	def delete(self, id):
		url = urlparse.urljoin(self.__base, '/sessions/%s' % id)
		r = requests.delete(url)
	
	def start(self, id):
		url = urlparse.urljoin(self.__base, '/sessions/%s/start' % id)
		r = requests.post(url)
		return r.json()
	
	def stop(self, id):
		url = urlparse.urljoin(self.__base, '/sessions/%s/stop' % id)
		r = requests.post(url)
		return r.json()
	