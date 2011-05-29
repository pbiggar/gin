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

  return (rval, obj.__dict__)


class BaseNode(object):
  """Base class for all nodes in the dependencyGraph."""





class State(object):
  def __init__(self, dg=None):
    self.dg = dg or DependencyGraph()
    self.needs_building = {}
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
    if not self.needs_building.get(data, False):
      return

    handle = self.call_remotely(data)
    self.handles[data] = handle


  def check_dependencies(self, target):
    """Recursively mark dependencies as needed"""
    self.needs_building[target] = True

    for d in self.dependencies(target):
      self.check_dependencies(d)


  def maybe_build(self, data):
    """Build if the dependencies are met"""
    if len([dep for dep in self.dependencies(data) if not getattr(dep, "success", False)]) == 0:
      self.start_build(data)
      return True

    return False



  def process(self):

    # Mark dependencies for the roots as needing building. We do this so that
    # we don't build roots that aren't needed for our targets.
    for t in self.targets():
      self.check_dependencies(t)

    # At this point, the depgraph nodes have needs_building set. Now we do a
    # breadth-first search, starting with the roots.
    for r in self.dg.roots():
      self.start_build(r)

    # When a handle is finished, check if the nodes that depends on it are
    # ready to go.
    try:
      failures = []
      while len(self.handles) > 0:
        for data, handle in self.handles.items():
          if handle.ready():
            try:
              (rval, remote_dict) = handle.get() # raises exception
            except:
              print "Remote exception"
              raise

            del self.handles[data]

            # Set the attributes from the remote object to the local object
            for k,v in remote_dict.items():
              setattr(data, k, v)

            data.success = rval

            # Report errors
            if not rval:
              print "Failed: " + str(data)
              failures.append(data)
            else:
              print "Success: " + str(data)

            # Try building successors
            for s in self.dg.successors(data):
              self.maybe_build(s)


    finally:
      self.pool.close()
      self.pool.join()

    print "Failures: " + str(failures)

    print ("And we're done");




  def targets(self):
    # Not all leaves are targets, but I'm not sure there's a good way to find
    # targets right now, so just go with leaves.
    """All the leaf targets in the system"""
    return self.dg.leaves()


  def __getattr__(self, name):
    if name in ['add_edge', 'dump_graphviz', 'dependencies']:
      return getattr(self.dg, name)

    raise
    # TODO: wrong error returned here



