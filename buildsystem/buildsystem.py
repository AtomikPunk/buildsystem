from enum import Enum

import os

verbose = False

class options(object):
	def __init__(self, cflags = set(), lflags = set(), defines = set(), incdirs = set(), intincdirs = set()):
		self.cflags = cflags
		self.lflags = lflags
		self.defines = defines
		self.incdirs = incdirs
		self.intincdirs = intincdirs

class node(object):
	def __init__(self, value = None, out_edges = []):
		self.value = value
		self.out_edges = out_edges
		
class dependency(node):
	def __init__(self, name = None, deps = [], opts = None):
		super().__init__(value = name, out_edges = deps)
		self.buildname = None
		self.options = opts
		
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
	def __init__(self, src = None, name = None, opts = None):
		if not name and isinstance(src, (str,)):
			(filename, ext) = os.path.splitext(src)
			if ext:
				name = filename
			else:
				name = src
				
		if type(src) is str:
			super().__init__(name = name, deps = [source(src)], opts = opts)
		else:
			super().__init__(name = name, deps = src, opts = opts)
		
class linkable(dependency):
	def __init__(self, name = None, deps = [], srcs = [], opts = None):
		if type(srcs) is list:
			if len(srcs) > 0:
				for s in srcs:
					deps.append(compiled(src = s, opts = opts))
		if not deps:
			if type(deps) is str:
				super().__init__(name = name, deps = [compiled(deps)], opts = opts)
			else:
				super().__init__(name = name, deps = [compiled(c) for c in deps], opts = opts)
		elif type(deps) is list:
			super().__init__(name = name, deps = deps, opts = opts)
		else:
			super().__init__(name = name, deps = [deps], opts = opts)
		
class executable(linkable):
	pass
		
class sharedlib(linkable):
	pass
		
class staticlib(linkable):
	pass
		
class project(dependency):
	pass
