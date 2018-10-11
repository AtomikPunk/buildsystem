import buildsystem.buildsystem as bs
import buildsystem.vc14_x64 as vc14_x64
from buildsystem.consolecolors import consolecolors as cc

import time
import argparse

argparser = argparse.ArgumentParser(description = 'buildsystem build script')
argparser.add_argument('targets', help = 'clean | build')
argparser.add_argument('-c', '--colors', action = 'store_true', help = 'colored output')
argparser.add_argument('-v', '--verbose', action = 'store_true', help = 'verbose output')
args = argparser.parse_args()

start_time = time.time()

bs.verbose = args.verbose
cc.enable = args.colors

tc = vc14_x64.toolchain()

e1 = bs.executable('myproj', srcs = ['mysrc1.cpp'])
p1 = bs.project('myproj', [e1])

c2 = bs.compiled('mysrc2.cpp', opts = bs.options(cflags = {'/EHsc'}))
e2 = bs.executable('myproj2', c2)
p2 = bs.project('myproj2', [e2])

l1 = bs.staticlib('mylib1', srcs = ['mylib1.cpp'])

l1u = bs.executable('mylib1use', srcs = ['mylib1use.cpp'], deps = [l1], opts = bs.options(cflags = {'/EHsc'}))

l2 = bs.sharedlib('mylib2', srcs = ['mylib2.cpp'])

l2u = bs.executable('mylib2use', srcs = ['mylib2use.cpp'], deps = [l2], opts = bs.options(cflags = {'/EHsc'}))

ps1 = bs.compiled('sub1/sub1.cpp')
ps1u = bs.executable('ps1u', srcs = ['ps1u.cpp'], deps = [ps1], opts = bs.options(incdirs = {'sub1'}))

s = bs.project('mysolution', deps = [p1, p2, l1, l1u, l2, l2u, ps1u])

# print('\n'.join([str(b) for b in tc.builders]))
if 'clean' in args.targets:
	print('clean:')
	tc.clean(s)
if 'build' in args.targets:
	print('build:')
	tc.build(s)

end_time = time.time()
print('Build time: ' + str(round(end_time - start_time, 6)) + 's')
