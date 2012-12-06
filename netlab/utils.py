import os
import json
import re

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

