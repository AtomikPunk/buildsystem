from . import dgml

class depsdgml(object):
	def __init__(self, deps):
		self.deps = deps

	def getdgml(self):
		g = dgml.DirectedGraph()

		for kp,p in self.deps.items():

			g.nodes.setdefault(kp, {'Category': 'Project', 'Group': 'Collapsed'})

			for kd,d in p.get('deps', {}).items():
				g.links.append({'Source': kp, 'Target': kd})

			for kl,l in p.get('incdirs', {}).items():
				g.nodes.setdefault(kl, {'Category': 'IncludeDir'})
				link = {'Source': kp, 'Target': kl}
				if l and ('interface' in l or 'public' in l):
					link['Category'] = 'Contains'
				g.links.append(link)

			for kl,l in p.get('libs', {}).items():
				g.nodes.setdefault(kl, {'Category': 'Lib'})
				link = {'Source': kp, 'Target': kl}
				if l and 'interface' in l:
					link['Category'] = 'Contains'
				g.links.append(link)

			for ksf,sf in p.get('project', {}).get('solutionfolder', {}).items():
				foldernode = self.getorcreatefoldernode(g, ksf)
				g.links.append({'Source': foldernode, 'Target': kp, 'Category': 'Contains'})

		g.categories['Define'] = {'Background': 'LightOrange'}
		g.categories['Dependency'] = {'Background': 'LightBlue'}
		g.categories['Folder'] = {'Background': 'LightPink'}
		g.categories['ImportLib'] = {'BasedOn': 'Lib'}
		g.categories['IncludeDir'] = {'Background': 'LightYellow'}
		g.categories['Lib'] = {'Background': 'LightBlue'}
		g.categories['LibDir'] = {'Background': 'LightCyan'}
		g.categories['Output'] = {'Background': 'LightSkyBlue'}
		g.categories['PostBuildCommand'] = {'Background': 'LightGreen'}

		g.categories['Missing'] = {'Background': 'Red'}
		g.categories['MissingDefine'] = {'BasedOn': 'Define', 'Foreground': 'Red'}
		g.categories['MissingIncludeDir'] = {'BasedOn': 'IncludeDir', 'Foreground': 'Red'}
		g.categories['MissingLib'] = {'BasedOn': 'Lib', 'Foreground': 'Red'}
		g.categories['MissingLibDir'] = {'BasedOn': 'LibDir', 'Foreground': 'Red'}
		g.categories['MissingPostBuildCommand'] = {'BasedOn': 'PostBuildCommand', 'Foreground': 'Red'}

		return g

	def getorcreatefoldernode(self, graph, folder):
		folders = folder.split('/')
		folderstr = None
		for f in folders:
			if folderstr:
				newfolderstr = folderstr + '_' + f
				if not graph.nodes.get(newfolderstr, False):
					graph.nodes.setdefault(newfolderstr, {'Label': f, 'Category': 'Folder', 'Group': 'Collapsed'})
					graph.links.append({'Source': folderstr, 'Target': newfolderstr, 'Category': 'Contains'})
				folderstr = newfolderstr
			else:
				folderstr = f
				if not graph.nodes.get(folderstr, False):
					graph.nodes.setdefault(folderstr, {'Label': f, 'Category': 'Folder', 'Group': 'Collapsed'})
		return folderstr