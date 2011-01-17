"""A bridge for fabricate.py, so we can keep it at (or atleast pretty close to) the vendor version."""

import fabricate

try:
  builder = fabricate.Builder("smart_runner", ignore='\.ccache')
  runner = builder.runner
  runner.keep_temps = False
  runner.silent = False
except fabricate.RunnerUnsupportedException, e:
  runner = None

def run(args, stdin):
  """Return files dependencies of the argument"""
  return builder.memoize(args, input=stdin)


