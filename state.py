import cPickle as pickle

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

  def get_next_target(self):
    # Find a target which hasn't ever been built
    for d in self._chain.values():
      if d.deps == None:
        return d

    assert (0)

        
  def process(self):
    while len(self._chain):
      # TODO: this is where caching, timestamps, etc, go
      data = self.get_next_target()
      data.deps = data.callback(*data.arguments)


