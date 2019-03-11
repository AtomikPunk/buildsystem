import buildsystem.builders as bu
import buildsystem.buildsystem as bs
import buildsystem.toolchain as tc

import os

class toolchain(tc.toolchain):
	def __init__(self, builders = {}, opts = bs.options(), cfg = None):
		super().__init__(builders = {
			bs.compiled: [builder_cpp2obj(self)],
			bs.executable: [builder_exe(self)],
			bs.staticlib: [builder_stlib(self)],
			bs.sharedlib: [builder_shlib(self)],
			bs.importlib: [builder_imlib(self)],
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
		self.in_exts = ['.cpp', '.cc']

	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		if dep.outputs:
			print('warning: trying to add another "compiled" output to ' + dep.name)
		dep.outputs.append(bs.output(output + '.obj', {'compiled'}))
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs.values()))

	def build(self, dep):
		os.makedirs(os.path.dirname(dep.outputs[0].name), exist_ok=True)

		# Lookup "compiled" output
		compiled = [o.name for o in dep.outputs if 'compiled' in o.attributes]
		if len(compiled) > 1:
			print('warning: ' + dep.name + ' defines more than one "compiled" output...')

		# Lookup "source" dependency
		sources = []
		for d in dep.deps:
			for o in d.outputs:
				if 'source' in o.attributes:
					sources.append(o.name)
		if len(sources) > 1:
			print('warning: ' + dep.name + ' has more than one "source" dependency...')

		cmd = [self.toolchain.compiler_path(), '/nologo', '/Fo' + compiled[0]]
		cmd.extend(['/D' + d + ('=' + str(v) if v else '') for d,v in dep.options.get('defines').value.items()])
		cmd.extend(['/I' + i for i in dep.options.get('incdirs').value])
		cmd.extend(dep.options.get('cflags').value)
		cmd.extend(['/c'])
		cmd.extend(sources)
		p = super().call_build_command(cmd, dep)
		self.printerrors(p)
		return p.returncode == 0

class builder_linkable(bu.command_builder):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.in_exts = ['.obj', '.lib']
	
	def call_build_command(self, cmd, dep, opts = None):
		# Lookup "compiled", "importedlib" and "staticlib" dependencies
		inputs = []
		for d in dep.deps:
			inputs.extend(o.name for o in d.outputs if 'compiled' in o.attributes)
			inputs.extend(o.name for o in d.outputs if 'importedlib' in o.attributes)
			inputs.extend(o.name for o in d.outputs if 'staticlib' in o.attributes)

		effectiveoptions = self.toolchain.mergeoptions(dep, opts)
		cmd.extend(['/LIBPATH:' + os.path.normpath(d) for d in effectiveoptions.get('libdirs').value])
		cmd.extend(effectiveoptions.get('lflags').value)
		cmd.extend(inputs)
		p = super().call_build_command(cmd, dep)
		self.printerrors(p)
		return p.returncode == 0
			
class builder_exe(builder_linkable):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.exe'

	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs.append(bs.output(output + '.exe', {'executable'}))
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs))
		
	def build(self, dep):
		os.makedirs(os.path.dirname(dep.outputs[0].name), exist_ok=True)
		cmd = [self.toolchain.linker_path(), '/nologo', '/out:' + dep.outputs[0].name]
		return self.call_build_command(cmd, dep)

class builder_stlib(builder_linkable):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.lib'

	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs.append(bs.output(output + '.lib', {'staticlib'}))
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs))
		
	def build(self, dep):
		os.makedirs(os.path.dirname(dep.outputs[0].name), exist_ok=True)
		cmd = [self.toolchain.librarian_path(), '/nologo', '/out:' + dep.outputs[0].name]
		return self.call_build_command(cmd, dep)

class builder_shlib(builder_linkable):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.lib'

	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		output = os.path.normpath(os.path.join(cfg.outdir, dep.name))
		if output.endswith(self.out_ext):
			output = output[:-len(self.out_ext)]
		dep.outputs.append(bs.output(output + '.lib', {'staticlib'}))
		dep.outputs.append(bs.output(output + '.dll', {'sharedlib'}))
		dep.outputs.append(bs.output(output + '.exp', {'other'}))
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs))
		
	def build(self, dep):
		os.makedirs(os.path.dirname(dep.outputs[0].name), exist_ok=True)
		shlibs = [o for o in dep.outputs if 'sharedlib' in o.attributes]
		if len(shlibs) > 1:
			print('warning: ' + dep.name + ' defines more than one "sharedlib" output...')

		cmd = [self.toolchain.linker_path(), '/nologo', '/dll', '/out:' + shlibs[0].name]
		return self.call_build_command(cmd, dep)

class builder_imlib(bu.builder):
	def __init__(self, toolchain, opts = None):
		super().__init__(toolchain, opts = opts)
		self.out_ext = '.lib'

	def setuptarget(self, dep, cfg):
		#if bs.verbose:
			#print('setuptarget: ' + dep.name + ' with builder ' + str(type(self)))
		outputs = [os.path.normpath(l) for l in dep.libs] # This is not an intermediate file, do not prepend cfg.outdir...
		for o in outputs:
			if o.endswith(self.out_ext):
				o = o[:-len(self.out_ext)]
			dep.outputs.append(bs.output(o + '.lib', {'staticlib'}))
			dep.outputs.append(bs.output(o + '.dll', {'sharedlib'}))
		#print(dep.name + ': ' + ','.join(outputs))
		#if bs.verbose:
			#print('  outputs: ' + ','.join(dep.outputs))

	def build(self, dep):
		return True