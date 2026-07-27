from PenguinPackage.package import Package

#PIL_Loaded = False
PYVIS_LOADED = False

try:
    from pyvis.network import Network
    import networkx as nx
    PYVIS_LOADED = True
except ModuleNotFoundError:
    PYVIS_LOADED = False


from graphistry.layout.sugiyama import SugiyamaLayout
from graphistry.layout.graph import Graph, Vertex, Edge
import pandas as pd
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt

from PenguinPackage.apt_packages import get_all_packages
from arch_official_packages import get_official_arch_packages, download_arch_package
from PenguinPackage.package import PackageList





#https://pygraphistry.readthedocs.io/en/latest/demos/more_examples/graphistry_features/layout_tree.html
def from_networkx(nxg):
    """
        Converts a networkx graph to a sugiyama graph.
    """
    vertices = []
    data_to_v = {}
    for x in nxg.nodes():
        vertex = Vertex(x)
        vertices.append(vertex)
        data_to_v[x] = vertex
    E = [Edge(data_to_v[xy[0]], data_to_v[xy[1]], data = xy) for xy in nxg.edges()]
    g = Graph(vertices, E)
    return g

def to_networkx(g):
    """
        Converts a sugiyama graph to a networkx graph.
    """
    from networkx import MultiDiGraph

    nxg = MultiDiGraph()
    for v in g.vertices():
        nxg.add_node(v.data)
    for e in g.edges():
        # todo: this leads to issues when the data is more than an id
        nxg.add_edge(e.v[0].data, e.v[1].data)
    return nxg


def draw_graph(target_package: Package, all_packages: list[Package]):
    if not PYVIS_LOADED:
        raise "You must install pyvis and networkx to use draw_graph"

    #TODO check there aren't multiple packages with same name


    #net = Network(directed=True)
    net = nx.DiGraph()


    packages_in_graph = collect_packages(target_package, all_packages, [])

    packages_and_ids = list(zip(packages_in_graph, range(len(packages_in_graph))))
    packages_and_ids_dict = dict(packages_and_ids)

    for package, id in packages_and_ids:
        net.add_node(id, label=package.name)

    for package, id in packages_and_ids:
        for dependency in package.dependencies:
             matching_packages = [p for p in all_packages if p.name == dependency.name]
             if len(matching_packages) == 1:
                 dependency_id = packages_and_ids_dict[matching_packages[0]]
                 net.add_edge(id, dependency_id)                

                #net.add_edges_from


    is_dag = nx.is_directed_acyclic_graph(net)
    print(f"Is DAG: {is_dag}")

    cycles = list(nx.simple_cycles(net))
    print(cycles)

    ids_to_nodes = {v: k for k, v in packages_and_ids_dict.items()}

    for cycle in cycles:
        print("Found cycle with packages:")
        for node_id in cycle:
            print(f"Package: {ids_to_nodes[node_id].name}")
        print()


    #libc6
    net.remove_edges_from(nx.selfloop_edges(net))

    
    gg = from_networkx(net)


    labels = {}
    for package, id in packages_and_ids:
        labels[id] = package.name


    layout_direction = 0
    root = None

    positions = SugiyamaLayout.arrange(gg, layout_direction = layout_direction, root=root)
    #nx.draw(net, pos = positions, with_labels = True, verticalalignment = 'bottom', arrowsize = 3, horizontalalignment = "left", font_size = 20)
    
    position1 = positions[0]
    
    #Find nodes with the same y position. Then sort them. Then add space to them based on the text length labels

    unique_y_positions = set([xy[1] for xy in positions.values()])

    print(unique_y_positions)

    nodes_at_y_values = {}
    for y_value in unique_y_positions:
        nodes_at_y_values[y_value] = []

    for id, position in positions.items():
        nodes_at_y_values[position[1]].append((id, position))


    new_positions = {}

    for y_value in unique_y_positions:
        
        #Sort by the x position
        nodes_at_y_values[y_value].sort(key=lambda x: x[1][0]) 

        additional_x_offset = 0
        for node in nodes_at_y_values[y_value]:
            #node[1][0] += additional_x_offset
            node_label = labels[node[0]]

            additional_x_offset += len(node_label) * 2
            new_positions[node[0]] = (node[1][0] + additional_x_offset, y_value)


    #plt.figure(figsize=(10, 8))
    plt.figure(figsize=(20, 8))


    nx.draw(net, pos = positions, labels=labels, verticalalignment = 'bottom',
             arrowsize = 3, horizontalalignment = "left", font_size = 14, font_color="black", node_color="gray", 
             edge_color="gray", font_weight='bold')


    plt.savefig("test.png")
    #plt.show()



    #nt = Network(directed=True)

    #Types of layouts: https://stackoverflow.com/questions/73490589/change-graph-layout-aka-node-positioning-algorithm-in-pyvis
    #nt.force_atlas_2based()
    #nt.repulsion()
    #nt.barnes_hut()
    #nt.barnes_hut()

    #nt.from_nx(net)

    #nt.save_graph("Test_graph.html")


def collect_packages(target_package: Package, all_packages: list[Package], collected_packages: list[Package]) -> list[Package]:

    collected_packages.append(target_package)

    for dep in target_package.dependencies:
        #TODO check if there are duplicates?

        matching_packages = [p for p in all_packages if p.name == dep.name]

        if len(matching_packages) is not 1:
            print(f"Invalid number of matching packages for dependency: {dep.name}")
            continue

        package = matching_packages[0]

        if package not in collected_packages:
            collect_packages(package, all_packages, collected_packages)

    return collected_packages


def draw_graph_from_name_arch(target_package_name):
    all_arch = get_official_arch_packages()
    package_list = PackageList(all_arch)
    target_package = package_list.get_package(target_package_name)
    draw_graph(target_package, all_arch)



def draw_graph_from_name_debian():
    pass
