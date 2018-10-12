import buildsystem.buildsystem as bs

from enum import Enum
import os
import subprocess

class builder(object):
	def __init__(self, opts = None):
		self.options = opts
		self.in_exts = ()
		self.out_ext = ''
	class BuildResults(Enum):
		OK = 0
		ERROR = 1
	def setuptarget(self, dep, cfg):
		if bs.verbose:
			print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		dep.buildname = os.path.join(cfg.outdir, os.path.normpath(dep.name))
		if not dep.buildname.endswith(self.out_ext):
			dep.buildname += self.out_ext
	def supports(self, dep):
		return True
	def build(self, dep, opts = None):
		pass
	def up_to_date(self, dep):
		return False
	def clean(self, dep):
		if bs.verbose:
			print('Removing ' + dep.buildname + ' (' + dep.name + ')')
		try:
			os.remove(dep.buildname)
		except OSError:
			pass
	def need_clean(self, dep):
		return os.path.isfile(dep.buildname)

class builder_alwaysuptodate(builder):
	def setuptarget(self, dep, cfg):
		if bs.verbose:
			print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		dep.buildname = os.path.normpath(dep.name) # This is not an intermediate file, do not prepend cfg.outdir...
		if not dep.buildname.endswith(self.out_ext):
			dep.buildname += self.out_ext
	def up_to_date(self, dep):
		return True
	def need_clean(self, dep):
		return False

class command_builder(builder):
	def __init__(self, toolchain, opts = None):
		super().__init__(opts = opts)
		self.toolchain = toolchain

	def supports(self, dep):
		return all([d.buildname.endswith(self.in_exts) for d in dep.deps])

	def up_to_date(self, dep):
		if os.path.isfile(dep.buildname):
			target_timestamp = os.path.getmtime(dep.buildname)
			return all([os.path.isfile(d.buildname) and os.path.getmtime(d.buildname) <= target_timestamp for d in dep.deps])
		return False

	def call_build_command(self, cmd, dep):
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		completedprocess = subprocess.run(cmd, env = self.toolchain.env())
		return completedprocess.returncode == 0
