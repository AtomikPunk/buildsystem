import buildsystem.builders as bu
import buildsystem.buildsystem as bs
import buildsystem.toolchain as tc

import os

class toolchain(tc.toolchain):
	def __init__(self, builders = {}, opts = None, cfg = None):
		super().__init__(builders = {
			bs.compiled: [builder_cpp2obj(self)],
			bs.executable: [builder_exe(self)],
			bs.staticlib: [builder_stlib(self)],
			bs.sharedlib: [builder_shlib(self)],
			},
			opts = opts,
			cfg = cfg)
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

class builder_cpp2obj(bu.command_builder):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.obj'
		self.in_exts = ('.cpp', '.cc')

	def setuptarget(self, dep, cfg):
		if bs.verbose:
			print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs = [
			output + '.obj',
			]
		if bs.verbose:
			print('  outputs: ' + ','.join(dep.outputs))

	def build(self, dep, opts = None):
		os.makedirs(os.path.dirname(dep.outputs[0]), exist_ok=True)
		cmd = [self.toolchain.compiler_path(), '/nologo', '/Fo' + dep.outputs[0], '/c', [d.outputs[0] for d in dep.deps]]
		defines = {}
		if isinstance(self.options, (bs.options,)):
			defines.update(self.opts.defines)
		if isinstance(dep.options, (bs.options,)):
			defines.update(dep.options.defines)
		if isinstance(opts, (bs.options,)):
			defines.update(opts.defines)
		cmd.extend(['/D' + d + ('=' + str(v) if v else '') for d,v in defines.items()])
		incdirs = set()
		if isinstance(self.options, (bs.options,)):
			incdirs.update(self.opts.incdirs)
		if isinstance(dep.options, (bs.options,)):
			incdirs.update(dep.options.incdirs)
		if isinstance(opts, (bs.options,)):
			incdirs.update(opts.incdirs)
		cmd.extend(['/I' + i for i in incdirs])
		cflags = set()
		if isinstance(self.options, (bs.options,)):
			cflags.update(self.opts.cflags)
		if isinstance(dep.options, (bs.options,)):
			cflags.update(dep.options.cflags)
		if isinstance(opts, (bs.options,)):
			cflags.update(opts.cflags)
		cmd.extend(cflags)
		p = super().call_build_command(cmd, dep)
		self.printerrors(p)
		return p.returncode == 0

class builder_linkable(bu.command_builder):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.in_exts = ('.obj', '.lib')
	
	def call_build_command(self, cmd, dep, opts = None):
		cmd.extend([d.outputs[0] for d in dep.deps])
		lflags = set()
		if isinstance(self.options, (bs.options,)):
			lflags.update(self.options.lflags)
		if isinstance(dep.options, (bs.options,)):
			lflags.update(dep.options.lflags)
		if isinstance(opts, (bs.options,)):
			lflags.update(opts.lflags)
		cmd.extend(lflags)
		p = super().call_build_command(cmd, dep)
		self.printerrors(p)
		return p.returncode == 0
			
class builder_exe(builder_linkable):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.exe'

	def setuptarget(self, dep, cfg):
		if bs.verbose:
			print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs = [
			output + '.exe',
#			output + '.lib',
#			output + '.exp',
			]
		if bs.verbose:
			print('  outputs: ' + ','.join(dep.outputs))
		
	def build(self, dep, opts = None):
		os.makedirs(os.path.dirname(dep.outputs[0]), exist_ok=True)
		cmd = [self.toolchain.linker_path(), '/nologo', '/out:' + dep.outputs[0]]
		return self.call_build_command(cmd, dep, opts = opts)

class builder_stlib(builder_linkable):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.lib'

	def setuptarget(self, dep, cfg):
		if bs.verbose:
			print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs = [
			output + '.lib',
#			output + '.exp',
			]
		if bs.verbose:
			print('  outputs: ' + ','.join(dep.outputs))
		
	def build(self, dep, opts = None):
		os.makedirs(os.path.dirname(dep.outputs[0]), exist_ok=True)
		cmd = [self.toolchain.librarian_path(), '/nologo', '/out:' + dep.outputs[0]]
		return self.call_build_command(cmd, dep, opts = opts)

class builder_shlib(builder_linkable):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.lib'

	def setuptarget(self, dep, cfg):
		if bs.verbose:
			print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs = [
			output + '.lib',
			output + '.dll',
			output + '.exp',
			]
		if bs.verbose:
			print('  outputs: ' + ','.join(dep.outputs))
		
	def build(self, dep, opts = None):
		os.makedirs(os.path.dirname(dep.outputs[0]), exist_ok=True)
		cmd = [self.toolchain.linker_path(), '/nologo', '/dll', '/out:' + dep.outputs[1]]
		return self.call_build_command(cmd, dep, opts = opts)
