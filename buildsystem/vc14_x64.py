import buildsystem.buildsystem as bs

import os
import subprocess

class toolchain(bs.toolchain):
	def __init__(self, transformers = []):
		super().__init__(transformers = transformers)
		self.transformers = {
			bs.compiled: transformer_cpp(),
			bs.executable: transformer_exe(),
			bs.staticlib: transformer_stlib(),
			bs.sharedlib: transformer_shlib(),
			}
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
	def transform(self, dep = None):
		if type(dep) in self.transformers.keys():
			self.transformers[type(dep)].transform(dep)

class transformer_cpp(bs.transformer):
	in_exts = ['.cpp','.cxx']
	out_ext = '.obj'
		
	def transform(self, deps = None):
		if not deps:
			print('error: ' + self.__class__.__name__ + '.transform(): no cpp file to process')
			return transformer.TransformResults.ERROR
		if not isinstance(deps, (list,)):
			deps = [deps]
		if len(deps) != 1:
			print('error: ' + self.__class__.__name__ + '.transform(): must provide exactly one cpp file to process')
			return transformer.TransformResults.ERROR
		if not self.check_supported(deps[0].deps):
			print('error: ' + self.__class__.__name__ + '.transform(): cpp has unsupported file name extension')
			return transformer.TransformResults.ERROR

		deps[0].filename = deps[0].name + self.out_ext
		cmd = [toolchain().compiler_path(), '/Fo' + deps[0].filename, '/c', [d.filename for d in deps[0].deps]]
		if deps[0].cflags:
			cmd.extend(deps[0].cflags)

		print(deps[0].name + ' <- [' + ' '.join([d.name for d in deps[0].deps]) + ']')
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
			
		subprocess.call(cmd, stderr = subprocess.DEVNULL, env = toolchain().env()) # For some reason, MS cl uses stdout for errors(?)
		
	def check_supported(self, deps = []):
		return all(isinstance(d, (bs.source,)) for d in deps)

class transformer_exe(bs.transformer):
	in_exts = ['.obj','.lib']
	out_ext = '.exe'
		
	def transform(self, deps = None):
		if not deps:
			print('error: ' + self.__class__.__name__ + '.transform(): no object or library file(s) to process')
			return transformer.TransformResults.ERROR
		if not isinstance(deps, (list,)):
			deps = [deps]
		if len(deps) != 1:
			print('error: ' + self.__class__.__name__ + '.transform(): must provide exactly one bs.executable file to process')
			return transformer.TransformResults.ERROR
		if not self.check_supported(deps[0].deps):
			print('error: ' + self.__class__.__name__ + '.transform(): object or library has unsupported file name extension')
			return transformer.TransformResults.ERROR

		deps[0].filename = deps[0].name + self.out_ext
		cmd = [toolchain().linker_path(), '/out:' + deps[0].filename]
		cmd.extend([d.filename for d in deps[0].deps])
		if deps[0].lflags:
			cmd.extend(deps[0].lflags)
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		print(deps[0].name + ' <- [' + ' '.join([d.name for d in deps[0].deps]) + ']')

		subprocess.call(cmd, stderr = subprocess.DEVNULL, env = toolchain().env()) # For some reason, MS cl uses stdout for errors(?)

	def check_supported(self, deps = []):
		return all(isinstance(d, (bs.compiled, bs.sharedlib, bs.staticlib)) for d in deps)
		
class transformer_stlib(bs.transformer):
	in_exts = ['.obj','.lib']
	out_ext = '.lib'
		
	def transform(self, deps = None):
		if not deps:
			print('error: ' + self.__class__.__name__ + '.transform(): no object or library file(s) to process')
			return transformer.TransformResults.ERROR
		if not isinstance(deps, (list,)):
			deps = [deps]
		if len(deps) != 1:
			print('error: ' + self.__class__.__name__ + '.transform(): must provide exactly one library file to process')
			return transformer.TransformResults.ERROR
		if not self.check_supported(deps[0].deps):
			print('error: ' + self.__class__.__name__ + '.transform(): object or library has unsupported file name extension')
			return transformer.TransformResults.ERROR

		deps[0].filename = deps[0].name + self.out_ext
		cmd = [toolchain().librarian_path(), '/out:' + deps[0].filename]
		cmd.extend([d.filename for d in deps[0].deps])
		if deps[0].lflags:
			cmd.extend(deps[0].lflags)
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		print(deps[0].name + ' <- [' + ' '.join([d.name for d in deps[0].deps]) + ']')
		
		subprocess.call(cmd, stderr = subprocess.DEVNULL, env = toolchain().env()) # For some reason, MS cl uses stdout for errors(?)

	def check_supported(self, deps = []):
		return all(isinstance(d, (bs.compiled, bs.sharedlib, bs.staticlib)) for d in deps)


class transformer_shlib(bs.transformer):
	in_exts = ['.obj','.lib']
	out_ext = '.lib'
		
	def transform(self, deps = None):
		if not deps:
			print('error: ' + self.__class__.__name__ + '.transform(): no object or library file(s) to process')
			return transformer.TransformResults.ERROR
		if not isinstance(deps, (list,)):
			deps = [deps]
		if len(deps) != 1:
			print('error: ' + self.__class__.__name__ + '.transform(): must provide exactly one bs.executable file to process')
			return transformer.TransformResults.ERROR
		if not self.check_supported(deps[0].deps):
			print('error: ' + self.__class__.__name__ + '.transform(): object or library has unsupported file name extension')
			return transformer.TransformResults.ERROR

		deps[0].filename = deps[0].name + self.out_ext
		cmd = [toolchain().linker_path(), '/dll', '/out:' + deps[0].name + '.dll']#, '/implib:' + deps[0].filename]
		cmd.extend([d.filename for d in deps[0].deps])
		if deps[0].lflags:
			cmd.extend(deps[0].lflags)
		if bs.verbose:
			print(subprocess.list2cmdline(cmd))
		print(deps[0].name + ' <- [' + ' '.join([d.name for d in deps[0].deps]) + ']')

		subprocess.call(cmd, stderr = subprocess.DEVNULL, env = toolchain().env()) # For some reason, MS cl uses stdout for errors(?)

	def check_supported(self, deps = []):
		return all(isinstance(d, (bs.compiled, bs.sharedlib, bs.staticlib)) for d in deps)
