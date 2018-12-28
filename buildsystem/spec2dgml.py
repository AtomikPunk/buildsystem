import buildsystem.buildsystem as bs
import buildsystem.dgml as dgml

def longname(dep):
	return dep.name+'['+dep.__class__.__name__+']'

def getdepnode(dep):
	return {'Label': longname(dep), 'Category': dep.__class__.__name__}

def getdepnodes(dep):
	n = {longname(dep): getdepnode(dep)}
	for d in dep.deps:
		n.update(getdepnodes(d))
	return n

def getdeplink(src, tgt):
	return {'Source': longname(src), 'Target': longname(tgt), 'Category': 'Dependency'}

def getdeplinks(dep):
	l = [getdeplink(dep,d) for d in dep.deps]
	for d in dep.deps:
		l.extend(getdeplinks(d))
	return l

def spec2dgml(dep):
	g = dgml.DirectedGraph()
	g.nodes = getdepnodes(dep)
	g.links = getdeplinks(dep)
	return g