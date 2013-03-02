import os
import json
import re
import termios
import select
import signal
import fcntl
import tty
import errno
import struct
import array
import socket

class JsonLoader(object):
	KEY_INCLUDE = '#include'
	
	def __init__(self, incdirs=[]):
		self.incdirs = ['.'] + incdirs
	
	def __minify(self, json, strip_space):
		tokenizer = re.compile('"|(/\*)|(\*/)|(//)|\n|\r')
		in_string = False
		in_multiline_comment = False
		in_singleline_comment = False
		
		new_str = []
		from_index = 0 # from is a keyword in Python
		
		for match in re.finditer(tokenizer, json):
			if not in_multiline_comment and not in_singleline_comment:
				tmp2 = json[from_index:match.start()]
				if not in_string and strip_space:
					tmp2 = re.sub('[ \t\n\r]*','',tmp2) # replace only white space defined in standard
				new_str.append(tmp2)
				
			from_index = match.end()
			
			if match.group() == '"' and not in_multiline_comment and not in_singleline_comment:
				escaped = re.search('(\\\\)*$',json[:match.start()])
				if not in_string or escaped is None or len(escaped.group()) % 2 == 0:
					# start of string with ", or unescaped " character found to end string
					in_string = not in_string
				from_index -= 1 # include " character in next catch
				
			elif match.group() == '/*' and not in_string and not in_multiline_comment and not in_singleline_comment:
				in_multiline_comment = True
			elif match.group() == '*/' and not in_string and in_multiline_comment and not in_singleline_comment:
				in_multiline_comment = False
			elif match.group() == '//' and not in_string and not in_multiline_comment and not in_singleline_comment:
				in_singleline_comment = True
			elif (match.group() == '\n' or match.group() == '\r') and not in_string and not in_multiline_comment and in_singleline_comment:
				in_singleline_comment = False
			elif not in_multiline_comment and not in_singleline_comment and (match.group() not in ['\n','\r',' ','\t'] or not strip_space):
				new_str.append(match.group()) 
		
		new_str.append(json[from_index:])
		return ''.join(new_str)
	
	def __include(self, dict):
		if self.KEY_INCLUDE in dict:
			filename = dict[self.KEY_INCLUDE]
			inc = self.load(filename)
			dict.pop(self.KEY_INCLUDE)
			if len(dict):
				combo = {}
				combo.update(dict)
				combo.update(inc)
				return combo
			else:
				return inc
		return dict
	
	def __try_path(self, dir, filename):
		path = os.path.join(dir, filename)
		if os.path.exists(path):
			return path
		return None
	
	def __get_path(self, filename):
		for dir in self.incdirs:
			path = self.__try_path(dir, filename)
			if path:
				return path
		return None

	def load(self, filename):
		raw_json = open(self.__get_path(filename)).read()
		mini_json = self.__minify(raw_json, False)
		data = json.loads(mini_json, object_hook=self.__include)
		return data

class Terminal(object):
	def __init__(self, fd):
		self.fd = fd
		
	def fileno(self):
		return self.fd

	def read(self, size):
		return os.read(self.fd, size)
	
	def write(self, buf):
		os.write(self.fd, buf)
	
	def ioctl(self, *args):
		return fcntl.ioctl(self.fd, *args)
		
	def __enter__(self):
		self.oldtios = termios.tcgetattr(self.fd)
		#tty.setraw(self.fd)

		newtios = termios.tcgetattr(self.fd)

		I_IFLAG  = 0
		I_OFLAG  = 1
		I_CFLAG  = 2
		I_LFLAG  = 3
		I_ISPEED = 4
		I_OSPEED = 5
		I_CC     = 6

		#newtios[I_IFLAG] &= ~(termios.IGNBRK | termios.BRKINT)
		newtios[I_LFLAG] &= ~(termios.ECHO | termios.ICANON | termios.ISIG)
		newtios[I_CC][termios.VMIN] = 1
		newtios[I_CC][termios.VTIME] = 0
		
		termios.tcsetattr(self.fd, termios.TCSANOW, newtios)
	
	def __exit__(self, type, value, traceback):
		termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.oldtios)

ESC = b'0x01'

class Console(object):
	def __init__(self):
		self.escape = False
		self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		self.stdin = Terminal(sys.stdin.fileno())
		self.stdout = Terminal(sys.stdout.fileno())
		self.master = None
		
	def recv_fds(self, msglen, maxfds):
		fds = array.array("i")   # Array of ints
		msg, ancdata, flags, addr = self.sock.recvmsg(msglen, socket.CMSG_LEN(maxfds * fds.itemsize))
		for cmsg_level, cmsg_type, cmsg_data in ancdata:
			if (cmsg_level == socket.SOL_SOCKET and cmsg_type == socket.SCM_RIGHTS):
				# Append data, ignoring any truncated integers at the end.
				fds.fromstring(cmsg_data[:len(cmsg_data) - (len(cmsg_data) % fds.itemsize)])
		return msg, list(fds)
	
	def run(self):
		if not os.path.exists(CTRL_PATH):
			sys.exit('netlabd has not been started.')
		
		with self.stdin:
			#os.setsid()
			
			self.sock.connect(CTRL_PATH)
			msg, fds = self.recv_fds(1024, 1)
			self.master = Terminal(fds[0])
			
			signal.signal(signal.SIGWINCH, self.sigwinch)
			self.resize()
			
			self.mainloop()
	
	def resize(self):
		#struct winsize {
		#   unsigned short ws_row;
		#   unsigned short ws_col;
		#   unsigned short ws_xpixel;
		#   unsigned short ws_ypixel;
		#};
		_WINSIZEFMT = "HHHH"
		wsz = self.stdin.ioctl(termios.TIOCGWINSZ, '\0' * struct.calcsize(_WINSIZEFMT))
		self.master.ioctl(termios.TIOCSWINSZ, wsz)
		
	def sigwinch(self, sig, stack):
		self.resize()
	
	def mainloop(self):
		inputs = [self.stdin, self.master]
		
		while True:
			try:
				reads, writes, excepts = select.select(inputs, [], [])
			except OSError as e:
				if e.errno == errno.EINTR:
					continue
				else:
					raise
			if self.stdin in reads:
				if not self.stdin_handler():
					return
			if self.master in reads:
				if not self.master_handler():
					return
	
	def stdin_handler(self):
		ch = self.stdin.read(1)
		#print(hex(ord(ch)))
		if ch[0] == ESC and not self.escape:
			print('^A')
			self.escape = not self.escape
			return True
			
		if chr(ch[0]) == 'q' and self.escape:
			print('^A-q')
			return False
			
		self.escape = False
		self.master.write(ch)
		return True
	
	def master_handler(self):
		data = self.master.read(1024)
		self.stdout.write(data)
		return True
