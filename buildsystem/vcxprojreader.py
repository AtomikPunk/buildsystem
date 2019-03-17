import lxml.etree as et

class ProjectReader:
	def __init__(self, fileName):
		self.fileName = fileName
		
	def parse(self):
		p = Project()
		p.fileName = self.fileName
		
		p.tree = et.parse(p.fileName)
		
		ns = "{http://schemas.microsoft.com/developer/msbuild/2003}"
		eProject = p.tree.getroot()
		eItemGroupProjectConfigs = eProject.find(ns + 'ItemGroup[@Label="ProjectConfigurations"]')
		p.configs = {c.get('Include'):ProjectConfig() for c in eItemGroupProjectConfigs.iterfind(ns + 'ProjectConfiguration')}

		eGlobals = eProject.find(ns + 'PropertyGroup[@Label="Globals"]')
		if eGlobals is not None:
			name = eGlobals.find(ns + 'ProjectName')
			if name is not None:
				p.name = name.text
		if not p.name:
			p.name = os.path.splitext(os.path.basename(p.fileName))[0]

		# Configuration definitions
		eConfigs = eProject.findall(ns + 'PropertyGroup[@Label="Configuration"]')
		if eConfigs is not None:
			for c in eConfigs:
				cfg = re.search(r"\=\='(.*)'", c.get('Condition'))
				# Config type (Appplication, StaticLibrary, DynamicLibrary, etc.)
				cfgtype = c.find(ns + 'ConfigurationType')
				if cfgtype is not None:
					pc = p.configs[cfg.group(1)]
					pc.configtype = cfgtype.text
					# Default for Application
					pc.targetext = '.exe'
					if pc.configtype == 'StaticLibrary':
						pc.targetext = '.lib'
					elif pc.configtype == 'DynamicLibrary':
						pc.targetext = '.dll'
		
		for g in eProject.iterfind(ns + 'ItemDefinitionGroup'):
			cfg = re.search(r"\=\='(.*)'", g.get('Condition'))
			if cfg.group(1) not in p.configs:
				print('Warning: found configuration in ItemDefinitionGroup that is not in ItemGroup@ProjectConfigurations')
				
			pc = p.configs[cfg.group(1)]
			eClCompile = g.find(ns + 'ClCompile')
			if eClCompile is not None:
				pc.incdirsnode = eClCompile.find(ns + 'AdditionalIncludeDirectories')
				if pc.incdirsnode is not None:
					pc.incdirs = pc.incdirsnode.text.split(';')

			eLink = g.find(ns + 'Link')
			if eLink is not None:
				pc.libsnode = eLink.find(ns + 'AdditionalDependencies')
				if pc.libsnode is not None:
					if pc.libsnode.text.strip(): # Fix bug if AdditionalDependencies tag is "empty" (e.g. all whitespaces like in XTractorCore.vcxproj)
						pc.libs = pc.libsnode.text.split(';')
				
				pc.libdirsnode = eLink.find(ns + 'AdditionalLibraryDirectories')
				if pc.libdirsnode is not None:
					pc.libdirs = pc.libdirsnode.text.split(';')

				pc.outputnode = eLink.find(ns + 'OutputFile')
				if pc.outputnode is not None:
					pc.output = pc.outputnode.text.replace('$(OutDir)', '').replace('$(TargetDir)', '').replace('$(TargetName)', p.name).replace('$(TargetExt)', pc.targetext).replace('$(ProjectName)', p.name).replace('\\','')
				else:
					pc.output = p.name + pc.targetext

				pc.importlibnode = eLink.find(ns + 'ImportLibrary')
				if pc.importlibnode is not None:
					if pc.importlibnode.text.strip(): # Fix bug if ImportLib tag is "empty" (e.g. all whitespaces like in FileManagement.vcxproj)
						pc.importlib = pc.importlibnode.text.replace('$(OutDir)', '').replace('$(TargetDir)', '').replace('$(TargetName)', p.name).replace('$(TargetExt)', pc.targetext).replace('$(ProjectName)', p.name).replace('\\','')

				# Default import library for StaticLibrary...
				if pc.configtype == 'DynamicLibrary' and not pc.importlib:
					pc.importlib = p.name + '.lib'

			eLib = g.find(ns + 'Lib')
			if eLib is not None:
				pc.libsnode = eLib.find(ns + 'AdditionalDependencies')
				if pc.libsnode is not None:
					if pc.libsnode.text.strip(): # Fix bug if AdditionalDependencies tag is "empty" (e.g. all whitespaces like in XTractorCore.vcxproj)
						pc.libs = pc.libsnode.text.split(';')
				
				pc.libdirsnode = eLib.find(ns + 'AdditionalLibraryDirectories')
				if pc.libdirsnode is not None:
					pc.libdirs = pc.libdirsnode.text.split(';')

				pc.outputnode = eLib.find(ns + 'OutputFile')
				if pc.outputnode is not None:
					pc.output = pc.outputnode.text.replace('$(OutDir)', '').replace('$(TargetName)', p.name).replace('$(TargetExt)', '.lib').replace('$(ProjectName)', p.name).replace('\\','')
				else:
					pc.output = p.name + '.lib'

			ePostBuildEvent = g.find(ns + 'PostBuildEvent')
			if ePostBuildEvent is not None:
				pc.postbuildcommandnode = ePostBuildEvent.find(ns + 'Command')
				if pc.postbuildcommandnode is not None:
					if pc.postbuildcommandnode.text.strip(): # Fix bug if AdditionalDependencies tag is "empty" (e.g. all whitespaces like in XTractorCore.vcxproj)
						pc.postbuildcommand = pc.postbuildcommandnode.text.split('\n')

			p.configs[cfg.group(1)] = pc
		
		return p
