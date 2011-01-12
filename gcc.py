import util
import os

def get_compiler(filenames):

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


def build_object(filename):
  output_file = filename + '.o'
  compiler = get_compiler([filename])


  print "compiling: " + filename + " into " + output_file + " with " + compiler
  util.check_run([compiler, '-c', filename, '-o', output_file])
  return output_file

def link(output_file, objects, libs):
  compiler = get_compiler(objects)
  print "linking " + str(objects) + " with " + str(libs) + " into " + output_file + " with " + compiler
  util.check_run([compiler, '-o', output_file] + objects + ["-l" + l for l in libs])

