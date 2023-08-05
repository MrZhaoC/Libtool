import re

import networkx as nx
from androguard.misc import AnalyzeAPK

class_names = []


def get_class_names(a, d_list):
    apk_main_package = a.get_package().split('.')
    apk_main_activity = a.get_main_activity().split('.')  # ??? 返回结果以 .***开头

    common_prefix = ''
    for i in range(min(len(apk_main_package), len(apk_main_activity))):
        if apk_main_package[i] == apk_main_activity[i]:
            common_prefix += apk_main_package[i] + '/'
        else:
            break
    correct_package_name = 'L' + common_prefix
    print(correct_package_name)

    pattern = re.compile(r'^R\$[a-z]+;$')
    for d in d_list:
        for full_class_name in d.get_classes():
            class_name = full_class_name.name
            end_class_name = str(class_name).split('/')[-1]

            if pattern.search(end_class_name) or end_class_name == 'R;':
                continue
            if not str(class_name).startswith(correct_package_name):
                class_names.append(class_name)


def get_extends_classes(d_list):
    class_graph = nx.DiGraph()
    for d in d_list:
        dex_classes = d.get_classes()
        for cla_relation in dex_classes:
            superclass_name = cla_relation.get_superclassname()
            class_name = cla_relation.get_name()
            # todo:
            if class_name in class_names:
                if superclass_name not in class_names:
                    class_graph.add_node(class_name)
                    continue
                if superclass_name != class_name and not class_graph.has_edge(superclass_name, class_name):
                    class_graph.add_edge(superclass_name, class_name)

        for cla_relation in dex_classes:
            # 添加接口实现关系
            interface_name_list = cla_relation.get_interfaces()
            class_name = cla_relation.get_name()
            if class_name in class_names:
                # 有可能没有接口实现关系
                for interface_class_name in interface_name_list:
                    if interface_class_name not in class_names:
                        class_graph.add_node(class_name)
                        continue
                    if interface_class_name != class_name and not class_graph.has_edge(interface_class_name,
                                                                                       class_name):
                        class_graph.add_edge(interface_class_name, class_name)

    return class_graph


def get_annotation_classes(d_list):
    annotation_graph = nx.DiGraph()
    for d in d_list:
        for cla_relation in d.get_classes():
            class_name = cla_relation.get_name()
            if class_name not in class_names:
                continue
            annotation_dir = cla_relation.annotations_directory_item
            if annotation_dir:
                annotation_set_item = annotation_dir.get_annotation_set_item()
                if annotation_set_item:
                    for x in annotation_set_item.get_annotation_off_item():
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
        caller_class = me.get_method().get_class_name()
        if caller_class not in class_names:
            continue
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
        ori_filed = field.get_field()
        caller_field_class = ori_filed.get_class_name()
        if caller_field_class not in class_names:
            continue
        # read
        for _, method_read in field.get_xref_read():
            ori_method = method_read.get_method()
            callee_field_class = ori_method.get_class_name()
            if callee_field_class not in class_names:
                continue
            if caller_field_class != callee_field_class and not field_graph.has_edge(caller_field_class,
                                                                                     callee_field_class):
                field_graph.add_edge(caller_field_class, callee_field_class)
        # write
        for _, method_write in field.get_xref_write():
            ori_method = method_write.get_method()
            callee_field_class = ori_method.get_class_name()
            if callee_field_class not in class_names:
                continue
            if caller_field_class != callee_field_class and not field_graph.has_edge(caller_field_class,
                                                                                     callee_field_class):
                field_graph.add_edge(caller_field_class, callee_field_class)

    return field_graph


def compose_graph(a, d_list, dx):
    superclass_graph = get_extends_classes(d_list)
    annotation_graph = get_annotation_classes(d_list)
    method_graph = get_method_classes(dx)
    field_graph = get_field_classes(dx)
    graph_list = [superclass_graph, method_graph, field_graph, annotation_graph]
    all_graph = nx.compose_all(graph_list)

    dependency_graph = nx.to_undirected(all_graph)
    print('all图中连通分量的个数为：', nx.number_connected_components(dependency_graph))  # 输出图中连通图的数量，也就是候选实例的个数
    print('all_class {}'.format(all_graph.number_of_nodes()))
    nx.write_gexf(all_graph, "../../dependency_graph/dependency_class.gexf")
    return dependency_graph


def get_connected_components(app_path):
    a, d_list, dx = AnalyzeAPK(app_path)
    get_class_names(a, d_list)
    modules = compose_graph(a, d_list, dx)
    return d_list, dx, modules


if __name__ == '__main__':
    apk_path = r'H:\maven-data\apks\haircomb\app-release-unsigned-shrink.apk'
    get_connected_components(apk_path)
