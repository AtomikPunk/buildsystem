import buildsystem.buildsystem as bs
import buildsystem.vc14_x64 as vc14_x64
from buildsystem.consolecolors import consolecolors as cc

import argparse

argparser = argparse.ArgumentParser(description = 'buildsystem build script')
argparser.add_argument('-t', '--tasks', help = 'comma separated list of tasks , eg: clean,build', default = 'build')
argparser.add_argument('-c', '--colors', action = 'store_true', help = 'colored output')
argparser.add_argument('-v', '--verbose', action = 'store_true', help = 'verbose output')
argparser.add_argument('-f', '--file', help = 'path to spec file', default = 'build.bs')
args = argparser.parse_args()

import time
start_time = time.time()

import importlib.util, importlib.machinery
importlib.machinery.SOURCE_SUFFIXES.append('') # Allow any file extension
spec = importlib.util.spec_from_file_location('buildscript',args.file)
mod = importlib.util.module_from_spec(spec)
importlib.machinery.SOURCE_SUFFIXES.pop() # Revert to known file extensions
spec.loader.exec_module(mod)
#print(dir(mod))

bs.verbose = args.verbose
cc.enable = args.colors

tc = vc14_x64.toolchain()

# print('\n'.join([str(b) for b in tc.builders]))

if not hasattr(mod, 'spec'):
	print('Error: build script must define spec')
else:
	for t in args.tasks.split(','):
		op = getattr(tc, t, None)
		if callable(op):
			print('Task: ' + t)
			op(mod.spec)
		else:
			print('Warning: unsupported task ' + t)

end_time = time.time()
print('Execution time: ' + str(round(end_time - start_time, 6)) + 's')
