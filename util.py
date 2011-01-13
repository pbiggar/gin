import os
import subprocess
import threading
import sys

def find_all_files():
  sources = []
  for (dirpath, dirnames, filenames) in os.walk('.'):
    sources += [Filename(dirpath, f) for f in filenames]

  return sources



class Filename(object):
  def __init__ (self, dirpath, filename=None):
    if filename == None:
      # it's not a dirpath, but the full string
      self._str = dirpath
    else:
      self._str = os.path.join(dirpath, filename)

  def suffix(self):
    try:
      return os.path.basename(self._str).split('.')[-1]
    except IndexError:
      return ''

  def __str__(self):
    return self._str

  def __repr__(self):
    return self._str

  def __add__(self, other):
    return self._str + other





def find_filetypes(types):
  sources = []
  for file in find_all_files():
    for type in types:
      if file.endswith("." + type):
        sources.append(os.path.join(dirpath, file))
        break

  return sources


def run(args, stdin=None):
  class ThreadWorker(threading.Thread):
    def __init__(self, pipe):
      super(ThreadWorker, self).__init__()
      self.all = ""
      self.pipe = pipe
      self.setDaemon(True)

    def run(self):
      while True:
        line = self.pipe.readline()
        if line == '': break
        else:
          self.all += line

  try:
    args = [str(a) for a in args] # convert to strs
    print subprocess.list2cmdline(args)

    stdin_pipe = subprocess.PIPE if stdin else None
    proc = subprocess.Popen(args, stdin=stdin_pipe, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if stdin_pipe:
      proc.stdin.write(stdin)
      proc.stdin.close()

    stdout_worker = ThreadWorker(proc.stdout)
    stderr_worker = ThreadWorker(proc.stderr)
    stdout_worker.start()
    stderr_worker.start()

    proc.wait()
    stdout_worker.join()
    stderr_worker.join()

  except KeyboardInterrupt, e:
    pass

  stdout, stderr = stdout_worker.all, stderr_worker.all
  result = (stdout, stderr, proc.returncode)
  return result

def check_run(args, stdin=None):
  out, err, exit = run(args, stdin)
  if exit != 0:
    raise Exception(err)

