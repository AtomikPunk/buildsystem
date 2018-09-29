import buildsystem.builders as bu
import buildsystem.buildsystem as bs

class toolchain(object):
	def __init__(self, builders = {}):
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
	def build(self, dep):
		for d in dep.deps:
			self.build(d)
		if type(dep) in self.builders.keys():
			builders = self.builders[type(dep)]
			built = False
			for b in builders:
				if b.supports(dep):
					if not b.up_to_date(dep):
						print('[b] ' + dep.buildname)
						b.build(dep)
					else:
						print('[-] ' + dep.buildname)
					built = True
					break
			if not built:
				print('warning: could not find builder for ' + dep.name + ' (' + dep.__class__.__name__ + ')')
		else:
			print('warning: could not find builder for type ' + str(type(dep)))