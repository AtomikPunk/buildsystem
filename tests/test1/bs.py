import argparse

import buildsystem.buildsystem as bs
import buildsystem.toolchain as tc
import buildsystem.vc14_x64 as vc14_x64
import time

argparser = argparse.ArgumentParser(description = 'buildsystem build script')
argparser.add_argument('-t', '--tasks', help = 'comma separated list of tasks , eg: clean,build', default = 'clean,build')
argparser.add_argument('-c', '--colors', action = 'store_true', help = 'colored output')
argparser.add_argument('-v', '--verbose', action = 'store_true', help = 'verbose output')
argparser.add_argument('-f', '--file', help = 'path to spec file', default = 'build.bs')
argparser.add_argument('-o', '--outdir', help = 'path to output (build) directory', default = '.bs')
args = argparser.parse_args()

start_time = time.time()

spec = bs.readspec(bs.readspecargs(file = args.file))
if spec is not None:
	vc = vc14_x64.toolchain(cfg = tc.config(outdir = args.outdir))
	bs.execspec(bs.execspecargs(spec, args.tasks, vc, verbose = args.verbose, enablecolors = args.colors))

end_time = time.time()
print('Execution time: ' + str(round(end_time - start_time, 6)) + 's')
