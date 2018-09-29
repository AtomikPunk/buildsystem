import buildsystem.buildsystem as bs

from enum import Enum
import os
import subprocess

class builder(object):
	class BuildResults(Enum):
		OK = 0
		ERROR = 1
	def supports(self, dep):
		return True
	def build(self, dep):
		pass
	def up_to_date(self, dep):
		return False

class builder_alwaysuptodate(builder):
	def up_to_date(self, dep):
		return True

class command_builder(builder):
	def __init__(self, toolchain):
		self.toolchain = toolchain

	def supports(self, dep):
		(filebase,ext) = os.path.splitext(dep.name)
		dep.buildname = filebase + self.out_ext
		return all([os.path.splitext(d.buildname)[1] in self.supported_exts for d in dep.deps])

	def up_to_date(self, dep):
		if os.path.isfile(dep.buildname):
			target_timestamp = os.path.getmtime(dep.buildname)
			return all([os.path.isfile(d.buildname) and os.path.getmtime(d.buildname) <= target_timestamp for d in dep.deps])
		return False

	def call_build_command(self, cmd, dep):
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		subprocess.call(cmd, stderr = subprocess.DEVNULL, stdout = subprocess.DEVNULL, env = self.toolchain.env())
