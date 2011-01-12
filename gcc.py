import util

def build_object(filename):
  output_file = filename + '.o'

  print "compiling: " + filename + " into " + output_file
  util.check_run(['gcc', '-c', filename, '-o', output_file])
  return output_file

def link(output_file, objects):
  print "linking " + str(objects) + " into " + output_file
  util.check_run(['gcc', '-o', output_file] + objects)

