import os
import sys

import util


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


def compile(input, target, includes=None, defs=None):
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

def dependencies(input, includes, defs):
  compiler = get_compiler([input])

  defs = ["-D%s=%s" % (k,v) for (k,v) in defs.items() if v != None] \
       + ["-D%s" % (k) for (k,v) in defs.items() if v == None]

  includes = ["-I" + i for i in includes]

  makefile_script = [compiler, '-c', input, '-M', '-MG'] + includes + defs
  (out, err, exit) = util.run(makefile_script)
  deps = parse_makefile_dependencies(out)
  return deps

def parse_makefile_dependencies(string):
  """Parse a makefile dependency, of the form produced by gcc:
      Nativei386.o: nanojit/Nativei386.cpp nanojit/nanojit.h nanojit/avmplus.h \
        nanojit/VMPI.h /usr/include/assert.h /usr/include/sys/cdefs.h \
        /usr/include/stdlib.h /usr/include/Availability.h
  """

  results = []

  first = True
  for line in string.split():

    # On the first line, the target is preceeded by a colon - strip both
    if first:
      colon_index = line.find(":")
      line = line[colon_index:]
      first = False

    # strip the end of lines
    if line.endswith(" \\"):
      line = line[:-2]

    # Filenames can have spaces in them, which sorta screws us here. But this
    # is a temporary hack til I get the latest version of tup, so it's fine for
    # now.
    results += line.split(" ")

  return results


