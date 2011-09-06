import cPickle as pickle
import multiprocessing
import time
import util
import networkx as nx
import sys
import traceback
import time
import depgraph

########################################
# Multiprocessing interface
########################################

# Why does multiprocessing require such hacks

# We use a proxy to catch exceptions and return them to the parent
def remote_proxy(obj, args, kwargs):
  try:
    return obj.run_task(*args, **kwargs)
  except Exception, e:
    traceback.print_exc(e)
    raise e


class BaseNode(object):
  """Base class for all nodes in the dependencyGraph."""

class FileNode(object):
  def __init__(self, filename):
    self.filename = filename

  def timestamp(self):
    raise TODO

  def signature(self):
    raise TODO

  def run_task(self, *args, **kwargs):
    self.success = True
    return self.__dict__


class TaskNode(object):
  """Add graph traversal interface for DependencyGraph nodes"""

  def __init__(self):
    self.success = True
    self.result = None

  def run_task(self, *args, **kwargs):
    """Returns a dictionary of the fields added by the task. We return a dictionary since the actual task's data isn't sychronized back."""

    self.success = self.run(*args, **kwargs)
    return self.__dict__



class State(object):
  def __init__(self, dg=None):
    # Anything we want to serialize
    self.dg = dg or depgraph.DependencyGraph()
    self.needs_building = {}

    # Things we can't serialize
    self.handles = {}
  #  self.pool = multiprocessing.Pool(multiprocessing.cpu_count() + 1)
# make it deterministic for now
    self.pool = multiprocessing.Pool(1)


  @staticmethod
  def load():
    try:
      return State(pickle.load(file('.ginpickle', 'r')))
    except Exception as e:
      print e
      return None


  def save(self):
    pickle.dump(self.dg, file('.ginpickle', 'w'))


  def call_remotely(self, node):
    return self.pool.apply_async(remote_proxy, (node, [self.dependencies(node)], {}))


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

  def needs_rebuild(self, node):

    # If it's never been built before
    if node.result == None:
      return True

    if node.timestamp < max([p.timestamp for p in self.predecessors(node)]):
      # TODO: add md5sum
      raise


  def maybe_build(self, data):
    """Build if the dependencies are met"""
    if len([dep for dep in self.dependencies(data) if not getattr(dep, "success", False)]) == 0:
      self.start_build(data)
      return True

    return False
   

  def process(self):
    """Mark all nodes which need to be built. Rules:
      - only build if it's a dependency of a target we're building
      - if it has no dependency information, it must be built to get dependency information
      - it it has dependency information, build it if any of its dependencies have changed.
    """

    # Mark dependencies for the roots as needing building. We do this so that
    # we don't build roots that aren't needed for our targets.
    for t in self.targets():
      self.check_dependencies(t)

    # TODO: read Mike Shia's paper here, and implement his algorithm.
    # For the time being, do it the O(N) way: start at the roots, and push
    # inwards. If we don't have to rebuild, keep pushing inwards, as some
    # successors will still have to.

    # At this point, the depgraph nodes have needs_building set. Now we do a
    # breadth-first search, starting with the roots.
    for r in self.dg.roots():
      self.start_build(r)

    try:
      failures = []
      while len(self.handles) > 0:
        for data, handle in self.handles.items():
          if handle.ready():
            try:
              remote_dict = handle.get() # raises exception
            except:
              print "Remote exception - this is always an error in gin, please report it."
              print "\t(Of course, it may be triggered by a bug in your ginfile or extension, so you may be able to work around this)"
              raise

            del self.handles[data]

            # Set the attributes from the remote object to the local object
            for k,v in remote_dict.items():
              setattr(data, k, v)

            # We may have new dependencies, fix up the graph.
            self.update_dependencies(data)

            if not data.success:

              # Many targets won't build correctly on the first go because their dependencies are not built.
              # So now we need to build the dependencies.
              # TODO: compare the old data.deps with the new one
              if data.old_deps != data.deps:

                new_deps = data.deps - data.old_deps

                # Mark it as needing building
                for d in new_deps:
                  self.check_dependencies(d)

                # TODO: Up until this point, we created the depgraph during
                # ginfile parsing. Now we need to update the graph dynamically,
                # and we dont' want to restart this function. We need to do
                # this in a clean elegant non-hacky way, or else we'll be
                # dealing with subtle bugs forever

                deps = new_dependencies
                remove_old_deps
                add_new_deps
                roots = get_roots (data)
                for r in roots:
                  self.start_build(r)

                # when the new predecessors are built, this node will automatically be built again


              # Report errors
              print "Failed building: " + data.input_file
              print data.message
              raise Exception("Stop")
            else:
              if hasattr(data, "message"):
                print data.message

            # Try building successors
            for s in self.dg.successors(data):
              self.maybe_build(s)

      print "Built";

    except:
      self.pool.terminate()
      print "Build failed"
      raise
    finally:
      self.pool.close()
      self.pool.join()





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



