import gcc
import state
import util

class ObjectFile(state.BaseNode):
  def __init__(self, output_file):
    self.output_file = output_file

  def run(self, dependencies):
    pass


class CompilerNode(state.BaseNode):

  def run_command(self, command):
    self.out, self.err, exit = util.run(command, display=True)
    return exit == 0

  def result_string(self):
    return self.out + "\n" + self.err






class Compile(CompilerNode):
  def __init__(self, input_file, defs=[], includes=[]):
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
  def __init__(self, target, libs):
    self.target = target
    self.libs = libs

  def run(self, dependencies):
    # get the objects directly from the graph
    objs = [d.output_file for d in dependencies]
    command = gcc.link(target=self.target, objects=objs, libs=self.libs)
    return self.run_command(command)


class Executable(object):
  def __init__(self, output_file):
    self.output_file = output_file

  def run(self, dependencies):
    pass

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

      obj = ObjectFile(Compile.get_output_file(f))
      state.dg.add_edge(c, obj)
      state.dg.add_edge(config_node, c)
      objs += [obj]

    # The linker depends on all object files, and produces a target file
    linker = Link(target_name, libs=struct["libraries"])
    for obj in objs:
      state.dg.add_edge(obj, linker)

    state.dg.add_edge(linker, Executable(target_name))

