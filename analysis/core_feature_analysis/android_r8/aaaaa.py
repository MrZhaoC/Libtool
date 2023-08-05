import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from sklearn.cluster import SpectralClustering
import scipy

# # 创建一个有向加权图
# G = nx.DiGraph()
#
# # 添加方法调用关系，节点值为方法签名，边权值为调用次数或其他度量指标
# G.add_edge("method1", "method2", weight=5)
# G.add_edge("method2", "method3", weight=3)
# G.add_edge("method3", "method4", weight=2)
# G.add_edge("method4", "method1", weight=4)


def deal_graph(G):
    # 转换为无向加权图
    undirected_graph = G.to_undirected()

    # 提取边权值，构建权重矩阵
    weights = np.array([data["weight"] for _, _, data in undirected_graph.edges(data=True)])
    weight_matrix = nx.to_numpy_matrix(undirected_graph)

    # 进行谱聚类，指定聚类数目
    num_clusters = 2
    spectral = SpectralClustering(n_clusters=num_clusters, affinity="precomputed")
    spectral.fit(weight_matrix)

    # 获取聚类结果
    cluster_labels = spectral.labels_

    # 可视化输出聚类结果
    pos = nx.spring_layout(undirected_graph)
    plt.figure(figsize=(10, 6))

    # 绘制节点
    nx.draw_networkx_nodes(undirected_graph, pos, node_size=500, node_color=cluster_labels, cmap=plt.cm.tab20)

    # 绘制边
    for i, j, data in undirected_graph.edges(data=True):
        plt.text((pos[i][0] + pos[j][0]) / 2, (pos[i][1] + pos[j][1]) / 2, data['weight'], fontsize=10)

    nx.draw_networkx_edges(undirected_graph, pos, width=2, alpha=0.5)

    # 绘制节点标签
    node_labels = {node: node for node in undirected_graph.nodes()}
    # nx.draw_networkx_labels(undirected_graph, pos, labels=node_labels, font_size=10)
    # nx.draw_networkx_edges(undirected_graph, pos)

    plt.title("Spectral Clustering Result")
    plt.axis("off")
    plt.show()


print(nx.__version__)
print(scipy.__version__)
