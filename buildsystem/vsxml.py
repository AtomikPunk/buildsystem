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
