# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 13:50:50 2018

@author: fdinel
"""

import uuid
import re

ProjectTypes = {
	'2150E333-8FDC-42A3-9474-1A3956D46DE8' : 'Folder',
	'8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942' : 'C++',
	}

class Project:
	def __init__(self):
		self.guid = None
		self.name = ''
		self.fileName = ''
		self.type = None
		self.deps = []
		self.items = []
		self.loaded = None

class Solution:
	def __init__(self):
		self.fileName = ''
		self.version = None
		self.projects = {}
		self.configs = []
		self.projectconfigs = []
		self.props = []
		self.nestedprojects = []
		self.testcasemgmtsettings = []

class SolutionReader:
	def __init__(self, fileName):
		self.fileName = fileName
	
	def parse(self):
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
							s.nestedprojects.append((cfg.group(1), cfg.group(2)))
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
					
		return s

class SolutionWriter:
	def __init__(self, solution = None):
		self.solution = solution
		
	def write(self, fileName):
		with open(fileName, 'w') as f:
			f.write('\n')
			f.write('Microsoft Visual Studio Solution File, Format Version ' + self.solution.version + '\n')
			f.write('# Visual Studio 14\n')
			f.write('VisualStudioVersion = 14.0.25420.1\n')
			f.write('MinimumVisualStudioVersion = 10.0.40219.1\n')

			for k,p in self.solution.projects.items():
				f.write('Project("{' + str(p.type).upper() + '}") = "' + p.name + '", "' + p.fileName + '", "{' + str(p.guid).upper() + '}"\n')
				if p.deps:
					f.write('\tProjectSection(ProjectDependencies) = postProject\n')
					for d in p.deps:
						f.write('\t\t{' + str(d).upper() + '} = {' + str(d).upper() + '}\n')
					f.write('\tEndProjectSection\n')
				if p.items:
					f.write('\tProjectSection(SolutionItems) = preProject\n')
					for i in p.items:
						f.write('\t\t' + i + ' = ' + i + '\n')
					f.write('\tEndProjectSection\n')
				f.write('EndProject\n')

			f.write('Global\n')
			if self.solution.configs:
				f.write('\tGlobalSection(SolutionConfigurationPlatforms) = preSolution\n')
				for c in self.solution.configs:
					f.write('\t\t' + c + ' = ' + c + '\n')
				f.write('\tEndGlobalSection\n')
			if self.solution.projectconfigs:
				f.write('\tGlobalSection(ProjectConfigurationPlatforms) = postSolution\n')
				for c in self.solution.projectconfigs:
					f.write('\t\t{' + c[0] + '}.' + c[1] + '.' + c[2] + ' = ' + c[3] + '\n')
				f.write('\tEndGlobalSection\n')
			if self.solution.props:
				f.write('\tGlobalSection(SolutionProperties) = preSolution\n')
				for c in self.solution.props:
					f.write('\t\t' + c[0] + ' = ' + c[1] + '\n')
				f.write('\tEndGlobalSection\n')
			if self.solution.nestedprojects:
				f.write('\tGlobalSection(NestedProjects) = preSolution\n')
				for c in self.solution.nestedprojects:
					f.write('\t\t{' + c[0] + '} = {' + c[1] + '}\n')
				f.write('\tEndGlobalSection\n')
			if self.solution.testcasemgmtsettings:
				f.write('\tGlobalSection(TestCaseManagementSettings) = postSolution\n')
				for c in self.solution.testcasemgmtsettings:
					f.write('\t\t' + c[0] + ' = ' + c[1] + '\n')
				f.write('\tEndGlobalSection\n')
			f.write('EndGlobal\n')
