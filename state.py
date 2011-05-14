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

# All nodes are either tasknodes, or Filenodes. There should never be an edge
# between two filenodes.
class FileNode(object):

  def __init__(self, filename):
    self.filename = filename

  def timestamp(self):
    raise TODO

  def signature(self):
    raise TODO


class TaskNode(object):
  """Add graph traversal interface for DependencyGraph nodes"""

  def __init__(self):
    self.message = ""
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

    # Things we can't serialize
    self.handles = {}
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


  def call_remotely(self, node):
    return self.pool.apply_async(remote_proxy, (node, [self.dependencies(node)], {}))


  def start_build(self, node):

    handle = self.call_remotely(node)
    node.result = None
    self.handles[node] = handle

  def needs_rebuild(self, node):

    # If it's never been built before
    if node.result == None:
      return True

    if node.timestamp < max([p.timestamp for p in self.predecessors(node)]):
      # TODO: add md5sum
      return True

    return False
    

  def process(self):
    """Mark all nodes which need to be built. Rules:
      - only build if it's a dependency of a target we're building
      - if it has no dependency information, it must be built to get dependency information
      - it it has dependency information, build it if any of its dependencies have changed.
    """

    # TODO: read Mike Shia's paper here, and implement his algorithm.
    # For the time being, do it the O(N) way: start at the roots, and push
    # inwards. If we don't have to rebuild, keep pushing inwards, as some
    # successors will still have to.


    # We'll pretend this is true for now
    targets = self.dg.leaves()

    roots = util.flatten([self.dg.node_roots(t) for t in targets])


    # We use a queue for this. We add nodes that are ready to be built to the
    # queue. When they are built (or if they dont need to be built, we add
    # their successors iff their successor's predecessors are all built.
    queue = list(set(roots))

    # TODO: ugly!!!! Tidy this code up for the love of god!
    # When a handle is finished, check if the nodes that depends on it are
    # ready to go.
    while len(queue) > 0:
      finished = False
      node = queue.pop(0)
      if not isinstance(node, TaskNode):
        finished = True
      else:
        if node not in self.handles:
          if self.needs_rebuild(node):
            self.start_build(node)
          else:
            finished = True
        else:
          # check the build is finished
          h = self.handles[node]
          if h.ready():
            try:
              rval = h.get() # raises exception
            except:
              print "Remote exception"
              raise

            print rval["message"],
            node.result = rval
            del self.handles[node]
            finished = True


      if not finished:
        # We'll try it again later.
        queue.append(node)
      else:
        # push succeesors
        for s in self.dg.successors(node):
          succ_ready = True
          for pred in self.dependencies(s): # the predecessors of the successor we want to build
            if pred.result == None:
              succ_ready = False
              break
          if succ_ready:
            queue.insert(0, s)
          else:
            pass # aNOTHER PREDECESSOR WILL GET THIS


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



