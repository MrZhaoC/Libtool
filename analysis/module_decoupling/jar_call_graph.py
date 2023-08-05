import os

import networkx as nx
from androguard.misc import AnalyzeDex
from matplotlib import pyplot as plt
from networkx import DiGraph

from analysis.core_feature_analysis.android_r8.aaaaa import deal_graph
from analysis.core_feature_analysis.android_r8.tttttt import cluster_analysis
from tools import tools

DOT_DEX = '.dex'

dex_file_path = r"D:\Android-exp\exp-example\faketraveler\libraries\dex\androidx.core@core@1.1.0.dex"
_, dex_d, dex_dx = AnalyzeDex(dex_file_path)

all_methods = []


def get_method_classes(dx):
    method_graph = nx.DiGraph()
    for me in dx.get_methods():
        method_full_name = me.full_name.replace('$', '')
        if method_full_name not in all_methods:
            continue

        # from
        for _, callee_from, _ in me.get_xref_from():
            callee_from_full_name = callee_from.full_name.replace('$', '')
            if callee_from_full_name not in all_methods:
                continue
            if method_full_name != callee_from_full_name and not method_graph.has_edge(method_full_name,
                                                                                       callee_from_full_name):
                method_graph.add_edge(callee_from_full_name, method_full_name, weight=1)

        # to
        for _, callee_to, _ in me.get_xref_to():
            callee_to_full_name = callee_to.full_name.replace('$', '')
            if callee_to_full_name not in all_methods:
                continue
            if method_full_name != callee_to_full_name and not method_graph.has_edge(method_full_name,
                                                                                     callee_to_full_name):
                method_graph.add_edge(method_full_name, callee_to_full_name, weight=1)

    # nx.draw_networkx(method_graph)
    # plt.show()
    dependency_graph = nx.to_undirected(method_graph)
    print('图中连通分量的个数为：', nx.number_connected_components(dependency_graph))  # 输出图中连通图的数量，也就是候选实例的个数
    # nx.write_gexf(method_graph, "method_call_graph.gexf")

    return method_graph


def analysis_dex_method_entry(dependencies_dex_path, t_dvm, t_dx, target_dex_file, b_keep_rule_path):
    method_graph = get_method_classes(t_dx)

    dex_files = tools.list_all_files(dependencies_dex_path)

    target_method_full_name_list = []

    # 得到目标dex的所有方法名(全限定类名+方法信息)集合
    for m in t_dvm.get_methods():
        target_method_full_name_list.append(m.full_name)

    for file in dex_files:
        file_name = file.split('\\')[-1]
        if file_name == target_dex_file:
            continue
        # 获取文件后缀
        file_ext = os.path.splitext(file)[-1]
        if file_ext == DOT_DEX:
            method_entry_list = []
            _, fd_dvm, fd_dx = AnalyzeDex(file)
            for class_x in fd_dx.get_classes():
                for method_x in class_x.get_methods():
                    if method_x.full_name in target_method_full_name_list:
                        method_entry_list.append(method_x.full_name.replace('$', ''))

            for method_fn in method_entry_list:
                if method_graph.has_node(method_fn):
                    increase_edge_weights_from_node(method_graph, method_fn)

    # cluster_analysis(method_graph)
    deal_graph(method_graph)
    # path = r'D:\Android-exp\exp-example\haircomb\core\r8-all-dependency'
    # remove_not_use_node(method_graph, target_dex_file, path)

    # nx.write_gexf(method_graph, r"D:\Android-exp\exp-example\haircomb\direct-weight-graph\{}.gexf".format(target_dex_file[:-4]))

    # pos = nx.spring_layout(method_graph, seed=42)
    # edge_labels = nx.get_edge_attributes(method_graph, 'weight')
    # nx.draw(method_graph, pos, with_labels=True, node_size=1000, node_color='skyblue', font_size=12, font_weight='bold')
    # nx.draw_networkx_edge_labels(method_graph, pos, edge_labels=edge_labels, font_size=10, font_color='red')
    # plt.title('Directed Weighted Graph')
    # plt.show()


def remove_not_use_node(method_graph: DiGraph, target_dex_file, path):
    dex_files = tools.list_all_files(path)
    for file in dex_files:
        file_name = file.split('\\')[-1]
        if file_name == target_dex_file:
            _, shrink_dex_dvm, shrink_dex_dx = AnalyzeDex(file)
            method_full_name_list = []
            for m in shrink_dex_dvm.get_methods():
                method_full_name_list.append(m.full_name)
            useless_method_node_list = []
            for node in method_graph.nodes:
                if node not in method_full_name_list:
                    useless_method_node_list.append(node)
            print(len(method_graph.nodes), len(useless_method_node_list))
            method_graph.remove_nodes_from(useless_method_node_list)
            nx.write_gexf(method_graph,
                          r"D:\Android-exp\exp-example\haircomb\direct-weight-graph\core-weight-graph\{}.gexf".format(
                              target_dex_file[:-4]))


def increase_edge_weights_from_node(graph, start_node):
    visited = set()

    def dfs(current_node):
        visited.add(current_node)
        neighbors = graph.neighbors(current_node)
        for neighbor in neighbors:
            if neighbor not in visited:
                # 获取当前边的权值并加1
                edge_weight = graph[current_node][neighbor]['weight']
                graph[current_node][neighbor]['weight'] = edge_weight + 1
                dfs(neighbor)

    dfs(start_node)


if __name__ == '__main__':

    dependencies_tree_path = r"D:\zc\haircomb_dependencies.txt"
    apk_dependencies = tools.get_dependency_from_file(dependencies_tree_path)

    dependency_path = r'F:\maven-data\haircomb\dependencies'
    base_keep_rule_path = r'D:\Android-exp\exp-example\haircomb\single-dependency-keep-rules'

    for folder in os.listdir(dependency_path):
        if folder.replace('@', ':') in apk_dependencies:
            dex_file = folder + '.dex'
            dex_tmp_name = os.path.join('dex', dex_file)
            base_path = os.path.join(dependency_path, folder)
            dex_path = os.path.join(base_path, dex_tmp_name)
            print(dex_path)
            if os.path.exists(dex_path):
                _, target_dvm, target_dx = AnalyzeDex(dex_path)

                for method in target_dvm.get_methods():
                    all_methods.append(method.full_name.replace('$', ''))

                analysis_dex_method_entry(os.path.join(base_path, 'dex'), target_dvm, target_dx, dex_file,
                                          base_keep_rule_path)
                # break
