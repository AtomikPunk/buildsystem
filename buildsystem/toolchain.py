import buildsystem.builders as bu
import buildsystem.buildsystem as bs
from buildsystem.consolecolors import consolecolors as cc

class config(object):
	def __init__(self, outdir='.bs'):
		self.outdir = outdir

class toolchain(object):
	def __init__(self, builders = {}, opts = bs.options(), cfg = config()):
		super().__init__()
		self.builders = {
			bs.source: [bu.builder_alwaysuptodate(self)],
			bs.compiled: [bu.builder(self)],
			bs.executable: [bu.builder(self)],
			bs.sharedlib: [bu.builder(self)],
			bs.staticlib: [bu.builder(self)],
			bs.project: [bu.builder(self)],
			bs.importlib: [bu.builder_alwaysuptodate(self)],
			}
		self.builders.update(builders)
		self.options = opts
		self.config = cfg

	def build(self, dep):
		# Inherit and propagate options to and from dependencies
		self.setupoptions(dep)
		self.builddep(dep)

	def builddep(self, dep):
		for d in dep.deps:
			self.builddep(d)
		if type(dep) in self.builders.keys():
			builders = self.builders[type(dep)]
			built = False
			for b in builders:
				if b.supports(dep):
					b.setuptarget(dep, self.config)
					if not b.up_to_date(dep):
						success = b.build(dep)
						if success:
							print('[' + cc().green + 'b' + cc().reset + '] ' + dep.name + ': ' + ','.join(dep.outputs))
						else:
							print('[' + cc().red + 'f' + cc().reset + '] ' + dep.name + ': ' + ','.join(dep.outputs))
					#elif bs.verbose:
						#print('[-] ' + ','.join(dep.outputs))
					built = True
					break
			if not built:
				print('warning: could not find builder for ' + dep.name + ' (' + dep.__class__.__name__ + ')')
		else:
			print('warning: could not find builder for type ' + str(type(dep)))
			
	def clean(self, dep):
		if isinstance(dep, set):
			dep = dep
		for d in dep.deps:
			self.clean(d)
		if type(dep) in self.builders.keys():
			builders = self.builders[type(dep)]
			cleaned = False
			for b in builders:
				if b.supports(dep):
					b.setuptarget(dep, self.config)
					if b.need_clean(dep):
						b.clean(dep)
						print('[' + cc().green + 'c' + cc().reset + '] ' + ','.join(dep.outputs))
					elif bs.verbose:
						print('[-] ' + ','.join(dep.outputs))
					cleaned = True
					break
			if not cleaned:
				print('warning: could not find cleaner for ' + dep.name + ' (' + dep.__class__.__name__ + ')')
		else:
			print('warning: could not find cleaner for type ' + str(type(dep)))

	def showdeps(self, dep):
		dep.showdeps()

	def setupoptions(self, dep):
		# Inherit options to dependencies
		inherited = {k:v for k,v in dep.options.items() if 'inherited' in v.attributes}
		for k,v in inherited.items():
			for d in dep.deps:
				d.options.updateifexist(k, dep.options)

		for d in dep.deps:
			self.setupoptions(d)

		# Propagate options from dependencies
		propagated = {k:v for k,v in dep.options.items() if 'propagated' in v.attributes}
		for k,v in propagated.items():
			for d in dep.deps:
				dep.options.updateifexist(k, d.options)

	def mergeoptions(self, dep, parentoptions, additionaloptions = None):
		effectiveoptions = bs.options()

		for k,v in effectiveoptions.items():
			effectiveoptions.updateifexist(k, self.options)
			if 'inherited' in v.attributes:
				effectiveoptions.updateifexist(k, parentoptions)
			if 'propagated' in v.attributes:
				for d in dep.deps:
					effectiveoptions.updateifexist(k, self.mergeoptions(d, dep.options))
			effectiveoptions.updateifexist(k, dep.options)
			effectiveoptions.updateifexist(k, additionaloptions)

		return effectiveoptions
