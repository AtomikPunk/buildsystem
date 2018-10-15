import buildsystem.builders as bu
import buildsystem.buildsystem as bs
from buildsystem.consolecolors import consolecolors as cc

class config(object):
	def __init__(self, outdir='.bs'):
		self.outdir = outdir

class toolchain(object):
	def __init__(self, builders = {}, opts = None, cfg = None):
		super().__init__()
		self.builders = {
			bs.source: [bu.builder_alwaysuptodate()],
			bs.compiled: [bu.builder()],
			bs.executable: [bu.builder()],
			bs.sharedlib: [bu.builder()],
			bs.staticlib: [bu.builder()],
			bs.project: [bu.builder_alwaysuptodate()],
			}
		self.builders.update(builders)
		self.options = opts
		self.config = cfg

	def build(self, dep, opts = None):
		for d in dep.deps:
			self.build(d, opts = self.options or bs.options() + dep.options + opts or bs.options())
		if type(dep) in self.builders.keys():
			builders = self.builders[type(dep)]
			built = False
			for b in builders:
				if b.supports(dep):
					b.setuptarget(dep, self.config)
					if not b.up_to_date(dep):
						success = b.build(dep, opts = self.options or bs.options() + dep.options + opts or bs.options())
						if success:
							print('[' + cc().green + 'b' + cc().reset + '] ' + ','.join(dep.outputs))
						else:
							print('[' + cc().red + 'f' + cc().reset + '] ' + ','.join(dep.outputs))
					elif bs.verbose:
						print('[-] ' + ','.join(dep.outputs))
					built = True
					break
			if not built:
				print('warning: could not find builder for ' + dep.name + ' (' + dep.__class__.__name__ + ')')
		else:
			print('warning: could not find builder for type ' + str(type(dep)))
			
	def clean(self, dep):
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