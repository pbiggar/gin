import cPickle as pickle
import multiprocessing
import time
import util
import networkx as nx
import sys
import time

class Data(object):
  def __init__(self, target, callback, arguments, deps):
    self.target = target
    self.callback = callback
    self.arguments = arguments
    self.deps = deps

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



def call_remotely(data):
  return pool.apply_async(remote_proxy, (data.callback, data.arguments, {}, data.target), callback=local_callback)
  


def after_callback(args):
  # Pass exceptions back
  if isinstance(args, Exception):
    raise args

  # THe reason this doesn't work is that data is serialized, and you're adding
  # deps to the wrong object. You're looking for D, but getting D'' (prime prime)

  (state, data, deps) = args
  data.deps = deps
  state._add_data(data)

  print "Done: " + data.target + "(%s)" % str(data)


def load():
  try:
    return pickle.load(file('.ginpickle', 'r'))
  except:
    return None

# TODO: state get's pickled, so perhaps it's not the best thing to be holding all this.
# Need a wrapper which isnt pickled, or look up how to specify what gets pickled
handles = []
pool = None



class State(object):
  def __init__(self):
    self._graph = nx.DiGraph()
    self._all = {}

  def save(self):
    pickle.dump(self, file('.ginpickle', 'w'))

  def add(self, target, outputs, function, arguments, deps):
    data = Data(target, function, arguments, deps)
    self._add_data(data)


  def _add_data(self, data):
    self._all[data.target] = data

    if data.deps:
      self._add_to_graph(data)


  def _add_to_graph(self, data):
    assert data.deps != None
    for d in data.deps:
      self._graph.add_edge(d, data.target)


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
    pool = multiprocessing.Pool(2)
    handles = []

    # Get the deps we don't know
    for data in [d for d in self._all.values() if d.deps == None]:
      self.build(data)

    for (handle, data) in handles:
      while not handle.ready():
        print "waiting for " + data.target
        time.sleep(0.2)
      assert handle.successful()
      handle.wait()

    pool.close()
    pool.join()

    # TODO: must we wait for all our deps, or can we go ahead
    # with what we know
    for data in self._all.values():
      assert(data.deps)



    # We now have a full dependency-tree. Do a breadth-first search from the roots.
    for data in self.bfs():
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

