import sys
import pprint
import gcc

def meta_information(ginfile):
  meta = ginfile["meta"]
  return [
    '#define PACKAGE "%s"\n' % (meta["name"]),
    '#define VERSION "%s"\n' % (meta["version"]),
  ]

def standard_dirs(ginfile):
  name = ginfile["meta"]["name"]

  prefix = "/usr/local"
  datadir = prefix + "/share"
  libdir = prefix + "/lib"
  pkglibdir = prefix + "/" + name
  return [
    '#define DATADIR "%s"\n' % (datadir),
    '#define PKGLIBDIR "%s"\n' % (pkglibdir),
  ]



def checks(ginfile):
  checks = ginfile["configure"]
  for t in ginfile["targets"].values():
    checks.update (t["configure"])

  # Store the name in the object for passing to Pool.map
  for name,check in checks.items():
    check["name"] = name
    state.add(FunctionNode(TODO, [], run_check, (check,)))

  libraries = []
  defines = []
  for check in checks.values():
    (ds, ls) = run_check(check)
    libraries += ls
    defines += ds

  libraries.sort()

  lines = []
  for define in defines:
    if type(define) == 'dict':
      lines.append ('#define %s "%s"\n' % (define.keys()[0], define.values()[0]))
    else:
      lines.append ('#define %s\n' % (define))
  lines.sort()

  return (libraries, lines)

def write_config_file(check_lines, meta_lines, dir_lines):
  config = file("config.h", "w")

  for l in meta_lines + dir_lines + check_lines:
    config.write(l)
  config.close()


def add_config_file(state, ginfile):
  meta_lines = meta_information(ginfile)
  dir_lines = standard_dirs(ginfile)
  state.add(Proc(write_config_file, (check_lines, meta_lines, dir_lines)))


def run_check(check):
  name = check["name"]
  print "Checking for " + name + '....',
  works = gcc.configure_test(check["test-program"], check["language"])
  print "yes" if works else "no"

  if works:
    defines = check.get("defines", [])
    libraries = check.get("libraries", [])
    return (defines, libraries)
  return ([], [])


  libraries = []
  defines = []
  for check in checks.values():
    (ds, ls) = run_check(check)
    libraries += ls
    defines += ds

  libraries.sort()

  lines = []
  for define in defines:
    if type(define) == 'dict':
      lines.append ('#define %s "%s"\n' % (define.keys()[0], define.values()[0]))
    else:
      lines.append ('#define %s\n' % (define))
  lines.sort()


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
  config = add_configure(state, checks)
  config_dot_h = add_config_dot_h(state, config, ginfile)
  return config


def parse_configure_checks(state, ginfile):
  # main section
  checks = ginfile["configure"]

  # subsection of targets
  for t in ginfile["targets"].values():
    checks.update (t["configure"])

  return [ConfigureCheck(name, **check) for name, check in checks.items()]


def add_configure(state, checks):
  config = Configure()
  for c in checks:
    state.dg.add_edge(c, config)
  return config


def add_config_dot_h(state, config, ginfile):
  config_h = ConfigDotH()
  state.dg.add_edge(config, config_h)



class Configure(object):
  def __init__(self):
    self.name = "configure"

  def process(self, dependencies):
    print dependencies
    raise TODO

class ConfigDotH(object):
  pass

class ConfigureCheck(object):
  def __init__(self, name, **kwargs):
    self.name = name
    self._settings = kwargs

  def process(self, dependencies):
    success = gcc.configure_test(self._settings["test-program"], self._settings["language"])

    if not success and "error-if-missing" in self._settings:
      return False

    return True


  def result_string(self):
    result = "Checking for " + self.name + '....'
    result += "yes" if self.success else "no"

    if not self.success:
      for key in ["warn-if-missing", "error-if-missing"]:
        if key in self._settings:
          result += self._settings[key]

    return result



  def __str__(self):
    return "ConfigureCheck: " + self.name
