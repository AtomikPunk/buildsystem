import vsxml

class ProjectWriter:
	def __init__(self, project):
		self.project = project
		self.vsxml = None
		
	def write(self):
		with open(self.project.fileName, 'w') as f:
			self.vsxml = vsxml.vsxml(f)

			self.vsxml.writeDeclaration()

			with self.vsxml.el('Project', [
				('DefaultTargets', 'Build'),
				('ToolsVersion', '14.0'),
				('xmlns', 'http://schemas.microsoft.com/developer/msbuild/2003'),]):

				self.writeProjectConfigs()
				self.writeGlobals()
				self.writeImportCppDefault()
				self.writeConfigurations()
				self.writeImportCpp()
				self.writeExtensionSettings()
				self.writeShared()
				self.writeUserMacros()
				self.writePropertyGroups()
				self.writeItemDefinitionGroups()

	def writeProjectConfigs(self):
		with self.vsxml.el('ItemGroup', [('Label', 'ProjectConfigurations')]):
			for c in self.project.configs.keys():
				with self.vsxml.el('ProjectConfiguration', [('Include', c)]):
					with self.vsxml.el('Configuration', inline=True):
						self.vsxml.write(c.split('|')[0])
					with self.vsxml.el('Platform', inline=True):
						self.vsxml.write(c.split('|')[1])

	def writeGlobals(self):
		with self.vsxml.el('PropertyGroup', [('Label', 'Globals')]):
			with self.vsxml.el('ProjectGuid', inline=True):
				self.vsxml.write('{' + str(self.project.guid).upper() + '}')
			with self.vsxml.el('Keyword', inline=True):
				self.vsxml.write(self.project.keyword)
			with self.vsxml.el('RootNamespace', inline=True):
				self.vsxml.write(self.project.rootnamespace)
			if self.project.targetversion:
				with self.vsxml.el('WindowsTargetPlatformVersion', inline=True):
					self.vsxml.write(self.project.targetversion)

	def writeImportCppDefault(self):
		self.vsxml.writeEmptyEl('Import', [('Project', '$(VCTargetsPath)\Microsoft.Cpp.Default.props')])

	def writeConfigurations(self):
		for k,c in self.project.configs.items():
			with self.vsxml.el('PropertyGroup', [('Condition', '\'$(Configuration)|$(Platform)\'==\'' + k + '\''), ('Label', 'Configuration')]):
				with self.vsxml.el('ConfigurationType', inline=True):
					self.vsxml.write(c.configtype)
				if c.usedebuglibs:
					with self.vsxml.el('UseDebugLibraries', inline=True):
						self.vsxml.write(c.usedebuglibs)
				if c.platformtoolset:
					with self.vsxml.el('PlatformToolset', inline=True):
						self.vsxml.write(c.platformtoolset)
				if c.wholeprogramoptimization:
					with self.vsxml.el('WholeProgramOptimization', inline=True):
						self.vsxml.write(c.wholeprogramoptimization)
				if c.characterset:
					with self.vsxml.el('CharacterSet', inline=True):
						self.vsxml.write(c.characterset)

	def writeImportCpp(self):
		self.vsxml.writeEmptyEl('Import', [('Project', '$(VCTargetsPath)\Microsoft.Cpp.props')])

	def writeExtensionSettings(self):
		with self.vsxml.el('ImportGroup', [('Label', 'ExtensionSettings')]):
			pass

	def writeShared(self):
		with self.vsxml.el('ImportGroup', [('Label', 'Shared')]):
			pass

	def writePropertySheets(self):
		for k in self.project.configs.keys():
			with self.vsxml.el('ImportGroup', [('Label', 'PropertySheets'), ('Condition', '\'$(Configuration)|$(Platform)\'==\'' + k + '\'')]):
				self.vsxml.writeEmptyEl('Import', [
					('Project', '$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props'),
					('Condition', 'exists(\'$(UserRootDir)\Microsoft.Cpp.$(Platform).user.props\')'),
					('Label', 'LocalAppDataPlatform'),])

	def writeUserMacros(self):
		self.vsxml.writeEmptyEl('PropertyGroup', [('Label', 'UserMacros')])

	def writePropertyGroups(self):
		for k,c in self.project.configs.items():
			with self.vsxml.el('PropertyGroup', [('Condition', '\'$(Configuration)|$(Platform)\'==\'' + k + '\'')]):
				with self.vsxml.el('LinkIncremental', inline=True):
					self.vsxml.write(c.linkincremental)

	def writeItemDefinitionGroups(self):
		for k,c in self.project.configs.items():
			with self.vsxml.el('ItemDefinitionGroup', [('Condition', '\'$(Configuration)|$(Platform)\'==\'' + k + '\'')]):
				with self.vsxml.el('ClCompile'):
					self.vsxml.write(c.linkincremental)
				with self.vsxml.el('Link'):
					self.vsxml.write(c.linkincremental)

import prj
import uuid

if __name__ == "__main__":
	p = prj.Project()
	p.fileName = 'test.vcxproj'
	
	p.name = 'Test'
	p.guid = uuid.UUID('74CBA50E-368C-4EC1-958F-5576F61A543F')
	p.keyword = 'Win32Proj'
	p.rootnamespace = 'App'
	p.targetversion = '8.1'

	pc = prj.ProjectConfig()
	pc.configtype = 'Application'
	pc.usedebuglibs = 'true'
	pc.platformtoolset = 'v140'
	pc.characterset = 'Unicode'
	pc.linkincremental = 'true'
	p.configs['Debug|Win32'] = pc

	pc = prj.ProjectConfig()
	pc.configtype = 'Application'
	pc.usedebuglibs = 'false'
	pc.platformtoolset = 'v140'
	pc.wholeprogramoptimization = 'true'
	pc.characterset = 'Unicode'
	pc.linkincremental = 'false'
	p.configs['Release|Win32'] = pc

	pc = prj.ProjectConfig()
	pc.configtype = 'Application'
	pc.usedebuglibs = 'true'
	pc.platformtoolset = 'v140'
	pc.characterset = 'Unicode'
	pc.linkincremental = 'true'
	p.configs['Debug|x64'] = pc

	pc = prj.ProjectConfig()
	pc.configtype = 'Application'
	pc.usedebuglibs = 'false'
	pc.platformtoolset = 'v140'
	pc.wholeprogramoptimization = 'true'
	pc.characterset = 'Unicode'
	pc.linkincremental = 'false'
	p.configs['Release|x64'] = pc

	w = ProjectWriter(p)
	w.write()
