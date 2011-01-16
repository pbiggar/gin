import util
import os
import fabric

def run(args, stdin=None):
  return fabric.run(args, stdin)

def check_run(args, stdin=None):
  exit = fabric.run(args, stdin)
  if exit != 0:
    raise Exception("Building failed: " + args)


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
  exit = run(['gcc', '-c', '-x', language.lower(), '-'], source)
  return exit == 0



def build_object(filename, includes, defs):
  obj = filename + '.o'
  compiler = get_compiler([filename])

  defs = ["-D%s=%s" % (k,v) for (k,v) in defs.items() if v != None] \
       + ["-D%s" % (k) for (k,v) in defs.items() if v == None]

  includes = ["-I" + i for i in includes]

  check_run([compiler, '-c', filename, '-o', obj] + includes + defs)

  return obj



def link(output_file, objects, libs):
  compiler = get_compiler(objects)

   # rpath -L/usr/lib -L/usr/local/lib -R/usr/local/lib -ldl

  libs = ["-l" + l for l in libs]

  check_run([compiler, '-o', output_file] + objects + libs)
