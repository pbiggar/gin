import networkx as nx
import pydot
import subprocess


class DependencyGraph(object):
  """An abstract and general graph representing dependencies. Properties of this graph:

       - it is directed
      
       - it is acyclic (technically the query interface below could be used to
         "break cycles" if we allowed them, but it sounds unuseful for now).
      
       - it has multiple roots and leaves
         (USE CASE: a build could produce multiple libraries which are leaves,
         and use multiple files which are roots).

       - edges represent dependencies. An edge E from a source S to a target T
         means that creating T requires creating S first.

       - Targets can query their dependencies for values. The values *must* be
         structured as string->T maps, where T is a simple type which can be
         easily serialized (preferably as JSON)
         (USE CASE: config.h needs to know the result of configure jobs).
         (USE CASE: we might allow plugins via a JSON interface)
       
       - Nodes can be wrapped by other nodes, which intercept values going in
         and coming out of their wrappees
         (USE CASE: gcc wrapped by distcc wrapped by ccache).

       - Nodes may have dynamic dependencies, which are unknown until the node
         is first processed.
         (USE CASE: gin magically handles all file dependencies)
         (USE CASE: changing a file's contents, perhaps a #include, will change
         its dependencies)
"""

  def __init__(self):
    self._G = nx.DiGraph()

  def add_edge(self, n1, n2):
    self._G.add_edge(n1, n2)

  def dump_graphviz(self):
    return # TODO: fix the add_node calls below
    dgraph = nx.to_pydot(self._G)
    for d in dgraph.get_node_list():
      print d.get_name()

    # Put the roots in the same subgraph so they can be put in the same rank in
    # the graphviz graph. This puts them at the top of the graph
    roots_graph = pydot.Subgraph(subgraph_name="roots")
    roots = [n for n,d in self._G.in_degree().items() if d == 0]
    for r in roots:
      print repr(r)
    [roots_graph.add_node(dgraph.get_node(str(repr(r)))) for r in roots]
    roots_graph.set_rank('source')
    dgraph.add_subgraph(roots_graph)

    # Same for the bottom of the graph
    leaves_graph = pydot.Subgraph(subgraph_name="leaves")
    leaves = [n for n,d in self._G.out_degree().items() if d == 0]
    [leaves_graph.add_node(dgraph.get_node(l)) for l in leaves]
    leaves_graph.set_rank('sink')
    dgraph.add_subgraph(leaves_graph)

    dgraph.write_ps("a.ps", prog="dot")

  # Note, all functions accept and return the types they are given, which can be any hashable type

  # Returns things: we return nodes and edges wrapped so that we can get useful
  # stuff from the node directly (even if that proxies it into the graph)

  def leaves(self):
    return [n for n in self._G.nodes() if self._G.out_degree(n) == 0]

  def roots(self):
    return [n for n in self._G.nodes() if self._G.in_degree(n) == 0]

  def dependencies(self, n):
    return self._G.predecessors(n)

  def successors(self, n):
    return self._G.successors(n)

