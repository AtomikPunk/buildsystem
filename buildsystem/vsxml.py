import io
 
class vsxml(object):
	def __init__(self, stream, indentsymbol = '  '):
		self.stream = stream
		self.currentlevel = 0
		self.indentsymbol = indentsymbol
		self.inline = []
		self.tag = []
		self.attr = []

	def write(self, data):
		if not self.inline:
			self.stream.write(self.indentsymbol*self.currentlevel)
		self.stream.write(data)
		if not self.inline:
			self.stream.write('\n')

	def writeEmptyEl(self, tag, attr = []):
		self.stream.write(self.indentsymbol*self.currentlevel)
		self.stream.write('<' + tag)
		for a in attr:
		   self.stream.write(' ' + a[0] + '="' + a[1] + '"')
		self.stream.write(' />\n')

	def writeDeclaration(self):
		self.write('<?xml version="1.0" encoding="utf-8"?>')

	def el(self, tag, attr = [], inline = False):
		self.tag.append(tag)
		self.inline.append(inline)
		self.attr = attr
		return self

	def __enter__(self):
		# Opening tag
		#if not self.inline[-1]:
		self.stream.write(self.indentsymbol*self.currentlevel)
		self.stream.write('<' + self.tag[-1])
		for a in self.attr:
		   self.stream.write(' ' + a[0] + '="' + a[1] + '"')
		self.stream.write('>')
		if not self.inline[-1]:
			self.stream.write('\n')
		self.currentlevel += 1
		return self

	def __exit__(self, type, value, traceback):
		# Closing tag
		self.currentlevel -= 1
		if not self.inline[-1]:
			self.stream.write(self.indentsymbol*self.currentlevel)
		self.stream.write('</' + self.tag[-1] + '>')
		self.stream.write('\n')
		self.tag.pop()
		self.inline.pop()

class attribute(object):
	def __init__(self, name, value = None):
		self.name = name
		self.value = value

class element(object):
	def __init__(self, name):
		self.children = []
		self.attributes = {}
		self.name = name

class vsxml2reader(object):
	def __init__(self):
		self.str = None
		self.parsedindex = None

	def read(self, fileName):
		with open(fileName) as f:
			return self.fromstring(f.read())

	def fromstring(self, str, index = 0):
		self.str = str

		# Skip XML declaration
		if self.str.find('<?', index) != -1:
			self.parsedindex = self.str.find('?>') + 2

		# Root element
		idx = self.str.find('<', self.parsedindex)
		rootnode = self.parseelement(idx)
		
		return rootnode

	def parseelement(self, beg):
		idx = self.locateelement(beg)
		self.parsedindex = idx[1]
		components = self.str[idx[0] + 1 : idx[1] - 1].split(' ')
		name = components.pop(0)
		#print('vsxml: ' + name)
		if not len(components):
			empty = False
		else:
			empty = components[-1] == '/'
			if empty:
				components.pop()

		e = element(name)
		if components:
			e.attributes = self.parseattributes(components)

		if empty:
			return e

		idx = self.locateelement(idx[1] + 1)
		while idx is not None:
			# Text content
			txt = self.str[self.parsedindex : idx[0]].strip()
			if txt:
				e.children.append(txt)

			self.parsedindex = idx[1]
			if self.str[idx[0] + 1] == '/':
				tag = self.str[idx[0] + 2 : idx[1] - 1]
				if tag == e.name:
					# Closing current element
					#print('vsxml: /' + tag)
					return e

				raise ValueError('vsxml error: invalid closing element at index ' + str(idx[0]) + ', expected </' + e.name + '>')
			else:
				e.children.append(self.parseelement(idx[0]))
			idx = self.locateelement(self.parsedindex + 1)

		return e

	def locateelement(self, beg):
		begidx = self.str.find('<', beg)
		if begidx == -1:
			return None

		endidx = self.str.find('>', begidx)
		if endidx == -1:
			raise ValueError('vsxml error: could not find closing xml bracket from index ' + begidx)

		return (begidx, endidx + 1)

	def parseattributes(self, alist):
		attr = {}
		for a in alist:
			pair = a.split('=')
			if len(pair) < 2:
				pair = pair
			key = pair[0]
			value = pair[1].strip('"')
			attr[key] = value
		return attr

class vsxml2writer(object):
	def __init__(self):
		self.indentlevel = 0
		self.indentsymbol = '  '

	def write(self, fileName, node):
		with open(fileName, 'w') as f:
			f.write(self.tostring(node))

	def tostring(self, node):
		s = ''
		s += self.prolog()
		s += self.elementtostring(node)
		return s

	def elementtostring(self, node):
		s = ''
		s += self.indentlevel*self.indentsymbol + '<' + node.name
		for k,v in node.attributes.items():
			s += ' ' + k + '="' + v + '"'
		if node.children:
			s += '>'
			self.indentlevel += 1
			haselement = False
			for c in node.children:
				if isinstance(c, str):
					# text
					s += c
				elif isinstance(c, element):
					# element
					s += '\n' + self.elementtostring(c)
					haselement = True
			self.indentlevel -= 1
			if haselement:
				s += '\n' + self.indentlevel*self.indentsymbol
			s += '</' + node.name + '>'
		else:
			s += ' />'
		return s

	def prolog(self):
		return '<?xml version="1.0" encoding="utf-8"?>\n'

if __name__ == "__main__":
	r = vsxml2reader()
	xml = r.read('test.vcxproj')

	w = vsxml2writer()
	w.write('testwrite.vcxproj', xml)
