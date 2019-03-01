from enum import Enum

import copy
import os
from buildsystem.consolecolors import consolecolors as cc

verbose = False

class readspecargs(object):
	def __init__(self, file):
		self.file = file

class execspecargs(object):
	def __init__(self, spec, tasks, toolchain, verbose = False, enablecolors = False):
		self.spec = spec
		self.tasks = tasks
		self.toolchain = toolchain
		self.verbose = verbose
		self.enablecolors = enablecolors

		if isinstance(tasks, str):
			self.tasks = [t for t in tasks.strip().split(',')]

def readspec(readspecargs):
	s = None
	try:
		import importlib.util
		import importlib.machinery
		importlib.machinery.SOURCE_SUFFIXES.append('') # Allow any file extension
		spec = importlib.util.spec_from_file_location('buildscript', readspecargs.file)
		mod = importlib.util.module_from_spec(spec)
		importlib.machinery.SOURCE_SUFFIXES.pop() # Revert to known file extensions

		spec.loader.exec_module(mod)
		if not hasattr(mod, 'spec'):
			raise RuntimeError('build script must define spec')

		s = mod.spec

	except Exception as e:
		print('Error: could not load build script ' + readspecargs.file + ' : ' + str(e))

	return s

def execspec(execspecargs):
	verbose = execspecargs.verbose
	cc.enable = execspecargs.enablecolors

	# print('\n'.join([str(b) for b in vc.builders]))

	for t in execspecargs.tasks:
		op = getattr(execspecargs.toolchain, t, None)
		if callable(op):
			print('Task: ' + t)
			op(execspecargs.spec)
		else:
			print('Warning: unsupported task ' + t)

class option(object):
	def __init__(self, name = None, value = None, attributes = {}):
		self.name = name
		self.value = value
		self.attributes = attributes

class options(dict):
	def __init__(self, cflags = set(), lflags = set(), defines = {}, incdirs = set(), libdirs = set()):
		self.setdefault('cflags', option('cflags', cflags, {'inherited'}))
		self.setdefault('defines', option('defines', defines, {'inherited'}))
		self.setdefault('incdirs', option('incdirs', incdirs, {'propagated'}))
		self.setdefault('lflags', option('lflags', lflags, {'inherited'}))
		self.setdefault('libdirs', option('libdirs', libdirs, {'propagated'}))
	
	def print(self):
		for o,v in self.items():
			print(o + ': ' + ','.join(v.values) + ' [' + ','.join(v.attributes) + ']')

	def merge(self, other):
		for k,v in self.items():
			self.updateifexist(k,other)

	def updateifexist(self, name, other):
		if name not in self:
			return

		if not isinstance(other, options):
			return

		if name not in other:
			return

		if other.get(name) is not None:
			self.get(name).value.update(other.get(name).value)

class node(object):
	def __init__(self, value = None, out_edges = {}):
		self.value = value
		if isinstance(out_edges, set):
			self.out_edges = out_edges
		else:
			self.out_edges = set(out_edges)
		
class dependency(node):
	def __init__(self, name = None, deps = set(), opts = options(), privopts = options()):
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
		if isinstance(deps, set):
			self.out_edges = deps
		else:
			self.out_edges = set(deps)

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
			super().__init__(name = name, deps = {source(src)}, opts = opts, privopts = privopts)
		else:
			super().__init__(name = name, deps = src, opts = opts, privopts = privopts)
		
class linkable(dependency):
	def __init__(self, name = None, deps = set(), srcs = [], opts = options()):
		srcdeps = set()
		if isinstance(srcs, list):
			for s in srcs:
				srcdeps.add(compiled(src = s, opts = opts))
		if isinstance(srcs, set):
			for s in list(srcs):
				srcdeps.add(compiled(src = s, opts = opts))
		if isinstance(deps, set):
			super().__init__(name = name, deps = deps.union(srcdeps), opts = opts)
		elif isinstance(deps, list):
			super().__init__(name = name, deps = set(deps).union(srcdeps), opts = opts)
		else:
			super().__init__(name = name, deps = {deps}.union(srcdeps), opts = opts)
		
class executable(linkable):
	pass
		
class sharedlib(linkable):
	pass
		
class staticlib(linkable):
	pass
		
class project(dependency):
	pass

class importlib(linkable):
	def __init__(self, name = None, deps = set(), libs = set(), opts = options(), mods = {}):
		super().__init__(name = name, deps = deps, opts = opts)
		self.libs = libs
		self.modules = mods
		
	def withmods(self, modnames = set()):
		result = copy.copy(self)
		mods = [result.modules[n] for n in modnames if n in result.modules]
		result.deps = mods
		return result
		