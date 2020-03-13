from . import vcxproj
from . import sln

import json
import ruamel_yaml
import ruamel_yaml.emitter
import binascii
import glob
import os
import uuid
import zipfile
import re
import copy

import jinja2

class DependencyManager(object):
	def __init__(self, sln):
		self.sln = sln

		# Prefix to prepend to all managed items (defines, incdirs, libdirs, libs and post-build commands), use '' to have no prefix...
		self.prefix = ''
		# Strip config already present in project files? Use True to completely manage dependencies using this tool... Use False to only add missing dependencies, without removing those unknown to this tool...
		self.stripconfig = True
		# Sort items (defines, incdirs, libdirs, libs and post-build commands)? Cleaner if True...
		self.sorted = True
		# Create missing projects?
		self.manageprojects = False#True
		# Use post-build commands (to manage binaries)? If false, will rely on binaries mechanism in project dependencies
		self.usepostbuildcommands = True#False
		# Keep unused project dependencies? An unused dependency is one defined in the solution but not required by the project definitions (source code, library, path, post-build action, etc.)
		self.keepunuseddeps = False#True
		# Warn user of unused project dependencies?
		self.warmunuseddeps = True

		# Parameters for the "CopyDeps" script
		# Solution directory (corresponding to the $(SolutionDir) variable in msbuild)
		self.solutiondir = ''
		# Configuration to pack
		self.configuration = 'Release'
		# Platform to pack
		self.platform = 'x64'
		# Output directory (corresponding to the $(OutDir) variable in msbuild)
		self.outdir = ''
		# Extra commands to include in "CopyDeps" script
		self.copydepsextracommands = ''

		self.loaddeps()

	def loaddeps(self):
		with open(self.sln.fileName + '.deps.yaml') as f:
			# Read "raw" yaml config file
			content = f.read()

			# Render using jinja2
			jenv = jinja2.Environment().from_string(content)
			rendered = jenv.render()
			with open(self.sln.fileName + '.rendered.yaml', 'w') as f:
				f.write(rendered)

			# Load jinja2-rendered config file
			yaml = ruamel_yaml.YAML()
			self.deps = yaml.load(rendered)

	def introspection(self):
		print('Dependencies introspection')
		self.validateDirectories()
		self.removedependenciesfromfolders()
		self.findnoninterfacelibs()

	def validateDirectories(self):
		print('  Validate directories')

		slnDir = os.path.dirname(os.path.abspath(self.sln.fileName)) + '/'

		for kp,p in self.deps.items():
			for tag in ['incdirs', 'libdirs']:
				for d in p.get(tag,{}).keys():

					try:
						sp = self.sln.getproject(kp)[0][1]

						rdr = vcxproj.reader()
						rootnode = rdr.read(sp.fileName)
						vcx = vcxproj.vcxproj(rootnode)

						for c in vcx.getconfigurations():
							dir = d

							dir = dir.replace('$(OutDir)', os.path.dirname(vcx.getoutdir(c)))

							dir = dir.replace('$(SolutionDir)', slnDir)

							# Warn if $(ProjectDir) is used
							if '$(ProjectDir)' in dir:
								print('    ' + kp + ': ' + tag + ' ' + d + ' [' + c + '] contains $(ProjectDir)')
								dir = dir.replace('$(ProjectDir)', os.path.dirname(os.path.abspath(sp.fileName)) + '/')
								print('      ' + dir)

							if dir.startswith('.'):
								dir = os.path.dirname(os.path.abspath(sp.fileName)) + '/' + dir

							(cfg, pfm) = c.split('|')
							dir = dir.replace('$(Configuration)', cfg)
							dir = dir.replace('$(ConfigurationName)', cfg)
							dir = dir.replace('$(Platform)', pfm)

							dir = os.path.abspath(dir)
							if not os.path.exists(dir):
								print('    ' + kp + ': ' + tag + ' ' + d + ' [' + c + '] does not exist')
								print('      ' + dir)
							elif os.path.isfile(dir):
								print('    ' + kp + ': ' + tag + ' ' + d + ' [' + c + '] exists but is a file')
								print('      ' + dir)

					# Not a solution project
					except IndexError:
						if '$(OutDir)' in d:
							print('    ' + kp + ': ' + tag + ' ' + d + ' contains $(OutDir) but is not found in solution')
						if '$(ProjectDir)' in d:
							print('    ' + kp + ': ' + tag + ' ' + d + ' contains $(ProjectDir) but is not found in solution')

	def removedependenciesfromfolders(self):
		print('  Remove dependencies from folders')

		for u,p in self.sln.projects.items():
			if p.isfolder() and p.deps:
				print('    ' + p.name + ' is a folder and has dependencies. Fixing.')
				p.deps = []

	def findnoninterfacelibs(self):
		print('  Find manually managed library dependencies (not defined as interface)')

		for kp,p in self.deps.items():
			for kl,l in p.get('libs',{}).items():
				if not l or 'interface' not in l:
					print('    ' + kp + ': depends on manually managed (non-interface) library ' + kl)

	def getvalues(self, name, tag, cfg):
		deps = self.getdeps(name)

		values = {}
		noninterfacedeps = {k:v for k,v in deps.items() if not v or 'interface' not in v}
		for dk,d in noninterfacedeps.items():
			# Get children public or interface (not private) items enabled for this configuration or all configurations
			found = {k:v for k,v in self.deps.get(dk).get(tag, {}).items() if v and ((not v.get('config', {}) or cfg in v.get('config', {})) and ('public' in v or 'interface' in v))}
			values.update(found)

		# Get private or public (not interface) items enabled for this configuration or all configurations
		found = {k:v for k,v in self.deps.get(name).get(tag, {}).items() if not v or ((not v.get('config', {}) or cfg in v.get('config', {})) and 'interface' not in v)}
		values.update(found)

		return values

	def getdeps(self, name):
		dep = self.deps.get(name)
		deps = {}
		for d,a in dep.get('deps', {}).items():
			deps = self.mergedeps(deps, self.getpublicdeps(d, a))
		deps = self.mergedeps(deps, dep.get('deps', {}))

		return deps

	def mergedeps(self, deps1, deps2):
		# Merge and flatten a dictionary of dependencies (name, spec)
		deps = deps1
		for dk,d2 in deps2.items():
			if dk not in deps:
				# Dep is new, simply reuse dep...
				deps.setdefault(dk, d2)
				continue

			# Otherwise we need to merge
			# Something to do if spec is None?

			# Merge visibility
			d1 = deps1.get(dk)
			deps[dk] = self.mergedep(d1, d2)

			if d2:
				for ik,i in d2.items():
					if ik == 'deps':
						for ck,c in i.items():
							childdeps = self.getpublicdeps(ck, c)
							deps = self.mergedeps(deps, childdeps)

		return deps

	def mergedep(self, dep1, dep2):
		if dep1 is None and dep2 is None:
			return None

		if dep1 and 'interface' in dep1 and dep2 and 'interface' in dep2:
			# interface
			dep = copy.copy(dep1)
			# in case... Should not be required if spec is well-formed
			dep.pop('private', None)
			dep.pop('public', None)
		elif (dep1 is None or 'private' in dep1) and (dep2 is None or 'private' in dep2):
			# private
			if dep1 is not None:
				dep = copy.copy(dep1)
			else:
				dep = copy.copy(dep2)
			dep.pop('public', None)
			dep.pop('interface', None)
		else:
			if dep1 is not None:
				dep = copy.copy(dep1)
			else:
				dep = copy.copy(dep2)
			dep.setdefault('public', None)
			dep.pop('private', None)
			dep.pop('interface', None)

		return dep

	def getpublicdeps(self, name, spec):
		dep = self.deps.get(name)
		if not dep:
			raise KeyError('Dep ' + name + ' does not exist')
		deps = {}

		publicdeps = {k:v for k,v in dep.get('deps', {}).items() if v and ('public' in v.keys() or 'interface' in v.keys())}
		for d,a in publicdeps.items():
			childdeps = self.getpublicdeps(d, a)
			deps = self.mergedeps(deps, childdeps)

			deps = self.mergedeps(deps, {d:a})

		return deps

	def write(self):
		with open(self.sln.fileName + '.generated.deps.yaml', 'w') as f:
			yaml = ruamel_yaml.YAML()
			yaml.emitter.MAX_SIMPLE_KEY_LENGTH = 9999 # Fix truncating long keys...
			yaml.dump(self.deps, f)

		w = sln.SolutionWriter(self.sln)
		w.write(self.sln.fileName)

		for u,p in self.sln.projects.items():
			if p.loaded:
				w = vcxproj.writer(p.loaded)
				w.write(p.fileName)

		self.writecopydeps()

	def writecopydeps(self):
		with open(self.sln.fileName + '.copydeps.bat', 'w') as f:
			depswithpostbuildcommands = {k:v for k,v in self.deps.items() if not os.path.isfile(self.projectpathfordep(k, v)) and 'postbuildcommands' in v and v.get('postbuildcommands',None) is not None}
			for dk,dv in depswithpostbuildcommands.items():
				f.write('::' + dk + '\n')
				for ck,cv in dv.get('postbuildcommands').items():
					cmd = ck.replace('$(SolutionDir)', self.solutiondir).replace('$(Configuration)', self.configuration).replace('$(Platform)', self.platform).replace('$(OutDir)', self.outdir)
					f.write(cmd + '\n')

			f.write(self.copydepsextracommands)

	def update(self):
		if self.manageprojects:
			for n in self.deps.keys():
				self.createprojectfiles(n)
		for u,p in self.sln.projects.items():
			self.updateproject(p)

	def updateproject(self, project):
		if not project.loaded or project.name not in self.deps:
			return

		self.updatebinaries(project)
		self.updatedefines(project)
		self.updateincdirs(project)
		self.updatelibdirs(project)
		self.updatelibs(project)
		self.updatepostbuildcommands(project)

		self.updatedependencies(project)

	def projectpathfordep(self, name, dep):
		prj = dep.get('project',{})
		dir = next(iter(prj.get('directory',{'':None})))
		filename = next(iter(prj.get('filename',{name:None})))
		path = dir.rstrip('/') + '/' + filename + '.vcxproj'
		return path

	def createprojectfiles(self, name):
		try:
			dep = self.deps.get(name)
			spec = dep.get('project')

			guid = None
			path = self.projectpathfordep(name, spec)

			# Is GUID provided?
			if 'uuid' in spec:
				guid = uuid.UUID(next(iter(spec.get('uuid', None))))

				# Is GUID found in solution?
				if guid in self.sln.projects:
					prj = self.sln.projects.get(guid)

					# Validate if it is consistent before returning...
					if prj.name != name:
						print('DM warning: changing project ' + str(guid).upper() + ' name from ' + prj.name + ' to ' + name)
						prj.name = name
					if prj.fileName != path:
						print('DM warning: relocating project ' + str(guid).upper() + ' from ' + prj.fileName + ' to ' + path)
						prj.fileName = path

					return

				# Load project if it already exist
				if os.path.isfile(path):
					r = vcxproj.reader()
					newproj = vcxproj.vcxproj(r.read(path))
					# TODO: We should also validate project name from vcxproj file...
					if guid != newproj.getguid():
						print('DM error: ' + path + ' does not match requested GUID ' + str(guid).upper())
						return
				# Otherwise create a new project
				else:
					newproj = vcxproj.vcxproj.createdefault(name, guid)

			# No GUID provided, is project file path in solution?
			elif path in [p.fileName for k,p in self.sln.projects.items()]:
				# Use GUID assigned to this project file path from solution
				guid = next(k for k,p in self.sln.projects.items() if path == p.fileName)

				# Load project if it already exist
				if os.path.isfile(path):
					r = vcxproj.reader()
					newproj = vcxproj.vcxproj(r.read(path))
					if guid != newproj.getguid():
						print('DM error: ' + path + ' does not match requested GUID ' + str(guid).upper())
						return

				# Otherwise create a new project
				else:
					newproj = vcxproj.vcxproj.createdefault(name, guid)

			# No GUID provided and project file not in solution, create a new one!
			else:
				# Load project if it already exist
				if os.path.isfile(path):
					r = vcxproj.reader()
					newproj = vcxproj.vcxproj(r.read(path))
					guid = newproj.getguid()
				# Otherwise create a new project
				else:
					newproj = vcxproj.vcxproj.createdefault(name)
					guid = newproj.getguid()
					if guid in self.sln.projects:
						print('DM error: could not create unique GUID for project' + name)
						return

			p = sln.Project(name, guid, path, sln.ProjectTypes.get('C++'), newproj)
			self.sln.projects.setdefault(guid, p)

			if 'solutionfolder' in spec:
				slnfolder = next(iter(spec.get('solutionfolder', None)))
				self.sln.setfolder(p, slnfolder)

		except Exception as e:
			# If anything is wrong (project tag is not present, name is invalid, etc.), simply return without creating the project...
			pass

	def updatedependencies(self, project):
		try:
			proj = self.sln.getproject(project.name)[0][1]
		except IndexError: # If proj is not found in self.sln.projects...
			return

		unuseddeps = proj.deps[:]
		proj.deps = []

		deps = self.deps.get(project.name).get('deps', {})
		for d in deps:
			try:
				dep = self.sln.getproject(d)[0][1]
				if dep.guid in unuseddeps:
					unuseddeps.remove(dep.guid)
					#print(project.name + ' removing ' + dep.name + ' from unuseddeps')
				else:
					print('DM info: ' + project.name + ' adding solution dependency to ' + dep.name)
				proj.deps.append(dep.guid)
			except (StopIteration, IndexError): # If dep is not found in self.sln.projects...
				pass

		if self.keepunuseddeps and self.warmunuseddeps:
			for u in unuseddeps:
				dep = self.sln.getproject(u)[0][1]
				print('DM warning: ' + project.name + ' keeping unused solution dependency to ' + dep.name)
				proj.deps.append(dep.guid)
		elif not self.keepunuseddeps:
			for u in unuseddeps:
				try:
					dep = self.sln.getproject(u)[0][1]
					print('DM info: ' + project.name + ' removing solution dependency to ' + dep.name)
				except IndexError:
					pass

	def updatebinaries(self, project):
		for c in project.loaded.getconfigurations():
			items = project.loaded.getbinaries(c)
			items = self.updatetag(project, 'binaries', items, c)
			project.loaded.setbinaries(c, items)

	def updatedefines(self, project):
		for c in project.loaded.getconfigurations():
			items = project.loaded.getdefines(c)
			items = self.updatetag(project, 'defines', items, c)
			project.loaded.setdefines(c, items)

	def updateincdirs(self, project):
		for c in project.loaded.getconfigurations():
			items = project.loaded.getincdirs(c)
			items = self.updatetag(project, 'incdirs', items, c)
			project.loaded.setincdirs(c, items)

	def updatelibdirs(self, project):
		for c in project.loaded.getconfigurations():
			items = project.loaded.getlibdirs(c)
			items = self.updatetag(project, 'libdirs', items, c)
			project.loaded.setlibdirs(c, items)

	def updatelibs(self, project):
		for c in project.loaded.getconfigurations():
			items = project.loaded.getlibs(c)
			items = self.updatetag(project, 'libs', items, c)
			project.loaded.setlibs(c, items)

	def updatepostbuildcommands(self, project):
		for c in project.loaded.getconfigurations():
			items = project.loaded.getpostbuildcommands(c)
			if self.usepostbuildcommands:
				items = self.updatetag(project, 'postbuildcommands', items, c)
			else:
				items = {}
			project.loaded.setpostbuildcommands(c, items)

	def updatetag(self, project, tag, items, cfg):
		depitems = self.getvalues(project.name, tag, cfg)

		# If asked to strip config, we simply start from scratch
		if self.stripconfig:
			items = {}

		# Remove all entries we manage ourselves (that have our prefix)
		if self.prefix:
			items = {k:x for k,x in items.items() if not k.startswith(self.prefix)}

		# Also remove duplicates
		for d in depitems:
			if d in items:
				items.remove(d)

		# Now add our managed deps sorted or not depending on user preference
		if self.sorted:
			deptuples = sorted(depitems.items())
		else:
			deptuples = depitems.items()

		# Start with items used in all configurations
		genericdeps = {k:v for (k,v) in deptuples if not v or not v.get('config',False)}
		for ki,i in genericdeps.items():
			items[self.prefix + ki] = i
		# Finish with items not in all configurations (they will appear as "different options" in VS GUI)
		specificdeps = {k:v for (k,v) in deptuples if v and v.get('config',False) and cfg in v.get('config')}
		for ki,i in specificdeps.items():
			items[self.prefix + ki] = i

		return items

	# Move a (private) library to dependencies
	def movetodeps(self, depname, tag, item, depvisibility = 'interface'):
		# Create library interface in dep
		self.deps.get(depname).setdefault(tag, {}).setdefault(item, {depvisibility: None})

		# Convert all requested tag items to deps
		matching = {k:v for k,v in self.deps.items() if v and item in v.get(tag,{}) and (not v.get(tag).get(item) or 'interface' not in v.get(tag).get(item))}
		for km,m in matching.items():
			m.get(tag).pop(item)
			if not m.get(tag):
				m.pop(tag)
			m.setdefault('deps', {}).setdefault(depname, None)

	def printdepswithouttag(self, depname, tag, regex):
		d = {k:v for k,v in self.deps.items() if v and depname in v.get('deps', {})}
		for k,v in d.items():
			found = False
			for ki,i in v.get(tag, {}).items():
				if re.search(regex, ki):
					found = True
					break
			if not found:
				print(k + ' does not match ' + regex + ' in ' + tag + ' for ' + depname)

	def printtagswithoutdep(self, depname, tag, regex):
		for k,v in self.deps.items():
			for ki,i in v.get(tag, {}).items():
				if re.search(regex, ki):
					if depname not in v.get('deps', {}):
						print(k + ' matches ' + regex + ' in ' + tag + ' but does not depend on ' + depname)

	def InstallPackages(self, repodir, destdir):
		for kd,d in self.deps.items():
			for kp,p in d.get('packages', {}).items():
				self.SyncPackage(repodir, kp, destdir)

	def SyncPackage(self, repodir, pkg, destdir):
		try:
			with zipfile.ZipFile(os.path.join(repodir, pkg), 'r') as z:
				try:
					for i in z.infolist():
						if i.is_dir():
							continue

						with open(os.path.join(destdir, i.filename), 'rb') as f:
							if i.CRC != binascii.crc32(f.read()):
								raise ValueError()
					print(pkg + ': synced')
				except:
					# If any file is missing or different, simply overwrite...
					z.extractall(destdir)
					print(pkg + ': extracted')
		except FileNotFoundError as e:
			print(kp + ': not found!')
