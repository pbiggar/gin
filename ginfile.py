import yaml
from collections import defaultdict


class _defaultdict(defaultdict):

  def __missing__(self, key):
    if key in schema:
      return schema[key]

    raise Exception("Schema has no default value for: " + key)

schema = {
  "configure": _defaultdict(),
  "targets": _defaultdict(),
  "includes": [],
  "libraries": [],
  "files": [],
}




class Ginfile(object):

  def __init__(self, filename):
    stream = file(filename, "r")
    contents = yaml.safe_load(stream)
    stream.close()

    self._struct = self._setdefaults(contents)

  def __getitem__(self, key):
    return self._struct[key]

  def _setdefaults(self, item):
    """Replace all dicts with defaultdicts"""

    if isinstance(item, dict):
      result = _defaultdict()
      for k,v in item.items():
        result[k] = self._setdefaults(v)

      return result

    return item


