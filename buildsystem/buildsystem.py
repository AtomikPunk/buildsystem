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
		self.options = opts
		self.outputs = [name]
		
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

	def showdeps(self, lvl = 0):
		print(' '*lvl + self.name + ' ' + str(self))
		for d in self.deps:
			d.showdeps(lvl = lvl+1)
		
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
				
		if isinstance(src, str):
			super().__init__(name = name, deps = [source(src)], opts = opts)
		else:
			super().__init__(name = name, deps = src, opts = opts)
		
class linkable(dependency):
	def __init__(self, name = None, deps = [], srcs = [], opts = None):
		srcdeps = []
		if isinstance(srcs, list):
			for s in srcs:
				srcdeps.append(compiled(src = s, opts = opts))
		if isinstance(deps, list):
			super().__init__(name = name, deps = deps + srcdeps, opts = opts)
		else:
			super().__init__(name = name, deps = [deps] + srcdeps, opts = opts)
		
class executable(linkable):
	pass
		
class sharedlib(linkable):
	pass
		
class staticlib(linkable):
	pass
		
class project(dependency):
	pass
