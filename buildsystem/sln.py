from . import vcxproj

import uuid
import re

ProjectTypes = {
	'Folder': '2150E333-8FDC-42A3-9474-1A3956D46DE8',
	'C++': '8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942',
	}

class Project:
	def __init__(self, name = None, guid = None, fileName = None, type = None, loaded = None):
		self.name = name or ''
		self.guid = guid
		self.fileName = fileName or self.name + '.vcxproj'
		self.type = type
		self.deps = []
		self.items = []
		self.loaded = loaded

	def load(self):
		# Skip folders
		if self.isfolder():
			return

		pf = self.fileName
		#print('Loading project ' + pf)
		pr = vcxproj.reader()
		p = pr.read(pf)

		self.loaded = vcxproj.vcxproj(p)

	def isfolder(self):
		# Optimize this...
		return str(self.type).upper() == ProjectTypes.get('Folder')

class Solution:
	def __init__(self):
		self.fileName = ''
		self.version = None
		self.projects = {}
		self.configs = []
		self.projectconfigs = []
		self.props = []
		self.nestedprojects = {}
		self.extensibilityglobals = []
		self.testcasemgmtsettings = []
		self._toolset = None
		self._sdk = None

	def getproject(self, nameoruuid):
		if isinstance(nameoruuid, uuid.UUID):
			return [(k,v) for (k,v) in self.projects.items() if v.guid == nameoruuid and not v.isfolder()]
		else:
			return [(k,v) for (k,v) in self.projects.items() if v.name == nameoruuid and not v.isfolder()]

	def setfolder(self, project, folder):
		folderprojects = {k:v for k,v in self.projects.items() if v.isfolder()}

		folders = folder.split('/')
		lastfolder = None
		for f in folders:
			matchingprojects = {k:v for k,v in folderprojects.items() if v.name == f and lastfolder == self.nestedprojects.get(k, None)}
			if matchingprojects:
				lastfolder = next(iter(matchingprojects))
				if len(matchingprojects) > 1:
					print('DM warning: more than one matching folder for project ' + project.name + ', assigning arbitrarily to ' + str(lastfolder).upper() + '...')
			else:
				p = Project()
				p.guid = uuid.uuid1()
				p.name = f
				p.fileName = f
				p.type = uuid.UUID(ProjectTypes.get('Folder'))

				lastfolder = p.guid
				folderprojects.setdefault(f, lastfolder)
				self.projects.setdefault(lastfolder, p)
		#oldfolder = self.nestedprojects.get(project.guid, None)
		#if oldfolder != lastfolder:
		#	print('DM warning: relocating ' + project.name + ' to ' + folder)
		self.nestedprojects[project.guid] = lastfolder

	def introspection(self):
		self.printreferences()

	def printreferences(self):
		for ksp,sp in self.projects.items():
			if not sp.loaded:
				continue
			refs = sp.loaded.getreferences()
			if refs:
				print(sp.name + ' has project references set:')
				for kr,r in refs.items():
					print('  ' + r)

	@property
	def toolset(self):
		return self._toolset

	@toolset.setter
	def toolset(self, value):
		self._toolset = value
		for kp,p in self.projects.items():
			if p.loaded:
				p.loaded.toolset = value

	@property
	def sdk(self):
		return self._sdk

	@sdk.setter
	def sdk(self, value):
		self._sdk = value
		for kp,p in self.projects.items():
			if p.loaded:
				p.loaded.sdk = value

class SolutionReader:
	def __init__(self, fileName):
		self.fileName = fileName
	
	def parse(self, parseprojects = False):
		s = Solution()
		s.fileName = self.fileName
		
		with open(self.fileName, 'r') as f:
			line = f.readline()
			while line:
				# Version
				if s.version is None:
					m = re.match('Microsoft Visual Studio Solution File, Format Version (.*)', line)
					if m:
						s.version = m.group(1)
					
				# Project
				if line.startswith('Project('):
					p = Project()
					m = re.match(r'Project\("\{(.*)\}"\) \= "(.*)", "(.*)", "\{(.*)\}"', line)
					if m:
						p.type = uuid.UUID(m.group(1))
						p.name = m.group(2)
						p.fileName = m.group(3)
						p.guid = uuid.UUID(m.group(4))
					# if str(p.type).upper() in ProjectTypes.keys():
						# print(str(p.guid) + ' = ' + p.name + ', ' + p.fileName + ', ' + ProjectTypes[str(p.type).upper()])
					# else:
						# print(str(p.guid) + ' = ' + p.name + ', ' + p.fileName + ', ' + str(p.type))
					
					line = f.readline()

					# Dependencies
					if line == '\tProjectSection(ProjectDependencies) = postProject\n':
						line = f.readline()
						while 'EndProjectSection' not in line:
							guid = re.search(r'\{(.*)\} = \{(.*)\}', line)
							# print('  ' + str(guid.group(1)))
							p.deps.append(uuid.UUID(guid.group(1)))
							line = f.readline()

					# SolutionItems
					if line == '\tProjectSection(SolutionItems) = preProject\n':
						line = f.readline()
						while 'EndProjectSection' not in line:
							item = re.search(r'\t\t(.*) = (.*)', line)
							# print('  ' + str(item.group(1)))
							p.items.append(item.group(1))
							line = f.readline()
							
					while line != 'EndProject\n':
						line = f.readline()
					
					s.projects[p.guid] = p
				
				# Global
				if line == 'Global\n':
					
					# Solution configs
					line = f.readline()
					if line == '\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n':
						line = f.readline()
						while 'EndGlobalSection' not in line:
							cfg = re.search(r'\t\t(.*) = (.*)', line)
							if cfg is None:
								print(line)
							s.configs.append(cfg.group(1))
							line = f.readline()

					# Project configs
					line = f.readline()
					if line == '\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n':
						line = f.readline()
						while 'EndGlobalSection' not in line:
							cfg = re.search(r'\t\t\{(.*)\}\.(.*)\.(.*) = (.*)', line)
							if cfg is None:
								print(line)
							s.projectconfigs.append((cfg.group(1), cfg.group(2), cfg.group(3), cfg.group(4)))
							line = f.readline()

					# Solution properties
					line = f.readline()
					if line == '\tGlobalSection(SolutionProperties) = preSolution\n':
						line = f.readline()
						while 'EndGlobalSection' not in line:
							cfg = re.search(r'\t\t(.*) = (.*)', line)
							if cfg is None:
								print(line)
							s.props.append((cfg.group(1), cfg.group(2)))
							line = f.readline()

					# Nested projects
					line = f.readline()
					if line == '\tGlobalSection(NestedProjects) = preSolution\n':
						line = f.readline()
						while 'EndGlobalSection' not in line:
							cfg = re.search(r'\t\t\{(.*)\} = \{(.*)\}', line)
							if cfg is None:
								print(line)
							s.nestedprojects.setdefault(uuid.UUID(cfg.group(1)), uuid.UUID(cfg.group(2)))
							line = f.readline()

					# Extensibility globals
					line = f.readline()
					if line == '\tGlobalSection(ExtensibilityGlobals) = postSolution\n':
						line = f.readline()
						while 'EndGlobalSection' not in line:
							cfg = re.search(r'\t\t(.*) = (.*)', line)
							if cfg is None:
								print(line)
							s.extensibilityglobals.append((cfg.group(1), cfg.group(2)))
							line = f.readline()

					# Test case management settings
					line = f.readline()
					if line == '\tGlobalSection(TestCaseManagementSettings) = postSolution\n':
						line = f.readline()
						while 'EndGlobalSection' not in line:
							cfg = re.search(r'\t\t(.*) = (.*)', line)
							if cfg is None:
								print(line)
							s.testcasemgmtsettings.append((cfg.group(1), cfg.group(2)))
							line = f.readline()
							
					while line != 'EndGlobal\n':
						line = f.readline()
						
				line = f.readline()
					
		if parseprojects:
			for k,sp in s.projects.items():
				try:
					sp.load()
				except:
					pass

		return s

class SolutionWriter:
	def __init__(self, solution = None):
		self.solution = solution

	def write(self, fileName):
		original = ''
		with open(fileName, 'r', encoding='utf-8-sig') as f:
			original = f.read()
		new = self.tostring()
		if original != new:
			print('sln: Updating ' + fileName)
			with open(fileName, 'w', encoding='utf-8-sig') as f:
				f.write(new)

	def tostring(self):
		s = ''
		s += '\n'
		s += 'Microsoft Visual Studio Solution File, Format Version ' + self.solution.version + '\n'
		s += '# Visual Studio Version 16\n'
		s += 'VisualStudioVersion = 16.0.28803.156\n'
		s += 'MinimumVisualStudioVersion = 10.0.40219.1\n'

		for k,p in self.solution.projects.items():
			s += 'Project("{' + str(p.type).upper() + '}") = "' + p.name + '", "' + p.fileName + '", "{' + str(p.guid).upper() + '}"\n'
			if p.deps:
				s += '\tProjectSection(ProjectDependencies) = postProject\n'
				for d in p.deps:
					s += '\t\t{' + str(d).upper() + '} = {' + str(d).upper() + '}\n'
				s += '\tEndProjectSection\n'
			if p.items:
				s += '\tProjectSection(SolutionItems) = preProject\n'
				for i in p.items:
					s += '\t\t' + i + ' = ' + i + '\n'
				s += '\tEndProjectSection\n'
			s += 'EndProject\n'

		s += 'Global\n'
		if self.solution.configs:
			s += '\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n'
			for c in self.solution.configs:
				s += '\t\t' + c + ' = ' + c + '\n'
			s += '\tEndGlobalSection\n'
		if self.solution.projectconfigs:
			s += '\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n'
			for c in self.solution.projectconfigs:
				s += '\t\t{' + c[0] + '}.' + c[1] + '.' + c[2] + ' = ' + c[3] + '\n'
			s += '\tEndGlobalSection\n'
		if self.solution.props:
			s += '\tGlobalSection(SolutionProperties) = preSolution\n'
			for c in self.solution.props:
				s += '\t\t' + c[0] + ' = ' + c[1] + '\n'
			s += '\tEndGlobalSection\n'
		if self.solution.nestedprojects:
			s += '\tGlobalSection(NestedProjects) = preSolution\n'
			for kc,c in self.solution.nestedprojects.items():
				s += '\t\t{' + str(kc).upper() + '} = {' + str(c).upper() + '}\n'
			s += '\tEndGlobalSection\n'
		if self.solution.extensibilityglobals:
			s += '\tGlobalSection(ExtensibilityGlobals) = postSolution\n'
			for c in self.solution.extensibilityglobals:
				s += '\t\t' + c[0] + ' = ' + c[1] + '\n'
			s += '\tEndGlobalSection\n'
		if self.solution.testcasemgmtsettings:
			s += '\tGlobalSection(TestCaseManagementSettings) = postSolution\n'
			for c in self.solution.testcasemgmtsettings:
				s += '\t\t' + c[0] + ' = ' + c[1] + '\n'
			s += '\tEndGlobalSection\n'
		s += 'EndGlobal\n'

		return s
