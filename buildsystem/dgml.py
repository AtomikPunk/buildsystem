
class DirectedGraph(object):
	def __init__(self):
		self.title = ''
		self.nodes = {}
		self.links = []
		self.categories = {}

	def write(self, fileName):
		with open(fileName, 'w') as f:
			f.write('<?xml version="1.0" encoding="utf-8"?>\n')
			f.write('<DirectedGraph Title="' + self.title + '" xmlns="http://schemas.microsoft.com/vs/2009/dgml">\n')

			if self.nodes:
				f.write('\t<Nodes>\n')
				for k,v in self.nodes.items():
					f.write('\t\t<Node Id="' + str(k) + '" Label="' + v['Label'] + '" Category="' + v['Category'] + '" ')
					if 'Group' in v.keys():
						f.write('Group="' + v['Group'] + '" ')
					f.write('/>\n')
				f.write('\t</Nodes>\n')

			if self.links:
				f.write('\t<Links>\n')
				for l in self.links:
					f.write('\t\t<Link Source="' + str(l['Source']) + '" Target="' + str(l['Target']) + '" Category="' + l['Category'] + '" />\n')
				f.write('\t</Links>\n')

			if self.categories:
				f.write('\t<Categories>\n')
				for ck,c in self.categories.items():
					f.write('\t\t<Category Id="' + ck + '"')
					for k,v in c.items():
						f.write(' ' + k + '="' + v + '"')
					f.write(' />\n')
				f.write('\t</Categories>\n')

			f.write('</DirectedGraph>\n')