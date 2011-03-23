import util
import os


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
  _, _, exit = util.run(['ccache', 'gcc', '-c', '-x', language.lower(), '-'], stdin=source, display=False)
  return exit == 0


def compile(input=None, target=None, includes=None, defs=None):
  compiler = get_compiler([input])

  defs = ["-D%s=%s" % (k,v) for (k,v) in defs.items() if v != None] \
       + ["-D%s" % (k) for (k,v) in defs.items() if v == None]

  includes = ["-I" + i for i in includes]

  return ['ccache', compiler, '-c', input, '-o', target] + includes + defs


def link(target, objects, libs):
  compiler = get_compiler(objects)

   # rpath -L/usr/lib -L/usr/local/lib -R/usr/local/lib -ldl

  libs = ["-l" + l for l in libs]

  return ['ccache', compiler, '-o', target] + objects + libs
