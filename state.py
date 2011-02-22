import cPickle as pickle
import multiprocessing
import time
import util
import networkx as nx
import sys
import time

class Node(object):
  def __init__(self, targets, deps):
    self.target = targets
    self.deps = deps

    for t in targets:
      assert isinstance(t, Node)

    if deps:
      for d in deps:
        assert isinstance(d, Node)

class FileNode(Node):
  """A node representing files"""
  def __init__(self, filename):
    # There are no targets because we don't have a node to represent them
    super(FileNode, self).__init__([], [])
    self.filename = filename

class FunctionNode(Node):
  """A node which calls a function to generate the target from its dependencies. |deps| can be None, in which case |function| updates it after it's called."""
  def __init__(self, targets, deps, function, args):
    super(FunctionNode, self).__init__(targets, deps)
    self.function = function
    self.args = args


class FactoringNode(Node):
  """A node to factor edges.
"Factor" is used in this context when discussing use-def graphs. Basically, We might have N targets which are all dependent on the same M nodes. Rather than adding M*N edges, you "factor" them by adding a FactoringNode, which sits between the edges, so you only have M+N+1 nodes."""
  pass

########################################
# Multiprocessing interface
########################################

# Why does multiprocessing require such hacks
state = None

# We use a proxy to catch exceptions and return them to the parent
def remote_proxy(function, args, kwargs, key):
  try:
    return (function(*args, **kwargs), key)
  except Exception as e:
    return e


def local_callback(rval):

  if isinstance(rval, Exception):
    raise rval 

  (deps, target) = rval
  data = state._all[target]
  data.deps = deps
  state._add_data(data)


def call_remotely(data):
  return pool.apply_async(remote_proxy, (data.callback, data.arguments, {}, data.target), callback=local_callback)
  

########################################
# Pickling
########################################
# TODO: state get's pickled, so perhaps it's not the best thing to be holding all this.
# Need a wrapper which isnt pickled, or look up how to specify what gets pickled
handles = []
pool = None



class State(object):
  def __init__(self):
    self._G = nx.DiGraph()
    self._all = {}

  @staticmethod
  def load():
    try:
      return pickle.load(file('.ginpickle', 'r'))
    except Exception as e:
      print e
      return None

  def save(self):
    pickle.dump(self, file('.ginpickle', 'w'))


  def add(self, node):
    if node in self._all:
      # TODO: need to do hashing and equality
      assert node == self._all[node]
      return

    data = Data(target, function, arguments, deps)
    self._add_data(data)


  def _add_data(self, data):
    # It's OK to add it multiple times
    if data.target in self._all:
      assert data == self._all[data.target]

    self._all[data.target] = data

    if data.deps:
      self._add_to_G(data)


  def _add_to_G(self, data):
    assert data.deps
    for d in data.deps:
      self._G.add_edge(d, data.target)

# TODO: not in my version of networkx
#    assert len(nx.algorithms.cycles.simple_cycles(self._G)) == 0


  def needs_building(self, data):
    for d in data.deps:
      if util.timestamp(d) >= util.timestamp(data.target):
        return True

    return False


  def build(self, data):
    global handles
    handle = call_remotely(data)
    handles += [(handle, data)]



  def process(self):
    global pool, handles, state
    state = self # HACK: this is getting irritating
    pool = multiprocessing.Pool(multiprocessing.cpu_count() + 1)
    handles = []

    # Get the deps we don't know
    for data in [d for d in self._all.values() if d.deps == None]:
      self.build(data)

    # TODO: we shouldn't need to wait for this to continue, but it simplifies
    # it for now.
    pool.close()
    pool.join()

    for data in self._all.values():
      assert(data.deps)


    # We now have a full dependency-tree. Do a breadth-first search from the roots.
    roots = [n for n,d in self._G.in_degree().items() if d == 0]
    print roots
    sys.exit(0)
    for data in nx.algorithms.traversal.breadth_first_search.bfs_edges(self._G):
                
      print data.target
      sys.exit(0)
      if self.needs_building(data):
        self.build(data)

      if build:
        handle = pool.apply_async(data.callback, data.arguments)
        results += [(data, handle)]
      else:
        print "No need to build: " + data.target

    for data, handle in results:
      data.deps = handle.get()
      #print "Adding deps to %s (%s): %s" % (data.target, str(data), str(data.deps))

