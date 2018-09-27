import buildsystem.buildsystem as bs
import buildsystem.vc14_x64 as vc2015

bs.verbose = True
bs.toolchain = vc2015.toolchain()

e1 = bs.executable('myproj', srcs = ['mysrc1.cpp'])
p1 = bs.project('myproj', [e1])

c2 = bs.compiled('mysrc2.cpp', cflags = ['/EHsc'])
e2 = bs.executable('myproj2', c2)
p2 = bs.project('myproj2', [e2])

l1 = bs.staticlib('mylib1', srcs = ['mylib1.cpp'])

l1u = bs.executable('mylib1use', srcs = ['mylib1use.cpp'], deps = [l1], cflags = ['/EHsc'])

l2 = bs.sharedlib('mylib2', srcs = ['mylib2.cpp'])

l2u = bs.executable('mylib2use', srcs = ['mylib2use.cpp'], deps = [l2], cflags = ['/EHsc'])

s = bs.solution('mysolution', deps = [p1, p2, l1, l1u, l2, l2u])

s.build()