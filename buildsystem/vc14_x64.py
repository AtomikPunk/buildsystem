import buildsystem.buildsystem as bs

import os
import subprocess

class toolchain(bs.toolchain):
	def __init__(self, builders = {}):
		super().__init__(builders = {
			bs.compiled: [builder_cpp()],
			bs.executable: [builder_exe()],
			bs.staticlib: [builder_stlib()],
			bs.sharedlib: [builder_shlib()],
			})
		self.builders.update(builders)
	def toolchain_path(self):
		return r'C:\Program Files (x86)\Microsoft Visual Studio 14.0'
	def toolchain_bin_path(self):
		return self.toolchain_path() + r'\vc\bin\amd64'
	def toolchain_lib_path(self):
		return self.toolchain_path() + r'\vc\lib\amd64'
	def compiler_path(self):
		return self.toolchain_bin_path() + '\cl.exe'
	def linker_path(self):
		return self.toolchain_bin_path() + '\link.exe'
	def librarian_path(self):
		return self.toolchain_bin_path() + '\lib.exe'
	def env(self, env = os.environ.copy()):
		env.setdefault('LIB','')
		env['LIB'] += os.pathsep + self.toolchain_lib_path()
		env['LIB'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\8.1\Lib\winv6.3\um\x64'
		env['LIB'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\10\lib\10.0.10240.0\ucrt\x64'
		env.setdefault('INCLUDE','')
		env['INCLUDE'] += os.pathsep + self.toolchain_path() + r'\VC\INCLUDE'
		env['INCLUDE'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt'
		return env

class command_builder(bs.builder):
	def supports(self, dep):
		return all([os.path.splitext(d.builtname)[1] in self.supported_exts for d in dep.deps])

	def up_to_date(self, dep):
		if os.path.isfile(dep.builtname):
			target_timestamp = os.path.getmtime(dep.builtname)
			# print(str(target_timestamp))
			# print('\n'.join([str(os.path.getmtime(d.filename or d.name)) for d in dep.deps]))
			# print('verifying if target ' + dep.name + ' is up-to-date...')
			# for d in dep.deps:
				# isfile = os.path.isfile(d.name)
				# if isfile:
					# mtime = os.path.getmtime(d.name)
					# if mtime <= target_timestamp:
						# print('  ' + d.name + ' is up-to-date...')
					# else:
						# print('  ' + d.name + ' is not up-to-date!')
				# else:
					# print('  ' + d.name + ' is not a file...')
			return all([os.path.isfile(d.name) and os.path.getmtime(d.name) <= target_timestamp for d in dep.deps])
		# else:
			# print('  ' + dep.builtname + ' does not exist...')
		return False
		
	def call_build_command(self, cmd, dep):
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		#print(dep.name + ' <- [' + ' '.join([d.name for d in dep.deps]) + ']')
		print('[b] ' + dep.builtname)

		subprocess.call(cmd, stderr = subprocess.DEVNULL, stdout = subprocess.DEVNULL, env = toolchain().env())
					
class builder_cpp(command_builder):
	out_ext = '.obj'
	supported_exts = ('.cpp', '.cc')
		
	def build(self, dep):
		(filebase,ext) = os.path.splitext(dep.name)
		dep.builtname = filebase + self.out_ext
		if self.up_to_date(dep):
			print('[-] ' + dep.builtname)
			return
		cmd = [toolchain().compiler_path(), '/Fo' + dep.builtname, '/c', [d.builtname for d in dep.deps]]
		if dep.cflags:
			cmd.extend(dep.cflags)
		self.call_build_command(cmd, dep)

class builder_linkable(command_builder):
	supported_exts = (
		'.obj',
		'.lib',
		)
	
	def call_build_command(self, cmd, dep):
		cmd.extend([d.builtname for d in dep.deps])
		if dep.lflags:
			cmd.extend(dep.lflags)
		super().call_build_command(cmd, dep)
			
class builder_exe(builder_linkable):
	out_ext = '.exe'
		
	def build(self, dep):
		(filebase,ext) = os.path.splitext(dep.name)
		dep.builtname = filebase + self.out_ext
		if self.up_to_date(dep):
			print('[-] ' + dep.builtname)
			return
		cmd = [toolchain().linker_path(), '/out:' + dep.builtname]
		self.call_build_command(cmd, dep)
		
class builder_stlib(builder_linkable):
	out_ext = '.lib'
		
	def build(self, dep):
		(filebase,ext) = os.path.splitext(dep.name)
		dep.builtname = filebase + self.out_ext
		if self.up_to_date(dep):
			print('[-] ' + dep.builtname)
			return
		cmd = [toolchain().librarian_path(), '/out:' + dep.builtname]
		self.call_build_command(cmd, dep)


class builder_shlib(builder_linkable):
	out_ext = '.lib'
		
	def build(self, dep):
		(filebase,ext) = os.path.splitext(dep.name)
		dep.builtname = filebase + self.out_ext
		if self.up_to_date(dep):
			print('[-] ' + dep.builtname)
			return
		cmd = [toolchain().linker_path(), '/dll', '/out:' + dep.name + '.dll']#, '/implib:' + dep.filename]
		self.call_build_command(cmd, dep)
