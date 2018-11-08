from enum import Enum

import copy
import os

verbose = False

class options(object):
	def __init__(self, cflags = set(), lflags = set(), defines = {}, incdirs = set(), libdirs = set()):
		self.cflags = cflags
		self.lflags = lflags
		self.defines = defines
		self.incdirs = incdirs
		self.libdirs = libdirs
	
	def __add__(self, other):
		opts = copy.copy(self)
		if isinstance(other, options):
			opts.cflags.update(other.cflags)
			opts.lflags.update(other.lflags)
			opts.defines.update(other.defines)
			opts.incdirs.update(other.incdirs)
			opts.libdirs.update(other.libdirs)
		return opts

	def print(self):
		if self.cflags:
			print('cflags: ' + ','.join(self.cflags))
		if self.lflags:
			print('lflags: ' + ','.join(self.lflags))
		if self.defines:
			print('defines: ' + ','.join(self.defines))
		if self.incdirs:
			print('incdirs: ' + ','.join(self.incdirs))
		if self.libdirs:
			print('libdirs: ' + ','.join(self.libdirs))

class node(object):
	def __init__(self, value = None, out_edges = []):
		self.value = value
		self.out_edges = out_edges
		
class dependency(node):
	def __init__(self, name = None, deps = [], opts = options(), privopts = options()):
		super().__init__(value = name, out_edges = deps)
		self.options = opts
		self.privateoptions = privopts
		self.outputs = []
		
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
	def __init__(self, src = None, name = None, opts = options(), privopts = options()):
		if not name and isinstance(src, (str,)):
			(filename, ext) = os.path.splitext(src)
			if ext:
				name = filename
			else:
				name = src
				
		if isinstance(src, str):
			super().__init__(name = name, deps = [source(src)], opts = opts, privopts = privopts)
		else:
			super().__init__(name = name, deps = src, opts = opts, privopts = privopts)
		
class linkable(dependency):
	def __init__(self, name = None, deps = [], srcs = [], opts = options()):
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

class importlib(linkable):
	def __init__(self, name = None, deps = [], libs = set(), opts = options(), mods = {}):
		super().__init__(name = name, deps = deps, opts = opts)
		self.libs = libs
		self.modules = mods
		
	def withmods(self, modnames = set()):
		result = copy.copy(self)
		mods = [result.modules[n] for n in modnames if n in result.modules]
		result.deps = mods
		return result
		