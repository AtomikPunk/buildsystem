# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 14:28:54 2018

@author: fdinel
"""

import os
import re

class ProjectConfig:
	def __init__(self):
		self.incdirs = []
		self.incdirsnode = None
		self.libs = []
		self.libsnode = None
		self.libdirs = []
		self.libdirsnode = None
		self.output = ''
		self.outputnode = None
		self.importlib = ''
		self.importlibnode = None
		self.postbuildcommand = []
		self.postbuildcommandnode = None
		self.configtype = ''
		self.targetext = ''
		self.platformtoolset = None
		self.characterset = None
		self.usedebuglibs = None
		self.wholeprogramoptimization = None
		self.linkincremental = None

class Project:
	def __init__(self):
		self.fileName = ''
		self.configs = {}
		self.tree = None
		self.name = ''
		self.guid = None
