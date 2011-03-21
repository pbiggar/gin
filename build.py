import gcc

class ObjectFile(object):
  def __init__(self, output_file):
    self.output_file = output_file

class Compile(object):
  def __init__(self, input_file, defs=[], includes=[]):
    self.input_file = input_file
    self.output_file = Compile.get_output_file(input_file)

  @staticmethod
  def get_output_file(filename):
    return filename + '.o'

  def run(self, dependencies):
    # We don't need to query anything from the dependencies
    return gcc.compile(target=self.output_file, defs=self.defs, includes=self.includes)

class Link(object):
  def __init__(self, target, libs):
    self.target = target
    self.libs = libs

  def run(self, dependencies):
    # get the objects directly from the graph
    gcc.link(target=self.target, objects=[d.filename for d in dependencies], libs=self.libs)


class Executable(object):
  def __init__(self, output_file):
    self.output_file = output_file

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

