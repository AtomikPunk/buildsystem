import buildsystem.buildsystem as bs

from enum import Enum
import os
import subprocess
import io

class builder(object):
	def __init__(self, toolchain, opts = None):
		self.options = opts
		self.in_exts = ()
		self.out_ext = ''
	class BuildResults(Enum):
		OK = 0
		ERROR = 1
	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.join(cfg.outdir, os.path.normpath(dep.name))
		if not output.endswith(self.out_ext):
			output = output + self.out_ext
		dep.outputs = [output]
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs))
	def supports(self, dep):
		return True
	def build(self, dep):
		return True
	def up_to_date(self, dep):
		return False
	def clean(self, dep):
		for o in dep.outputs:
			try:
				if bs.verbose:
					print('Removing ' + o)
				os.remove(o)
			except OSError:
				pass
	def need_clean(self, dep):
		return any([os.path.isfile(o) for o in dep.outputs])

class builder_alwaysuptodate(builder):
	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(dep.name) # This is not an intermediate file, do not prepend cfg.outdir...
		if not output.endswith(self.out_ext):
			output = output + self.out_ext
		dep.outputs = [output]
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs))
	def up_to_date(self, dep):
		return True
	def need_clean(self, dep):
		return False

class command_builder(builder):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.toolchain = toolchain

	def up_to_date(self, dep):
		try:
			for o in dep.outputs:
				if not os.path.isfile(o):
					if bs.verbose:
						print(dep.name + ' is not up-to-date because ' + o + ' is not a file')
					return False
				target_timestamp = os.path.getmtime(o)
				if not all([all([os.path.getmtime(do) <= target_timestamp for do in d.outputs]) for d in dep.deps]):
					if bs.verbose:
						print(dep.name + ' is not up-to-date because one of its dependency is not up-to-date')
					return False
			return True
		except FileNotFoundError as e:
			print(str(e))
			return False

	def call_build_command(self, cmd, dep):
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		completedprocess = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, env = self.toolchain.env())
		return completedprocess

	def printerrors(self, completedprocess):
		for l in completedprocess.stdout.decode('utf-8').splitlines():
			if ':' in l:
				print(l)
		for l in completedprocess.stderr.decode('utf-8').splitlines():
			if ':' in l:
				print(l)
