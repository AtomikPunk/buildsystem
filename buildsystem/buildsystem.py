import subprocess
from enum import Enum

verbose = False

class builder(object):
	class BuildResults(Enum):
		OK = 0
		ERROR = 1
	def supports(self, dep):
		return True
	def build(self, dep):
		if self.up_to_date(dep):
			print('[-] ' + dep.name)
			return
		print('[b] ' + dep.name)
	def up_to_date(self, dep):
		return False

class toolchain(object):
	def __init__(self, builders = {}):
		super().__init__()
		self.builders = {
			source: [builder()],
			compiled: [builder()],
			executable: [builder()],
			sharedlib: [builder()],
			staticlib: [builder()],
			project: [builder()],
			}
		self.builders.update(builders)
	def build(self, dep):
		for d in dep.deps:
			self.build(d)
		if type(dep) in self.builders.keys():
			builders = self.builders[type(dep)]
			built = False
			for b in builders:
				if b.supports(dep):
					# print(' trying builder ' + b.__class__.__name__ + ' for ' + dep.name + ' (' + dep.__class__.__name__ + ')')
					b.build(dep)
					built = True
			if not built:
				print('warning: could not find builder for ' + dep.name + ' (' + dep.__class__.__name__ + ')')
		else:
			print('warning: could not find builder for type ' + str(type(dep)))

class node(object):
	def __init__(self, value = None, out_edges = []):
		self.value = value
		self.out_edges = out_edges
		
class dependency(node):
	def __init__(self, name = None, deps = []):
		super().__init__(value = name, out_edges = deps)
		self.builtname = name
		
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
	def __init__(self, src = None, name = None, cflags = None):
		self.cflags = cflags
		
		if not name and isinstance(src, (str,)):
			name = src
				
		if type(src) is str:
			super().__init__(name = name, deps = [source(src)])
		else:
			super().__init__(name = name, deps = src)
		
class linkable(dependency):
	def __init__(self, name = None, deps = [], srcs = [], cflags = None, lflags = None):
		self.lflags = lflags
		
		if type(srcs) is list:
			if len(srcs) > 0:
				for s in srcs:
					deps.append(compiled(src = s, cflags = cflags))
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
	def __init__(self, name = None, deps = [], srcs = [], cflags = None, lflags = None):
		super().__init__(name = name, deps = deps, srcs = srcs, cflags = cflags, lflags = lflags)
		
class sharedlib(linkable):
	def __init__(self, name = None, deps = [], srcs = [], cflags = None, lflags = None):
		super().__init__(name = name, deps = deps, srcs = srcs, cflags = cflags, lflags = lflags)
		
class staticlib(linkable):
	def __init__(self, name = None, deps = [], srcs = [], cflags = None, lflags = None):
		super().__init__(name = name, deps = deps, srcs = srcs, cflags = cflags, lflags = lflags)
		
class project(dependency):
	def __init__(self, name = '', deps = []):
		super().__init__(name = name, deps = deps)
