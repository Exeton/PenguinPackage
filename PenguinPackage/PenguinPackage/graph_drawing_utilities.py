from PenguinPackage.package import Package

#PIL_Loaded = False
PYVIS_LOADED = False
GRAPHVIZ_LOADED = False

try:
    from pyvis.network import Network
    import networkx as nx
    PYVIS_LOADED = True
except ModuleNotFoundError:
    PYVIS_LOADED = False


try:
    import graphviz
    GRAPHVIZ_LOADED = True
except ModuleNotFoundError:
    GRAPHVIZ_LOADED = False


from graphistry.layout.sugiyama import SugiyamaLayout
from graphistry.layout.graph import Graph, Vertex, Edge
import pandas as pd
import networkx as nx
import matplotlib
import matplotlib.pyplot as plt



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


    package_dict = {package.name: package for package in all_packages}

    packages_in_graph = collect_packages(target_package, all_packages)

    packages_and_ids = list(zip(packages_in_graph, range(len(packages_in_graph))))
    packages_and_ids_dict = dict(packages_and_ids)

    for package, id in packages_and_ids:
        net.add_node(id, label=package.name)

    for package, id in packages_and_ids:
        for dependency in package.dependencies:
             
             if dependency.name in package_dict:
                 matching_package = package_dict[dependency.name]
                 dependency_id = packages_and_ids_dict[matching_package]
                 net.add_edge(id, dependency_id)  
             #matching_packages = [p for p in all_packages if p.name == dependency.name]
             #if len(matching_packages) == 1:
             #    dependency_id = packages_and_ids_dict[matching_packages[0]]
             #    net.add_edge(id, dependency_id)                

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


def draw_graph_graphviz(target_package: Package, all_packages: list[Package], output_name=None):
    if not GRAPHVIZ_LOADED:
        raise "You must install graphviz to use draw_graph_graphviz"

    dot = graphviz.Digraph("Dependency Graph")



    package_dict = {package.name: package for package in all_packages}
    packages_in_graph = collect_packages(target_package, all_packages)
    packages_and_ids = list(zip(packages_in_graph, range(len(packages_in_graph))))
    packages_and_ids_dict = dict(packages_and_ids)

    for package, id in packages_and_ids:
        dot.node(str(id), label=package.name)

    for package, id in packages_and_ids:
        for dependency in package.dependencies:
             
             if dependency.name in package_dict:
                 matching_package = package_dict[dependency.name]
                 dependency_id = packages_and_ids_dict[matching_package]
                 dot.edge(str(id), str(dependency_id))  


    final_name = output_name
    if final_name == None:
        final_name = f"{package.name}.gv"


    dot.render(final_name, view=True)



def collect_packages(target_package: Package, all_packages: list[Package]) -> list[Package]:
    
    #Duplicate package names will be dropped
    package_dict = {package.name: package for package in all_packages}
    return _collect_packages(target_package, package_dict, [])

def _collect_packages(target_package: Package, package_dict: dict[str, Package], collected_packages: list[Package]) -> list[Package]:

    collected_packages.append(target_package)

    for dep in target_package.dependencies:
        #TODO check if there are duplicates?

        if dep.name not in package_dict:
            print(f"No matching packages for dependency: {dep.name}")
            continue

        package = package_dict[dep.name]

        if package not in collected_packages:
            _collect_packages(package, package_dict, collected_packages)

    return collected_packages



from PenguinPackage.apt_packages import get_all_packages

path_to_indexes = "/path/to/indexes"
all_packages = get_all_packages(
    path_to_indexes
)
print(len(all_packages))

python_canidates = [
    package for package in all_packages if "libpython3-all-dbg" in package.name
]

#python_canidates = [
#    package for package in all_packages if "steam-installer" in package.name
#]

#draw_graph(python_canidates[0], all_packages)


#from aur_packages import extract_packages_from_metadata
#from arch_official_packages import get_official_arch_packages



#aur_packages = extract_packages_from_metadata()
#official_packages = get_official_arch_packages()

#arch_all_packages = aur_packages + official_packages


 

#canidates = [
#    package for package in arch_all_packages if "ffmpeg" == package.name.lower() 
#]

#print(len(canidates))

#draw_graph_graphviz(canidates[0], arch_all_packages)

#python_canidates = [
#    package for package in all_packages if "ffmpeg" == package.name
#]

#river = [package for package in arch_all_packages if package.name == "river"][0]
#draw_graph_graphviz(river, arch_all_packages)

#draw_graph_graphviz(python_canidates[0], all_packages)