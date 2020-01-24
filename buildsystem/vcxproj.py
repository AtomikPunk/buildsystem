import os
import re
import uuid

class attribute(object):
	def __init__(self, name, value = None):
		self.name = name
		self.value = value

class element(object):
	def __init__(self, name, attrs = None, chld = None, selfclosing = False):
		self.children = chld or []
		self.attributes = attrs or {}
		self.name = name
		self.selfclosing = selfclosing

	def indexoflast(self, name):
		return len(self.children) - 1 - next(i for i,v in enumerate(self.children[::-1]) if v.name == name)

class vcxproj(object):
	def __init__(self, rootnode):
		self.rootnode = rootnode

	def getconfigurations(self):
		cfgs = []
		for pc in self.rootnode.children[0].children:
			cfgs.append(pc.attributes['Include'])
		return cfgs

	def isstaticlib(self, cfg):
		cfgnode = next(filter(lambda c: c.name == 'PropertyGroup' and 'Configuration' in c.attributes.get('Label', '') and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		cfgtypenode = next(filter(lambda c: c.name == 'ConfigurationType', cfgnode.children), None)
		if cfgtypenode.children[0] == 'StaticLibrary':
			return True
		return False

	def getguid(self):
		gnode = next(filter(lambda c: c.name == 'PropertyGroup' and 'Globals' in c.attributes.get('Label', ''), self.rootnode.children), None)
		guidnode = next(filter(lambda c: c.name == 'ProjectGuid', gnode.children), None)
		return uuid.UUID(guidnode.children[0])

	@property
	def toolset(self):
		raise NotImplementedError()

	@toolset.setter
	def toolset(self, value):
		for cfg in self.getconfigurations():
			cfgnode = next(filter(lambda c: c.name == 'PropertyGroup' and 'Configuration' in c.attributes.get('Label', '') and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
			toolsetnode = next(filter(lambda c: c.name == 'PlatformToolset', cfgnode.children), None)
			if not toolsetnode:
				gnode.children.append(element('PlatformToolset', chld = [value]))
			else:
				toolsetnode.children[0] = value

	@property
	def sdk(self):
		gnode = next(filter(lambda c: c.name == 'PropertyGroup' and 'Globals' in c.attributes.get('Label', ''), self.rootnode.children), None)
		sdknode = next(filter(lambda c: c.name == 'WindowsTargetPlatformVersion', gnode.children), element(chld = ['8.1']))
		return sdknode.children[0]

	@sdk.setter
	def sdk(self, value):
		gnode = next(filter(lambda c: c.name == 'PropertyGroup' and 'Globals' in c.attributes.get('Label', ''), self.rootnode.children), None)
		sdknode = next(filter(lambda c: c.name == 'WindowsTargetPlatformVersion', gnode.children), None)
		if not sdknode:
			gnode.children.append(element('WindowsTargetPlatformVersion', chld = [value]))
		else:
			sdknode.children[0] = value

	def getoutdir(self, cfg):
		outdirnode = None
		# Unconditional PropertyGroup
		gnode = next(filter(lambda c: c.name == 'PropertyGroup' and not c.attributes, self.rootnode.children), None)
		if gnode:
			outdirnode = next(filter(lambda c: c.name == 'OutDir' and cfg in c.attributes.get('Condition', ''), gnode.children), None)
		if not outdirnode:
			# Conditional PropertyGroup
			gnode = next(filter(lambda c: c.name == 'PropertyGroup' and 'Label' not in c.attributes and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
			if gnode:
				outdirnode = next(filter(lambda c: c.name == 'OutDir' and not c.attributes, gnode.children), None)

		return outdirnode.children[0]

	def libnodetag(self, cfg):
		if self.isstaticlib(cfg):
			return 'Lib'
		else:
			return 'Link'

	def getbinaries(self, cfg):
		binaries = {}
		ignodes = [c for c in self.rootnode.children if c.name == 'ItemGroup' and 'DM_Binaries' in c.attributes.get('Label', '')]
		for ignode in ignodes:
			cbnodes = [c for c in ignode.children if c.name == 'CustomBuild']
			for cbnode in cbnodes:
				inputpath = cbnode.attributes.get('Include')
				filename = os.path.basename(inputpath)
				onodes = [c for c in cbnode.children if c.name == 'Outputs' and cfg in c.attributes.get('Condition', '')]
				outputpath = None
				for onode in onodes:
					outputpath = onode.children[0].strip()
					binaries.setdefault(inputpath, {})
					if outputpath != '$(OutDir)' + filename:
						binaries.get(inputpath).setdefault('dest',{outputpath:None})
		return binaries

	def setbinaries(self, cfg, binaries):
		if not binaries:
			ignodes = [c for c in self.rootnode.children if c.name == 'ItemGroup' and 'DM_Binaries' in c.attributes.get('Label', '')]
			for ignode in ignodes:
				self.rootnode.children.remove(ignode)
			return

		ignodes = [c for c in self.rootnode.children if c.name == 'ItemGroup' and 'DM_Binaries' in c.attributes.get('Label', '')]
		if ignodes:
			ignode = ignodes[0]
			# Strip items from current config
			cbnodes = [c for c in ignode.children if c.name == 'CustomBuild']
			for cbnode in cbnodes:
				cbnode.children = [c for c in cbnode.children if not cfg in c.attributes.get('Condition', '')]
			ignode.children = [i for i in ignode.children if i.children]
		else:
			lastidg = self.rootnode.indexoflast('ItemDefinitionGroup')
			ignode = element('ItemGroup')
			ignode.attributes.setdefault('Label', 'DM_Binaries')
			self.rootnode.children.insert(lastidg+1, ignode)

		for kb,b in binaries.items():
			spec = b or {}
			oe = element('Outputs')
			oe.attributes.setdefault('Condition', "'$(Configuration)|$(Platform)'=='" + cfg + "'")
			dest = next(iter(spec.get('dest',{'': None})))
			base = os.path.basename(dest)
			if base:
				outpath = os.path.join('$(OutDir)' + os.path.dirname(dest), base)
			else:
				outpath = os.path.join('$(OutDir)' + os.path.dirname(dest), os.path.basename(kb))
			oe.children.append(outpath)

			ce = element('Command')
			ce.attributes.setdefault('Condition', "'$(Configuration)|$(Platform)'=='" + cfg + "'")
			#ce.children.append('xcopy %(FullPath) ' + outpath + ' /y & IF ERRORLEVEL 2 (echo %(Fullpath) NOT COPIED to ' + outpath + ' ) ELSE (echo %(Fullpath) copied to ' + outpath + ')')
			ce.children.append('xcopy %(FullPath) ' + outpath + '* /f /y') # Use * suffix to destination path in xcopy command to specify destination is a file name
			me = element('Message')
			me.attributes.setdefault('Condition', "'$(Configuration)|$(Platform)'=='" + cfg + "'")
			me.children.append('')

			config = spec.get('config',{})
			cbnodes = [c for c in ignode.children if c.name == 'CustomBuild' and kb == c.attributes.get('Include', None) and (not config or cfg in config)]
			if cbnodes:
				e = cbnodes[0]
			else:
				e = element('CustomBuild')
				e.attributes.setdefault('Include', kb)
				if config:
					e.attributes.setdefault('Condition', "'$(Configuration)|$(Platform)'=='" + cfg + "'")
			e.children.append(oe)
			e.children.append(ce)
			e.children.append(me)
			if not cbnodes:
				ignode.children.append(e)

	def getdefines(self, cfg):
		defines = []
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		clnode = next(filter(lambda c: c.name == 'ClCompile', idgnode.children), None)
		if not clnode:
			return []
		definesnode = next(filter(lambda c: c.name == 'PreprocessorDefinitions', clnode.children), None)
		if definesnode:
			if definesnode.children[0].strip():
				defines.append(definesnode.children[0].strip())
		if not defines:
			#print('vcxproj warning: no include directories are defined...')
			return []
		if len(defines) > 1:
			ref = defines[0]
			for i in defines:
				if i != ref:
					print('vcxproj warning: more than one set of include directories are defined...')
					break
		return [x for x in defines[0].split(';') if x]

	def setdefines(self, cfg, defines):
		self.addtoend(defines, '%(PreprocessorDefinitions)')
		newnode = element('PreprocessorDefinitions')
		newnode.children.append(';'.join(defines))
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		clnode = next(filter(lambda c: c.name == 'ClCompile', idgnode.children), None)
		if not clnode:
			if len(defines) <= 1:
				return
			clnode = element('ClCompile')
			idgnode.children.append(clnode)
		definesnode = next(filter(lambda c: c.name == 'PreprocessorDefinitions', clnode.children), None)
		if definesnode:
			if len(defines) == 1:
				definesnode.children = []
				clnode.children.remove(definesnode)
			else:
				definesnode.children = newnode.children
		elif len(defines) > 1:
			clnode.children.append(newnode)

	def getincdirs(self, cfg):
		incdirs = []
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		clnode = next(filter(lambda c: c.name == 'ClCompile', idgnode.children), None)
		if not clnode:
			return []
		incdirsnode = next(filter(lambda c: c.name == 'AdditionalIncludeDirectories', clnode.children), None)
		if incdirsnode:
			if incdirsnode.children and incdirsnode.children[0].strip():
				incdirs.append(incdirsnode.children[0].strip())
		if not incdirs:
			#print('vcxproj warning: no include directories are defined...')
			return []
		if len(incdirs) > 1:
			ref = incdirs[0]
			for i in incdirs:
				if i != ref:
					print('vcxproj warning: more than one set of include directories are defined...')
					break
		return [x for x in incdirs[0].split(';') if x]

	def setincdirs(self, cfg, incdirs):
		self.addtoend(incdirs, '%(AdditionalIncludeDirectories)')
		newnode = element('AdditionalIncludeDirectories')
		newnode.children.append(';'.join(incdirs))
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		clnode = next(filter(lambda c: c.name == 'ClCompile', idgnode.children), None)
		if not clnode:
			if len(incdirs) <= 1:
				return
			clnode = element('ClCompile')
			idgnode.children.append(clnode)
		incdirsnode = next(filter(lambda c: c.name == 'AdditionalIncludeDirectories', clnode.children), None)
		if incdirsnode:
			if len(incdirs) == 1:
				incdirsnode.children = []
				clnode.children.remove(incdirsnode)
			else:
				incdirsnode.children = newnode.children
		elif len(incdirs) > 1:
			clnode.children.append(newnode)

	def getlibdirs(self, cfg):
		libdirs = []
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		linklibnode = next(filter(lambda c: c.name == self.libnodetag(cfg), idgnode.children), None)
		if not linklibnode:
			return []
		libdirsnode = next(filter(lambda c: c.name == 'AdditionalLibraryDirectories', linklibnode.children), None)
		if libdirsnode:
			if libdirsnode.children[0].strip():
				libdirs.append(libdirsnode.children[0].strip())
		if not libdirs:
			#print('vcxproj warning: no library directories are defined...')
			return []
		if len(libdirs) > 1:
			ref = libdirs[0]
			for i in libdirs:
				if i != ref:
					print('vcxproj warning: more than one set of library directories are defined...')
					break
		return [x for x in libdirs[0].split(';') if x]

	def setlibdirs(self, cfg, libdirs):
		self.addtoend(libdirs, '%(AdditionalLibraryDirectories)')
		newnode = element('AdditionalLibraryDirectories')
		newnode.children.append(';'.join(libdirs))
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		linklibnode = next(filter(lambda c: c.name == self.libnodetag(cfg), idgnode.children), None)
		if not linklibnode:
			if len(libdirs) <= 1:
				return
			linklibnode = element(self.libnodetag(cfg))
			idgnode.children.append(linklibnode)
		libdirsnode = next(filter(lambda c: c.name == 'AdditionalLibraryDirectories', linklibnode.children), None)
		if libdirsnode:
			if len(libdirs) == 1:
				libdirsnode.children = []
				linklibnode.children.remove(libdirsnode)
			else:
				libdirsnode.children = newnode.children
		elif len(libdirs) > 1:
			linklibnode.children.append(newnode)

	def getlibs(self, cfg):
		libs = []
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		linklibnode = next(filter(lambda c: c.name == self.libnodetag(cfg), idgnode.children), None)
		if not linklibnode:
			return []
		libsnode = next(filter(lambda c: c.name == 'AdditionalDependencies', linklibnode.children), None)
		if libsnode and libsnode.children:
			if libsnode.children[0].strip():
				libs.append(libsnode.children[0].strip())
		if not libs:
			#print('vcxproj warning: no libraries are defined...')
			return []
		if len(libs) > 1:
			ref = libs[0]
			for i in libs:
				if i != ref:
					print('vcxproj warning: more than one set of libraries are defined...')
					break
		return [x for x in libs[0].split(';') if x]

	def setlibs(self, cfg, libs):
		self.addtoend(libs, '%(AdditionalDependencies)')
		newnode = element('AdditionalDependencies')
		newnode.children.append(';'.join(libs))
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		linklibnode = next(filter(lambda c: c.name == self.libnodetag(cfg), idgnode.children), None)
		if not linklibnode:
			if len(libs) <= 1:
				return
			linklibnode = element(self.libnodetag(cfg))
			idgnode.children.append(linklibnode)
		libsnode = next(filter(lambda c: c.name == 'AdditionalDependencies', linklibnode.children), None)
		if libsnode:
			if len(libs) == 1:
				libsnode.children = []
				linklibnode.children.remove(libsnode)
			else:
				libsnode.children = newnode.children
		elif len(libs) > 1:
			linklibnode.children.append(newnode)

	def getpostbuildcommands(self, cfg):
		commands = []
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		postbuildeventnode = next(filter(lambda c: c.name == 'PostBuildEvent', idgnode.children), None)
		if not postbuildeventnode:
			return []
		commandsnode = next(filter(lambda c: c.name == 'Command', postbuildeventnode.children), None)
		if commandsnode and commandsnode.children:
			if commandsnode.children[0].strip():
				commands.append(commandsnode.children[0].strip())
		if not commands:
			#print('vcxproj warning: no libraries are defined...')
			return []
		if len(commands) > 1:
			ref = commands[0]
			for i in commands:
				if i != ref:
					print('vcxproj warning: more than one set of libraries are defined...')
					break
		return [x for x in commands[0].splitlines() if x]

	def setpostbuildcommands(self, cfg, cmds):
		self.addtoend(cmds, '%(Command)')
		newnode = element('Command')
		newnode.children.append('\n'.join(cmds))
		idgnode = next(filter(lambda c: c.name == 'ItemDefinitionGroup' and cfg in c.attributes.get('Condition', ''), self.rootnode.children), None)
		postbuildeventnode = next(filter(lambda c: c.name == 'PostBuildEvent', idgnode.children), None)
		if not postbuildeventnode:
			if len(cmds) <= 1:
				return
			postbuildeventnode = element('PostBuildEvent')
			idgnode.children.append(postbuildeventnode)
		commandsnode = next(filter(lambda c: c.name == 'Command', postbuildeventnode.children), None)
		if commandsnode:
			if len(cmds) == 1:
				commandsnode.children = []
				postbuildeventnode.children.remove(commandsnode)
			else:
				commandsnode.children = newnode.children
		elif len(cmds) > 1:
			postbuildeventnode.children.append(newnode)

	def getreferences(self):
		references = {}
		ignodes = [c for c in self.rootnode.children if c.name == 'ItemGroup']
		for ignode in ignodes:
			prnodes = [c for c in ignode.children if c.name == 'ProjectReference']
			for prnode in prnodes:
				inputpath = prnode.attributes.get('Include')
				pnode = next(filter(lambda c: c.name == 'Project', prnode.children), None)
				references[uuid.UUID(pnode.children[0][1:-1])] = inputpath
		return references

	def addtoend(self, list, item):
		if item in list:
			list.remove(item)
		list.setdefault(item, {})

	def createdefault(name = 'unnamed', guid = None):
		cfgs = ['Debug|x64', 'Release|x64']
		# Based on https://docs.microsoft.com/en-us/cpp/build/reference/vcxproj-file-structure
		p = element('Project', {'DefaultTargets': 'Build', 'ToolsVersion': '14.0', 'xmlns': 'http://schemas.microsoft.com/developer/msbuild/2003'})
		# ProjectConfigurations
		igpc = element('ItemGroup', {'Label': 'ProjectConfigurations'})
		for c in cfgs:
			pc = element('ProjectConfiguration', {'Include': c})
			pc.children.append(element('Configuration', chld = [c.split('|')[0]]))
			pc.children.append(element('Platform', chld = [c.split('|')[1]]))
			igpc.children.append(pc)
		p.children.append(igpc)
		# Globals
		pgg = element('PropertyGroup', {'Label': 'Globals'})
		if guid:
			pgg.children.append(element('ProjectGuid', chld = ['{' + str(guid).upper() + '}']))
		else:
			pgg.children.append(element('ProjectGuid', chld = ['{' + str(uuid.uuid1()).upper() + '}']))
		pgg.children.append(element('RootNamespace', chld = [name]))
		pgg.children.append(element('WindowsTargetPlatformVersion', chld = ['8.1']))
		p.children.append(pgg)
		# Import Microsoft.Cpp.Default.props
		p.children.append(element('Import', attrs = {'Project': '$(VCTargetsPath)\Microsoft.Cpp.Default.props'}, selfclosing = True))
		# Project configurations
		for c in cfgs:
			pg = element('PropertyGroup', attrs = {'Condition': "'$(Configuration)|$(Platform)'=='" + c + "'", 'Label': 'Configuration'})
			pg.children.append(element('ConfigurationType', chld = ['Utility']))
			if 'Debug' in c:
				pg.children.append(element('UseDebugLibraries', chld = ['true']))
			else:
				pg.children.append(element('UseDebugLibraries', chld = ['false']))
			pg.children.append(element('PlatformToolset', chld = ['v140']))
			if 'Release' in c:
				pg.children.append(element('WholeProgramOptimization', chld = ['true']))
			pg.children.append(element('CharacterSet', chld = ['MultiByte']))
			p.children.append(pg)
		# Import Microsoft.Cpp.props
		p.children.append(element('Import', attrs = {'Project': '$(VCTargetsPath)\Microsoft.Cpp.props'}, selfclosing = True))
		# ImportGroup ExtensionSettings
		p.children.append(element('ImportGroup', attrs = {'Label': 'ExtensionSettings'}))
		# ImportGroup Shared
		p.children.append(element('ImportGroup', attrs = {'Label': 'Shared'}))
		# ImportGroup PropertySheets
		for c in cfgs:
			ig = element('ImportGroup', attrs = {'Label': 'PropertySheets', 'Condition': "'$(Configuration)|$(Platform)'=='" + c + "'"})
			ig.children.append(element('Import', attrs = {'Project': '$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props', 'Condition': "exists('$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props')", 'Label': 'LocalAppDataPlatform'}, selfclosing = True))
			p.children.append(ig)
		# UserMacros
		p.children.append(element('PropertyGroup', attrs = {'Label': 'UserMacros'}, selfclosing = True))
		# PropertyGroups
		for c in cfgs:
			pg = element('PropertyGroup', attrs = {'Condition': "'$(Configuration)|$(Platform)'=='" + c + "'"})
			pg.children.append(element('OutDir', chld = [r'$(SolutionDir)..\bin\$(Platform)\$(Configuration)' + '\\']))
			pg.children.append(element('IntDir', chld = [r'$(SolutionDir)..\build\$(Platform)\$(Configuration)\$(ProjectName)' + '\\']))
			p.children.append(pg)
		# ItemDefinitionGroups
		for c in cfgs:
			idg = element('ItemDefinitionGroup', attrs = {'Condition': "'$(Configuration)|$(Platform)'=='" + c + "'"})
			clc = element('ClCompile')
			clc.children.append(element('WarningLevel', chld = ['Level3']))
			if 'Debug' in c:
				clc.children.append(element('Optimization', chld = ['Disabled']))
			else:
				clc.children.append(element('Optimization', chld = ['MaxSpeed']))
				clc.children.append(element('FunctionLevelLinking', chld = ['true']))
				clc.children.append(element('IntrinsicFunctions', chld = ['true']))
			clc.children.append(element('SDLCheck', chld = ['true']))
			idg.children.append(clc)
			if 'Release' in c:
				lnk = element('Link')
				lnk.children.append(element('EnableCOMDATFolding', chld = ['true']))
				lnk.children.append(element('OptimizeReferences', chld = ['true']))
				idg.children.append(lnk)
			p.children.append(idg)
		# ItemGroup
		p.children.append(element('ItemGroup'))
		# Targets
		p.children.append(element('Import', attrs = {'Project': '$(VCTargetsPath)\Microsoft.Cpp.targets'}, selfclosing = True))
		# ExtensionTargets
		p.children.append(element('ImportGroup', attrs = {'Label': 'ExtensionTargets'}))
		return vcxproj(p)

class reader(object):
	def __init__(self):
		self.str = None
		self.parsedindex = None

	def read(self, fileName):
		with open(fileName) as f:
			return self.fromstring(f.read())

	def fromstring(self, str, index = 0):
		self.str = str

		# Skip XML declaration
		if self.str.find('<?', index) != -1:
			self.parsedindex = self.str.find('?>') + 2

		# Root element
		idx = self.str.find('<', self.parsedindex)
		rootnode = self.parseelement(idx)
		
		return rootnode

	def parseelement(self, beg):
		idx = self.locateelement(beg)
		self.parsedindex = idx[1]
		#components = self.str[idx[0] + 1 : idx[1] - 1].split(' ')
		components = re.findall('(\S+=\".*?\"|\S+)+', self.str[idx[0] + 1 : idx[1] - 1])
		name = components.pop(0)
		#print('vcxproj: ' + name)
		selfclosing = False
		if components:
			selfclosing = components[-1] == '/'
			if selfclosing:
				components.pop()

		e = element(name)
		if components:
			e.attributes = self.parseattributes(components)

		if selfclosing:
			e.selfclosing = True
			return e

		idx = self.locateelement(idx[1])
		while idx is not None:
			# Text content
			txt = self.str[self.parsedindex : idx[0]].strip()
			if txt:
				e.children.append(self.xmltotext(txt))

			self.parsedindex = idx[1]
			if self.str[idx[0] + 1] == '/':
				tag = self.str[idx[0] + 2 : idx[1] - 1]
				if tag == e.name:
					# Closing current element
					#print('vcxproj: /' + tag)
					return e

				raise ValueError('vcxproj error: invalid closing element at index ' + str(idx[0]) + ', expected </' + e.name + '>')
			else:
				e.children.append(self.parseelement(idx[0]))
			idx = self.locateelement(self.parsedindex + 1)

		return e

	def locateelement(self, beg):
		begidx = self.str.find('<', beg)
		if begidx == -1:
			return None

		endidx = self.str.find('>', begidx)
		if endidx == -1:
			raise ValueError('vcxproj error: could not find closing xml bracket from index ' + begidx)

		return (begidx, endidx + 1)

	def parseattributes(self, alist):
		attr = {}
		for a in alist:
			pair = a.split('=', 1)
			if len(pair) < 2:
				raise ValueError('vcxproj error: invalid attributes list in parseattributes()')
			key = pair[0]
			value = pair[1].strip('"')
			attr[key] = value
		return attr

	def xmltotext(self, str):
		# Microsoft replaces only &, < and > (not " nor ')
		return (str
			.replace('&amp;',  '&')
			.replace('&lt;',   '<')
			.replace('&gt;',   '<'))

class writer(object):
	def __init__(self, vcxproj):
		self.indentlevel = 0
		self.indentsymbol = '  '
		self.proj = vcxproj

	def write(self, fileName):
		original = None
		try:
			with open(fileName, 'r', encoding='utf-8-sig') as f:
				original = f.read()
		except:
			pass
		new = self.tostring()
		if original != new:
			if original:
				print('vcxproj: Updating ' + fileName)
			else:
				print('vcxproj: Creating ' + fileName)
			os.makedirs(os.path.dirname(fileName), exist_ok = True)
			with open(fileName, 'w', encoding='utf-8-sig') as f:
				f.write(new)

	def tostring(self):
		s = ''
		s += self.prolog()
		s += self.elementtostring(self.proj.rootnode)
		return s

	def elementtostring(self, node):
		s = ''
		s += self.indentlevel*self.indentsymbol + '<' + node.name
		for k,v in node.attributes.items():
			s += ' ' + k + '="' + v + '"'
		if node.selfclosing:
			s += ' />'
		else:
			s += '>'
			self.indentlevel += 1
			for c in node.children:
				if isinstance(c, str):
					# text
					s += self.texttoxml(c)
				elif isinstance(c, element):
					# element
					s += '\n' + self.elementtostring(c)
			self.indentlevel -= 1
			if len(node.children) == 1 and isinstance(node.children[0], str):
				pass
			else:
				s += '\n' + self.indentlevel*self.indentsymbol
			s += '</' + node.name + '>'
		return s

	def prolog(self):
		return '<?xml version="1.0" encoding="utf-8"?>\n'

	def texttoxml(self, str):
		# Microsoft replaces only &, < and > (not " nor ')
		return (str
			.replace('&', '&amp;')
			.replace('<', '&lt;')
			.replace('<', '&gt;'))

if __name__ == "__main__":
	#r = reader()
	#p = r.read('test.vcxproj')

	#vx = vcxproj(p)
	#incdirs = vx.getincdirs()
	#incdirs.append('inc')
	#vx.setincdirs(incdirs)

	#w = writer()
	#w.write('testwrite.vcxproj', p)
	w = writer(vcxproj.createdefault('zlib'))
	w.write('_default.vcxproj')