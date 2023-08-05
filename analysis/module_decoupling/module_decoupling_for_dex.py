import networkx as nx
from androguard.misc import AnalyzeAPK, AnalyzeDex

class_names = []


def get_extends_classes(d):
    class_graph = nx.DiGraph()
    dex_classes = d.get_classes()
    for cla_relation in dex_classes:
        superclass_name = cla_relation.get_superclassname()
        class_name = cla_relation.get_name()
        if superclass_name not in class_names:
            if not class_graph.has_node(class_name):
                class_graph.add_node(class_name)
            continue
        if superclass_name != class_name and not class_graph.has_edge(superclass_name, class_name):
            class_graph.add_edge(superclass_name, class_name)
    for cla_relation in dex_classes:
        # 添加接口实现关系
        interface_name_list = cla_relation.get_interfaces()
        class_name = cla_relation.get_name()
        for interface_class_name in interface_name_list:
            if interface_class_name not in class_names:
                if not class_graph.has_node(class_name):
                    class_graph.add_node(class_name)
                continue
            if interface_class_name != class_name and not class_graph.has_edge(interface_class_name, class_name):
                class_graph.add_edge(interface_class_name, class_name)

    return class_graph


def get_annotation_classes(d):
    annotation_graph = nx.DiGraph()
    for cla_relation in d.get_classes():
        class_name = cla_relation.get_name()
        if class_name not in class_names:
            continue
        annotation_dir = cla_relation.annotations_directory_item
        if annotation_dir:
            for x in annotation_dir.get_annotation_set_item().get_annotation_off_item():
                for y in x.get_annotation_item().get_annotation().get_elements():
                    # print(y.get_value().get_value_type()) 26:method 4:数字 30:None 23:简单类名（ChunkedSink）
                    # 28:EncodedArray  24:全类名 27 29 28:Signature 24:EnclosingClass 26:EnclosingMethod(value =
                    # Lokhttp3/Cache;->urls()Ljava/util/Iterator;) 27:retention
                    if y.get_value().get_value_type() == 24:
                        # print(cla_relation.get_name(), y.get_value().get_value())
                        annotation_rel_class_name = y.get_value().get_value()
                        if annotation_rel_class_name in class_names:
                            if not annotation_graph.has_edge(class_name, annotation_rel_class_name):
                                annotation_graph.add_edge(class_name, annotation_rel_class_name)
                    if y.get_value().get_value_type() == 28:
                        for t in y.get_value().get_value().get_values():
                            if t.get_value_type() == 24:  # 23:signature 24:memberClass 27:字段？
                                annotation_arr_rel_class_name = t.get_value()
                                if annotation_arr_rel_class_name in class_names:
                                    if not annotation_graph.has_edge(class_name, annotation_arr_rel_class_name):
                                        annotation_graph.add_edge(class_name, annotation_arr_rel_class_name)

    return annotation_graph


def get_method_classes(dx):
    method_graph = nx.DiGraph()
    for me in dx.get_methods():
        caller_class = me.get_class_name()
        if caller_class not in class_names:
            continue
        # super_class已经添加全部类节点
        # to
        for _, callee_to, _ in me.get_xref_to():
            callee_class = callee_to.get_class_name()
            if callee_class not in class_names:
                continue
            if caller_class != callee_class and not method_graph.has_edge(caller_class, callee_class):
                method_graph.add_edge(caller_class, callee_class)
        # from
        for _, callee_from, _ in me.get_xref_from():
            callee_class = callee_from.get_class_name()
            if callee_class not in class_names:
                continue
            if caller_class != callee_class and not method_graph.has_edge(callee_class, caller_class):
                method_graph.add_edge(callee_class, caller_class)

        # todo:
        # read (class method _)
        #  iget-object v0, p1, Lokhttp3/Request$Builder;->url:Lokhttp3/HttpUrl;
        for class_analysis, field_analysis, _ in me.get_xref_read():
            class_name = class_analysis.name
            field_class_name = field_analysis.class_name
            # 是否需要判断不在class_names中的类，因为super_graph时已经添加了全部类节点
            if class_name == field_class_name:
                continue
            if class_name in class_names and field_class_name in class_names:
                if not method_graph.has_edge(class_name, field_class_name):
                    method_graph.add_edge(class_name, field_class_name)

        # write (class method _)
        # iput-object v0, p0, Lokhttp3/Request;->url:Lokhttp3/HttpUrl;
        for class_analysis, field_analysis, _ in me.get_xref_write():
            class_name = class_analysis.name
            field_class_name = field_analysis.class_name
            # 是否需要判断不在class_names中的类，因为super_graph时已经添加了全部类节点
            if class_name == field_class_name:
                continue
            if class_name in class_names and field_class_name in class_names:
                if not method_graph.has_edge(class_name, field_class_name):
                    method_graph.add_edge(class_name, field_class_name)

        # new_instance (class int)
        # new-instance v0, Lokhttp3/HttpUrl$Builder;
        for new_instance_class, _ in me.get_xref_new_instance():
            class_name = new_instance_class.name
            if caller_class == class_name:
                continue
            if class_name in class_names:
                if not method_graph.has_edge(caller_class, class_name):
                    method_graph.add_edge(caller_class, class_name)

        # const_class (class int)
        # const-class v0, Lokhttp3/internal/http2/Http2;
        for const_class, _ in me.get_xref_const_class():
            class_name = const_class.name
            if caller_class == class_name:
                continue
            if class_name in class_names:
                if not method_graph.has_edge(caller_class, class_name):
                    method_graph.add_edge(caller_class, class_name)

    return method_graph


def get_field_classes(dx):
    field_graph = nx.DiGraph()
    fields = dx.get_fields()
    for field in fields:
        caller_field_class = field.get_field().get_class_name()
        if caller_field_class not in class_names:
            continue
        # read
        for _, method_read in field.get_xref_read():
            ori_method = method_read.get_method()
            callee_field_class = ori_method.get_class_name()
            if callee_field_class not in class_names:
                continue
            # 去掉自己调用自己的边
            if caller_field_class == callee_field_class:
                continue
            if not field_graph.has_edge(caller_field_class, callee_field_class):
                print(caller_field_class, callee_field_class)
                field_graph.add_edge(caller_field_class, callee_field_class)
        # write
        for _, method_write in field.get_xref_write():
            ori_method = method_write.get_method()
            callee_field_class = ori_method.get_class_name()
            if callee_field_class not in class_names:
                continue
            # 去掉自己调用自己的边
            if caller_field_class == callee_field_class:
                continue
            if not field_graph.has_edge(caller_field_class, callee_field_class):
                field_graph.add_edge(caller_field_class, callee_field_class)

    return field_graph


def compose_graph(d, dx):
    superclass_graph = get_extends_classes(d)
    annotation_graph = get_annotation_classes(d)
    method_graph = get_method_classes(dx)
    field_graph = get_field_classes(dx)
    graph_list = [superclass_graph, method_graph, field_graph, annotation_graph]
    all_graph = nx.compose_all(graph_list)

    dependency_graph = nx.to_undirected(all_graph)
    print('图中连通分量的个数为：', nx.number_connected_components(dependency_graph))  # 输出图中连通图的数量，也就是候选实例的个数
    return dependency_graph


def get_connected_components(dex_file_path):
    _, dex_d, dex_dx = AnalyzeDex(dex_file_path)

    for cla in dex_d.get_classes():
        class_names.append(cla.name)

    all_modules = compose_graph(dex_d, dex_dx)
    return all_modules


if __name__ == '__main__':
    dex_path = r''
    all_connected_components = get_connected_components(dex_path)
