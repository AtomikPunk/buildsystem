
import vs.sln
import karma.dgml

class slndepsdgml(object):
	def getdgml(self, sln, prjs, deps, skips):
		g = karma.dgml.DirectedGraph()

		for k,d in deps.items():
			g.nodes[k] = {'Label': k, 'Category': 'Dependency', 'Group': 'Collapsed'}
			if 'includedirs' in d.keys():
				for i in d['includedirs']:
					if i in skips['includedirs']:
						continue
					g.nodes[i] = {'Label': i, 'Category': 'IncludeDir'}
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'}) # Special Category for groups
			if 'libdirs' in d.keys():
				for i in d['libdirs']:
					if i in skips['libdirs']:
						continue
					g.nodes[i] = {'Label': i, 'Category': 'LibDir'}
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'}) # Special Category for groups
			if 'libs' in d.keys():
				for i in d['libs']:
					if i in skips['libs']:
						continue
					g.nodes[i] = {'Label': i, 'Category': 'Lib'}
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'}) # Special Category for groups
			if 'postbuildcommand' in d.keys():
				for i in d['postbuildcommand']:
					if i in skips['postbuildcommand']:
						continue
					g.nodes[i] = {'Label': i, 'Category': 'PostBuildCommand'}
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'}) # Special Category for groups

		for k,p in prjs.items():
			# Create project node
			g.nodes.setdefault(k, {'Label': k, 'Category': 'Project', 'Group': 'Collapsed'})

			if 'includedirs' in p.keys():
				for i in p['includedirs']:
					g.nodes.setdefault(i, {'Label': i, 'Category': 'IncludeDir'})
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'})
			if 'libdirs' in p.keys():
				for i in p['libdirs']:
					g.nodes.setdefault(i, {'Label': i, 'Category': 'LibDir'})
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'})
			if 'libs' in p.keys():
				for i in p['libs']:
					g.nodes.setdefault(i, {'Label': i, 'Category': 'Lib'})
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'})
			if 'output' in p.keys():
				for i in p['output']:
					g.nodes.setdefault(i, {'Label': i, 'Category': 'Output'})
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'})
			if 'postbuildcommand' in p.keys():
				for i in p['postbuildcommand']:
					g.nodes.setdefault(i, {'Label': i, 'Category': 'PostBuildCommand'})
					g.links.append({'Source': k, 'Target': i, 'Category': 'Contains'})

		for k,sp in sln.projects.items():
			# Create solution project nodes
			g.nodes.setdefault(sp.name, {'Label': sp.name, 'Category': 'Project', 'Group': 'Collapsed'})

			# Create deps links
			for d in sp.deps:
				p = sln.projects.get(d)
				g.links.append({'Source': sp.name, 'Target': p.name, 'Category': 'Dependency'})

			if sp.loaded:
				for ck,c in sp.loaded.configs.items():
					# Create configs
					g.nodes[sp.name+ck] = {'Label': ck, 'Category': 'Config', 'Group': 'Collapsed'}
					g.links.append({'Source': sp.name, 'Target': sp.name+ck, 'Category': 'Contains'}) # Special Category for groups
					# Create output
					g.nodes[c.output] = {'Label': c.output, 'Category': 'Output'}
					g.links.append({'Source': sp.name, 'Target': c.output, 'Category': 'Contains'}) # Special Category for groups
					# Create import lib
					if c.importlib:
						g.nodes[c.importlib] = {'Label': c.importlib, 'Category': 'ImportLib'}
						g.links.append({'Source': sp.name, 'Target': c.importlib, 'Category': 'Contains'}) # Special Category for groups

					for i in c.incdirs:
						if i in skips['includedirs']:
							continue
						if i not in g.nodes:
							g.nodes[i] = {'Label': i, 'Category': 'MissingIncludeDir'}
						g.links.append({'Source': sp.name+ck, 'Target': i, 'Category': 'IncludeDir'})
					for i in c.libdirs:
						if i in skips['libdirs']:
							continue
						if i not in g.nodes:
							g.nodes[i] = {'Label': i, 'Category': 'MissingLibDir'}
						g.links.append({'Source': sp.name+ck, 'Target': i, 'Category': 'LibDir'})
					for i in c.libs:
						if i in skips['libs']:
							continue
						if i not in g.nodes:
							g.nodes[i] = {'Label': i, 'Category': 'MissingLib'}
						g.links.append({'Source': sp.name+ck, 'Target': i, 'Category': 'Lib'})

		g.categories['Missing'] = {'Background': 'Red'}
		g.categories['MissingIncludeDir'] = {'BasedOn': 'Missing'}
		g.categories['MissingLibDir'] = {'BasedOn': 'Missing'}
		g.categories['MissingLib'] = {'BasedOn': 'Missing'}

		g.categories['Dependency'] = {'Background': 'LightBlue'}
		g.categories['IncludeDir'] = {'Background': 'Yellow'}
		g.categories['Lib'] = {'Background': 'Green'}
		g.categories['LibDir'] = {'Background': 'LightGreen'}
		g.categories['PostBuildCommand'] = {'Background': 'Blue'}

		return g