import buildsystem.buildsystem as bs
import buildsystem.vc as vc

import os

class toolchain(vc.toolchain):
	def toolchain_path(self):
		return r'C:\Program Files (x86)\Microsoft Visual Studio 14.0'
	def toolchain_bin_path(self):
		return self.toolchain_path() + r'\vc\bin\amd64'
	def toolchain_lib_path(self):
		return self.toolchain_path() + r'\vc\lib\amd64'
	def env(self, env = os.environ.copy()):
		env.setdefault('LIB','')
		env['LIB'] += os.pathsep + self.toolchain_lib_path()
		env['LIB'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\8.1\Lib\winv6.3\um\x64'
		env['LIB'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\10\lib\10.0.10240.0\ucrt\x64'
		env.setdefault('INCLUDE','')
		env['INCLUDE'] += os.pathsep + self.toolchain_path() + r'\VC\INCLUDE'
		env['INCLUDE'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\8.1\Include\shared'
		env['INCLUDE'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\8.1\Include\um'
		env['INCLUDE'] += os.pathsep + r'C:\Program Files (x86)\Windows Kits\10\Include\10.0.10240.0\ucrt'
		return env
