import cPickle as pickle
import multiprocessing
import time
import util

class Data(object):
  def __init__(self, target, callback, arguments):
    self.target = target
    self.callback = callback
    self.arguments = arguments
    self.deps = None # means always build

def load():
  try:
    return pickle.load(file('.ginpickle', 'r'))
  except:
    return None


class State(object):
  def __init__(self):
    self._chain = {}
    self._reverse = {}

  def save(self):
    pickle.dump(self, file('.ginpickle', 'w'))


  def add(self, target, outputs, function, arguments):
    data = Data(target, function, arguments)
    self._chain[target] = data

        
  def process(self):
    pool = multiprocessing.Pool(3)
    timestamp = time.time()

    # TODO: md5
    # For targets where we don't know the deps, we must build
    results = []
    for data in self._chain.values():
      build = False
      if not data.deps:
        print "No deps available, building %s (%s)" % (data.target, data)
        build = True
      else:
        for d in data.deps:
          if util.timestamp(d) >= util.timestamp(data.target):
            build = True
            print "Dep outdated, building: " + data.target + d
            break

      if build:
        handle = pool.apply_async(data.callback, data.arguments)
        results += [(data, handle)]
      else:
        print "No need to build: " + data.target

    for data, handle in results:
      data.deps = handle.get()
      print "Adding deps to %s (%s): %s" % (data.target, str(data), str(data.deps))

