import buildsystem.builders as bu
import buildsystem.buildsystem as bs
import buildsystem.toolchain as tc

import os

class toolchain(tc.toolchain):
	def __init__(self, builders = {}):
		super().__init__(builders = {
			bs.compiled: [builder_cpp(self)],
			bs.executable: [builder_exe(self)],
			bs.staticlib: [builder_stlib(self)],
			bs.sharedlib: [builder_shlib(self)],
			})
		self.builders.update(builders)
	def toolchain_path(self):
		# Return path to compiler base path (e.g. return r'C:\Program Files (x86)\Microsoft Visual Studio 14.0')
		raise NotImplementedError('vc.toolchain is an abstract base class')
	def toolchain_bin_path(self):
		# Return binaries subdirectory of compiler path (e.g. return self.toolchain_path() + r'\vc\bin\amd64')
		raise NotImplementedError('vc.toolchain is an abstract base class')
	def toolchain_lib_path(self):
		# Return libraries subdirectory of compiler path (e.g. return self.toolchain_path() + r'\vc\lib\amd64')
		raise NotImplementedError('vc.toolchain is an abstract base class')
	def compiler_path(self):
		return self.toolchain_bin_path() + '\cl.exe'
	def linker_path(self):
		return self.toolchain_bin_path() + '\link.exe'
	def librarian_path(self):
		return self.toolchain_bin_path() + '\lib.exe'
	def env(self, env = os.environ.copy()):
		# Return compilation environment (e.g.
		# env.setdefault('LIB','')
		# env['LIB'] += os.pathsep + self.toolchain_lib_path()
		# env['LIB'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\8.1\Lib\winv6.3\um\x64'
		# env['LIB'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\10\lib\10.0.10240.0\ucrt\x64'
		# env.setdefault('INCLUDE','')
		# env['INCLUDE'] += os.pathsep + self.toolchain_path() + r'\VC\INCLUDE'
		# env['INCLUDE'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt'
		# return env
		# )
		raise NotImplementedError('vc.toolchain is an abstract base class')

class builder_cpp(bu.command_builder):
	out_ext = '.obj'
	supported_exts = ('.cpp', '.cc')
		
	def build(self, dep):
		cmd = [self.toolchain.compiler_path(), '/nologo', '/Fo' + dep.buildname, '/c', [d.buildname for d in dep.deps]]
		if dep.incdirs:
			cmd.extend(['/I' + i for i in dep.incdirs])
		if dep.cflags:
			cmd.extend(dep.cflags)
		return self.call_build_command(cmd, dep)

class builder_linkable(bu.command_builder):
	supported_exts = ('.obj', '.lib')
	
	def call_build_command(self, cmd, dep):
		cmd.extend([d.buildname for d in dep.deps])
		if dep.lflags:
			cmd.extend(dep.lflags)
		return super().call_build_command(cmd, dep)
			
class builder_exe(builder_linkable):
	out_ext = '.exe'
		
	def build(self, dep):
		cmd = [self.toolchain.linker_path(), '/nologo', '/out:' + dep.buildname]
		return self.call_build_command(cmd, dep)
		
class builder_stlib(builder_linkable):
	out_ext = '.lib'
		
	def build(self, dep):
		cmd = [self.toolchain.librarian_path(), '/nologo', '/out:' + dep.buildname]
		return self.call_build_command(cmd, dep)


class builder_shlib(builder_linkable):
	out_ext = '.lib'
		
	def build(self, dep):
		cmd = [self.toolchain.linker_path(), '/nologo', '/dll', '/out:' + dep.name + '.dll']#, '/implib:' + dep.buildname]
		return self.call_build_command(cmd, dep)
