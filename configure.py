import sys
import pprint
import gcc
from state import FileNode, TaskNode



# The configure node factors the configure checks. The configure node is needed
# by the compile jobs for include files, by the link job for libs, and by
# config.h for #defines. Most compile jobs also need config.h, but we let them
# work that out for themselves.
#                
# c1 ---\        /--> config.h -\
# c2 -\  \      /  /--------> o1.obj-------\
# ... -> Configure ---------> o2.obj ----\  \
# cn -/            \-------------------------> prog
def configure(state, ginfile):
  checks = parse_configure_checks(state, ginfile)
  gen_config_h = add_config_dot_h(state, checks, ginfile)
  config = add_configure(state, checks, gen_config_h)
  return config


def parse_configure_checks(state, ginfile):
  # main section
  checks = ginfile["configure"]

  # subsection of targets
  for t in ginfile["targets"].values():
    checks.update (t["configure"])

  return [ConfigureCheck(name, **check) for name, check in checks.items()]


def add_configure(state, config, config_h):
  # TODO: we probably don't need a configure node. Suppose we have a rule that
  # depends on bison - we certainly need to check for bison before we run it,
  # but we don't need to wait for a gcc check. But having a configure node
  # holds that up.
  config = Configure()
  state.dg.add_edge(config_h, config)
  return config


def add_config_dot_h(state, checks, ginfile):
  gen_config_h = GenConfigDotH(ginfile)
  for c in checks:
    state.dg.add_edge(c, gen_config_h)
  config_h = FileNode("config.h")
  state.dg.add_edge(gen_config_h, config_h)
  return gen_config_h

  # Most compilations will require config.h to be ready before they can begin,
  # but we might not know that because the dependencies won't be ready until
  # after the first compilation. So here we make Configure depend on config.h
  # so that compilations won't start first.
  return config_h



class Configure(TaskNode):

  def run(self, dependencies):
    self.libraries = []
    for d in dependencies:
      if hasattr(d, "libraries"):
        self.libraries.extend(d.libraries)

    return True


class GenConfigDotH(TaskNode):

  def __init__(self, ginfile):
    super(GenConfigDotH, self).__init__()
    self.name = ginfile['meta']['name']
    self.version = ginfile['meta']['version']

  def _meta_information(self):
    return [
      '#define PACKAGE "%s"\n' % (self.name),
      '#define VERSION "%s"\n' % (self.version),
    ]

  def _standard_dirs(self):
    prefix = "/usr/local"
    datadir = prefix + "/share"
    libdir = prefix + "/lib"
    pkglibdir = prefix + "/" + self.name
    return [
      '#define DATADIR "%s"\n' % (datadir),
      '#define PKGLIBDIR "%s"\n' % (pkglibdir),
    ]

  def _write_config_file(self, meta_lines, dir_lines, define_lines):
    config = file("config.h", "w")

    for l in meta_lines + dir_lines + define_lines:
      config.write(l)
    config.close()


  def _define_lines(self, dependencies):
    defines = {}
    for d in dependencies:
      defines.update(d.defines)

    lines = []
    for define in defines:
      if type(define) == 'dict':
        lines.append ('#define %s "%s"\n' % (define.keys()[0], define.values()[0]))
      else:
        lines.append ('#define %s\n' % (define))
    lines.sort()

    return lines


  def run (self, dependencies):
    meta_lines = self._meta_information()
    dir_lines = self._standard_dirs()
    define_lines = self._define_lines(dependencies)
    self._write_config_file(meta_lines, dir_lines, define_lines)
    return True



class ConfigureCheck(TaskNode):
  def __init__(self, name, **kwargs):
    super(ConfigureCheck, self).__init__()
    self.name = name
    self.test_program = kwargs['test-program']
    self.language = kwargs['language']
    self.error_if_missing = kwargs.get('error-if-missing', None)
    self.warn_if_missing = kwargs.get('warn-if-missing', None)
    self.libraries = kwargs.get('libraries', [])
    self.type = kwargs.get('type', None)
    self.help = kwargs.get('help', None)
    self.defines = kwargs.get('defines', {})
    # TODO else block - ugly!

  def run(self, dependencies):
    success = gcc.configure_test(self.test_program, self.language)

    self.message = "Checking for " + self.name + '....'
    self.message += "yes" if success else "no"

    if not success:
      for val in [self.warn_if_missing, self.error_if_missing]:
        if val:
          self.message += "\n"
          self.message += val

    self.message += "\n"

    # We don't actually fail unless |error_if_missing| is set.
    return success or not self.error_if_missing

