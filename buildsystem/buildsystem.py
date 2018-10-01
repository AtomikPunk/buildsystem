from enum import Enum

verbose = False

class node(object):
	def __init__(self, value = None, out_edges = []):
		self.value = value
		self.out_edges = out_edges
		
class dependency(node):
	def __init__(self, name = None, deps = []):
		super().__init__(value = name, out_edges = deps)
		self.buildname = name
		
	@property
	def name(self):
		return self.value
	@name.setter
	def name(self, name):
		self.value = name
		
	@property
	def deps(self):
		return self.out_edges
	@deps.setter
	def deps(self, deps):
		self.out_edges = deps
		
class source(dependency):
	def __init__(self, name = None):
		super().__init__(name = name)

class compiled(dependency):
	def __init__(self, src = None, name = None, incdirs = [], intincdirs = [], cflags = None):
		self.cflags = cflags
		self.incdirs = incdirs
		self.intincdirs = intincdirs
		
		if not name and isinstance(src, (str,)):
			name = src
				
		if type(src) is str:
			super().__init__(name = name, deps = [source(src)])
		else:
			super().__init__(name = name, deps = src)
		
class linkable(dependency):
	def __init__(self, name = None, deps = [], srcs = [], incdirs = [], intincdirs = [], cflags = None, lflags = None):
		self.lflags = lflags
		
		if type(srcs) is list:
			if len(srcs) > 0:
				for s in srcs:
					deps.append(compiled(src = s, incdirs = incdirs, intincdirs = intincdirs, cflags = cflags))
		if not deps:
			if type(deps) is str:
				super().__init__(name = name, deps = [compiled(deps)])
			else:
				super().__init__(name = name, deps = [compiled(c) for c in deps])
		elif type(deps) is list:
			super().__init__(name = name, deps = deps)
		else:
			super().__init__(name = name, deps = [deps])
		
class executable(linkable):
	pass
		
class sharedlib(linkable):
	pass
		
class staticlib(linkable):
	pass
		
class project(dependency):
	pass
