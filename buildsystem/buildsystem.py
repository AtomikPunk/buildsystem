import subprocess
from enum import Enum

verbose = False
toolchain = None

class transformer(object):
	class TransformResults(Enum):
		OK = 0
		ERROR = 1
	in_exts = []
	out_ext = ''
	def check_supported(self, deps = []):
		return all(d.name[-4:] in self.in_exts for d in deps)

class toolchain(object):
	def __init__(self, transformers = []):
		self.transformers = transformers
	def transform(self, dep = None):
		pass

class node(object):
	def __init__(self, value = None, out_edges = []):
		self.value = value
		self.out_edges = out_edges
		
class dependency(node):
	def __init__(self, name = None, deps = []):
		super().__init__(value = name, out_edges = deps)
		self.filename = name
		
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
	
	def build(self):
		pass
		
	def uptodate(self):
		return False
		
class source(dependency):
	def __init__(self, name = None, file = None):
		super().__init__(name = name, deps = file)

class compiled(dependency):
	def __init__(self, src = None, name = None, cflags = None):
		self.cflags = cflags
		
		if not name and isinstance(src, (str,)):
			if src[-4:] == '.cpp':
				name = src[:-4]
			else:
				print('warning: unknown source file extension')
				name = src
				
		if type(src) is str:
			super().__init__(name = name, deps = [source(src)])
		else:
			super().__init__(name = name, deps = src)
	
	def build(self):
		if self.uptodate():
			return
			
		super().build()
		toolchain.transform(self)
		
class executable(dependency):
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
	
	def build(self):
		super().build()
		for d in self.deps:
			d.build()
		
		toolchain.transform(self)
		
class sharedlib(dependency):
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
	
	def build(self):
		super().build()
		for d in self.deps:
			d.build()
		
		toolchain.transform(self)
		
class staticlib(dependency):
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
	
	def build(self):
		super().build()
		for d in self.deps:
			d.build()
		
		toolchain.transform(self)
		
class project(dependency):
	def __init__(self, name = '', deps = []):
		super().__init__(name = name, deps = deps)

	def build(self):
		super().build()
		for d in self.deps:
			d.build()
		
class solution(project):
	def __init__(self, name = '', deps = []):
		super().__init__(name = name, deps = deps)
	
	def build(self):
		super().build()
