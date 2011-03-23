import cPickle as pickle
import multiprocessing
import time
import util
import networkx as nx
import sys
import traceback
import time
from depgraph import DependencyGraph

########################################
# Multiprocessing interface
########################################

# Why does multiprocessing require such hacks

# We use a proxy to catch exceptions and return them to the parent
def remote_proxy(obj, args, kwargs):
  try:
    rval = obj.run(*args, **kwargs)
  except Exception, e:
    traceback.print_exc(e)
    raise e


class BaseNode(object):
  """Base class for all nodes in the dependencyGraph."""
 
  def run(self, *args, **kwargs):
    self.process(*args, **kwargs)
    print self.result_string()

  def result_string(self):
    return ""







class State(object):
  def __init__(self, dg=None):
    self.dg = dg or DependencyGraph()
    self.needs_rebuilding = {}
    self.handles = {}
    self.results = {}
    self.already_built = set()
    self.pool = multiprocessing.Pool(multiprocessing.cpu_count() + 1)



  @staticmethod
  def load():
    try:
      return State(pickle.load(file('.ginpickle', 'r')))
    except Exception as e:
      print e
      return None


  def save(self):
    pickle.dump(self.dg, file('.ginpickle', 'w'))


  def call_remotely(self, data):
    deps = self.dependencies(data)
    return self.pool.apply_async(remote_proxy, (data, [deps], {}))


  def start_build(self, data):
    if data in self.already_built:
      return

#    print "building: " + str(data)

    self.already_built.add(data)

    handle = self.call_remotely(data)
    self.handles[data] = handle


  def check_dependencies(self, target):
    if target not in self.needs_rebuilding:
      self.needs_rebuilding[target] = True

    for d in self.dependencies(target):
      self.needs_rebuilding[target] |= self.check_dependencies(d)

    return self.needs_rebuilding[target]




  def process(self):

    for t in self.targets():
      self.check_dependencies(t)

    # TODO: check the needs_rebuilding flag first

    # At this point, the depgraph nodes have needs_rebuilding set. Now we do a
    # breadth-first search, starting with the roots.
    for r in self.dg.roots():
      self.start_build(r)

    # When a handle is finished, check if the nodes that depends on it are
    # ready to go.
    while len(self.handles) > 0:
      for d, h in self.handles.items():
        if h.ready():
          try:
            rval = h.get() # raises exception
          except:
            print "Remote exception"
            sys.exit(1)

          self.results[d] = rval

          del self.handles[d]

          for s in self.dg.successors(d):
            if len([p for p in self.dependencies(s) if p not in self.results]) == 0:
              self.start_build(s)

    self.pool.close()
    self.pool.join()


    print ("And we're done");




  def targets(self):
    # Not all leaves are targets, but I'm not sure there's a good way to find
    # targets right now, so just go with leaves.
    """All the leaf targets in the system"""
    return self.dg.leaves()


  def __getattr__(self, name):
    if name in ['add_edge', 'dump_graphviz', 'dependencies']:
      return getattr(self.dg, name)

    # TODO: wrong error returned here



