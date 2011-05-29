import gcc
import state
import util
from state import TaskNode, FileNode

class CompilerNode(TaskNode):

  def run_command(self, command):
    self.out, self.err, self.exit = util.run(command, display=True)
    self.message = self.out + self.err
    return self.exit == 0


class Compile(CompilerNode):
  def __init__(self, input_file, defs=[], includes=[]):
    super(Compile, self).__init__()
    self.input_file = input_file
    self.output_file = Compile.get_output_file(input_file)
    self.defs = defs
    self.includes = includes

  @staticmethod
  def get_output_file(filename):
    return filename + '.o'

  def run(self, dependencies):
    command = gcc.compile(input=self.input_file, target=self.output_file, defs=self.defs, includes=self.includes)
    return self.run_command(command)


class Link(CompilerNode):
  def __init__(self, target):
    super(Link, self).__init__()
    self.target = target

  def run(self, dependencies):
    # get the objects directly from the graph
    objs = [d.output_file for d in dependencies if hasattr(d, "output_file")]

    # get all the libs from the dependencies
    for d in dependencies:
      if hasattr(d, "libraries"):
        print "libs" + d.libraries
      else:
        print "NOLIBS"

    raise TODO
    libs = [d.libraries for d in dependencies if hasattr(d, "libraries")]
    print libs
    raise TODO

    command = gcc.link(target=self.target, objects=objs, libs=libs)
    return self.run_command(command)



def build(state, config_node, ginfile):
  for (target_name, struct) in ginfile["targets"].items():

    # The nodes for building a simple file look like this:
    #  proc_1 -> objfile_1
    #  ...
    #  proc_n -> objfile_n

    objs = []
    for f in struct['files']:
      c = Compile(input_file=f,
                  includes=struct["includes"] + ['.'],
                  defs={"HAVE_CONFIG_H": None},
                  )

      obj = FileNode(Compile.get_output_file(f))
      state.dg.add_edge(c, obj)
      state.dg.add_edge(config_node, c)
      objs += [obj]

    # The linker depends on all object files, and produces a target file
    linker = Link(target_name)
    for obj in objs:
      state.dg.add_edge(obj, linker)

    state.dg.add_edge(config_node, linker)
    state.dg.add_edge(linker, FileNode(target_name))

