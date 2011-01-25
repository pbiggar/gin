import util
import os

def run(args, stdin=None):
  out, err, exit = util.run(args, stdin)
  return exit

def check_run(args, stdin=None):
  out, err, exit = util.run(args, stdin)
  if exit != 0:
    print out
    print err
    raise Exception("Building failed: " + str(args))

def get_output_file(filename):
  return filename + '.o'

def get_deps_file(filename):
  return filename + '.deps'


def get_compiler(filenames):
  """Return 'gcc' unless there are C++ files, in which case return 'g++'"""

  any_cxx = False
  suffixes = set()
  for f in filenames:
    prefix, suffix = os.path.splitext(f)
    if suffix == '.o':
      prefix, suffix = os.path.splitext(prefix)

    suffixes.add(suffix[1:])

  if 'cpp' in suffixes:
    return 'g++'
  else:
    return 'gcc'

def configure_test(source, language):
  exit = run(['ccache', 'gcc', '-c', '-x', language.lower(), '-'], source)
  return exit == 0


def read_deps_file(string):
  lines = string.split()

  lines = [l for l in lines if l != '\\' and l[-1:] != ':']

  return lines


def build_object(filename, includes, defs):
  obj = get_output_file (filename)
  deps_file = get_deps_file (filename)
  compiler = get_compiler([filename])

  defs = ["-D%s=%s" % (k,v) for (k,v) in defs.items() if v != None] \
       + ["-D%s" % (k) for (k,v) in defs.items() if v == None]

  includes = ["-I" + i for i in includes]

  check_run(['ccache', compiler, '-c', filename, '-o', obj, '-MT', obj, '-MD', '-MP', '-MF', deps_file] + includes + defs)

  deps = file(deps_file).read()
  deps = read_deps_file(deps)

  return deps



def link(output_file, objects, libs):
  compiler = get_compiler(objects)

   # rpath -L/usr/lib -L/usr/local/lib -R/usr/local/lib -ldl

  libs = ["-l" + l for l in libs]

  check_run(['ccache', compiler, '-o', output_file] + objects + libs)
