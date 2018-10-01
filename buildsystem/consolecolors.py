class consolecolors(object):
	enable = True

	@property
	def black(self):
		if self.enable:
			return '\u001b[30m'
		else:
			return ''
		
	@property
	def red(self):
		if self.enable:
			return '\u001b[31m'
		else:
			return ''
		
	@property
	def green(self):
		if self.enable:
			return '\u001b[32m'
		else:
			return ''
		
	@property
	def yellow(self):
		if self.enable:
			return '\u001b[33m'
		else:
			return ''
		
	@property
	def blue(self):
		if self.enable:
			return '\u001b[34m'
		else:
			return ''
		
	@property
	def magenta(self):
		if self.enable:
			return '\u001b[35m'
		else:
			return ''
		
	@property
	def cyan(self):
		if self.enable:
			return '\u001b[36m'
		else:
			return ''
		
	@property
	def white(self):
		if self.enable:
			return '\u001b[37m'
		else:
			return ''
		
	@property
	def reset(self):
		if self.enable:
			return '\u001b[0m'
		else:
			return ''
