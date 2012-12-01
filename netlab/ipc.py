import sys
import os
import socket
import struct

CTRL_PATH = '/var/run/netlabd.socket'

class PeerCredential(object):
	#struct ucred {
	#    pid_t pid;    /* process ID of the sending process */
	#    uid_t uid;    /* user ID of the sending process */
	#    gid_t gid;    /* group ID of the sending process */
	#};
	
	ucred_fmt = 'III'
	
	def __init__(self, buf):
		ucred = tuple(struct.unpack(self.ucred_fmt, buf))
		self.pid = ucred[0]
		self.uid = ucred[1]
		self.gid = ucred[2]
	
	@classmethod
	def buflen(self):
		return struct.calcsize(self.ucred_fmt)
	
	def __repr__(self):
		return '(%d, %d, %d)' % (self.pid, self.uid, self.gid)

class Session(object):
	def __init__(self, sock):
		self.socket = sock
		self.connected = False

	@classmethod
	def create(Class):
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		return Class(sock)
	
	def connect(self):
		if not self.connected:
			self.socket.connect(CTRL_PATH)
			self.connected = True

	@property
	def peercred(self):
		""" Get peer credentials on a UNIX domain socket."""
		SO_PEERCRED = 17
		buf = self.socket.getsockopt(socket.SOL_SOCKET, SO_PEERCRED, PeerCredential.buflen())
		return PeerCredential(buf)

	def send(self, msg):
		self.__send(msg.dump())

	def recv(self):
		return Message.load(self.__recv())
	
	def __send(self, msg):
		size = struct.pack('I', len(msg))
		self.socket.sendall(size)
		self.socket.sendall(msg)

	def __recv(self):
		#print '__recv> size'
		buf = self.socket.recv(struct.calcsize('I'))
		if not buf:
			return None
		size, = struct.unpack('I', buf)
		#print '__recv> %d data' % size
		return self.socket.recv(size)
