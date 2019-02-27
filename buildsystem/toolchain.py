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

	def build(self, dep, opts = bs.options()):
		options = self.options + dep.options + opts
		inheritedoptions = bs.options()
		for d in dep.deps:
			self.build(d, opts = options)
			inheritedoptions += d.options
		dep.inheritedoptions = inheritedoptions
		if type(dep) in self.builders.keys():
			builders = self.builders[type(dep)]
			built = False
			for b in builders:
				if b.supports(dep):
					b.setuptarget(dep, self.config)
					if not b.up_to_date(dep):
						success = b.build(dep, opts = options)
						if success:
							print('[' + cc().green + 'b' + cc().reset + '] ' + ','.join(dep.outputs))
						else:
							print('[' + cc().red + 'f' + cc().reset + '] ' + ','.join(dep.outputs))
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

	def mergeoptions(self, dep, additionaloptions = None):
		effectiveoptions = bs.options()

		# Compilation
		# Defines
		if isinstance(self.options, (bs.options,)):
			effectiveoptions.defines.update(self.options.defines)
		if isinstance(dep.options, (bs.options,)):
			effectiveoptions.defines.update(dep.options.defines)
		if isinstance(additionaloptions, (bs.options,)):
			effectiveoptions.defines.update(additionaloptions.defines)

		# Include dirs
		if isinstance(self.options, (bs.options,)):
			effectiveoptions.incdirs.update(self.options.incdirs)
		if isinstance(dep.options, (bs.options,)):
			effectiveoptions.incdirs.update(dep.options.incdirs)
		if isinstance(dep.privateoptions, (bs.options,)):
			effectiveoptions.incdirs.update(dep.privateoptions.incdirs)
		if isinstance(dep.inheritedoptions, (bs.options,)):
			effectiveoptions.incdirs.update(dep.inheritedoptions.incdirs)
		if isinstance(additionaloptions, (bs.options,)):
			effectiveoptions.incdirs.update(additionaloptions.incdirs)

		# Cflags
		if isinstance(self.options, (bs.options,)):
			effectiveoptions.cflags.update(self.options.cflags)
		if isinstance(dep.options, (bs.options,)):
			effectiveoptions.cflags.update(dep.options.cflags)
		if isinstance(dep.privateoptions, (bs.options,)):
			effectiveoptions.cflags.update(dep.privateoptions.cflags)
		if isinstance(additionaloptions, (bs.options,)):
			effectiveoptions.cflags.update(additionaloptions.cflags)

		# Linking
		# Libdirs
		if isinstance(self.options, (bs.options,)):
			effectiveoptions.libdirs.update(self.options.libdirs)
		if isinstance(dep.options, (bs.options,)):
			effectiveoptions.libdirs.update(dep.options.libdirs)
		if isinstance(dep.inheritedoptions, (bs.options,)):
			effectiveoptions.libdirs.update(dep.inheritedoptions.libdirs)
		if isinstance(additionaloptions, (bs.options,)):
			effectiveoptions.libdirs.update(additionaloptions.libdirs)

		# Lflags
		if isinstance(self.options, (bs.options,)):
			effectiveoptions.lflags.update(self.options.lflags)
		if isinstance(dep.options, (bs.options,)):
			effectiveoptions.lflags.update(dep.options.lflags)
		if isinstance(dep.inheritedoptions, (bs.options,)):
			effectiveoptions.lflags.update(dep.inheritedoptions.lflags)
		if isinstance(additionaloptions, (bs.options,)):
			effectiveoptions.lflags.update(additionaloptions.lflags)

		return effectiveoptions
