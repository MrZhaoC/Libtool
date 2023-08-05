import ast
import os
import re
import threading
import time
import networkx as nx
from androguard.core.analysis import analysis
from androguard.core.bytecodes import apk, dvm
from androguard.misc import AnalyzeAPK, AnalyzeDex
from matplotlib import pyplot as plt
import pyssdeep
import Levenshtein
import generate_feature
from tools.tools import write_excel_xlsx
from database.utils import feature_business_utils

apk_path = r'D:\Android-exp\exp-example\haircomb\apk\app-release-unsigned-shrink.apk'

apk_class_names = []
excel_data = []

a, d_list, dx = AnalyzeAPK(apk_path)
print('Info: loading and analysis %s' % apk_path)

db_tpl_feature_info = []


def get_class_names():
    apk_main_package = a.get_package().split('.')
    apk_main_activity = a.get_main_activity().split('.')  # ??? 返回结果以 .***开头

    common_prefix = ''
    for i in range(min(len(apk_main_package), len(apk_main_activity))):
        if apk_main_package[i] == apk_main_activity[i]:
            common_prefix += apk_main_package[i] + '/'
        else:
            break
    correct_package_name = 'L' + common_prefix
    print('main package: {}'.format(correct_package_name))

    pattern = re.compile(r'^R\$[a-z]+;$')
    for d in d_list:
        for full_class_name in d.get_classes():
            class_name = full_class_name.name
            end_class_name = str(class_name).split('/')[-1]

            if pattern.search(end_class_name) or end_class_name == 'R;':
                continue
            if not str(class_name).startswith(correct_package_name):
                apk_class_names.append(class_name)


def get_extends_classes():
    class_graph = nx.DiGraph()
    for d in d_list:
        dex_classes = d.get_classes()
        for cla_relation in dex_classes:
            superclass_name = cla_relation.get_superclassname()
            class_name = cla_relation.get_name()
            # todo:
            if class_name in apk_class_names:
                if superclass_name not in apk_class_names:
                    class_graph.add_node(class_name)
                    continue
                if superclass_name != class_name and not class_graph.has_edge(superclass_name, class_name):
                    class_graph.add_edge(superclass_name, class_name)

        for cla_relation in dex_classes:
            # 添加接口实现关系
            interface_name_list = cla_relation.get_interfaces()
            class_name = cla_relation.get_name()
            if class_name in apk_class_names:
                # 有可能没有接口实现关系
                for interface_class_name in interface_name_list:
                    if interface_class_name not in apk_class_names:
                        class_graph.add_node(class_name)
                        continue
                    if interface_class_name != class_name and not class_graph.has_edge(interface_class_name,
                                                                                       class_name):
                        class_graph.add_edge(interface_class_name, class_name)

    # nx.write_gexf(class_graph, "super_class.gexf")
    return class_graph


def get_annotation_classes():
    annotation_graph = nx.DiGraph()
    for d in d_list:
        for cla_relation in d.get_classes():
            class_name = cla_relation.get_name()
            if class_name not in apk_class_names:
                continue
            annotation_dir = cla_relation.annotations_directory_item
            if annotation_dir:
                annotation_set_item = annotation_dir.get_annotation_set_item()
                if annotation_set_item:
                    for x in annotation_set_item.get_annotation_off_item():
                        for y in x.get_annotation_item().get_annotation().get_elements():
                            # print(y.get_value().get_value_type())
                            # 26:method 4:数字 30:None 23:简单类名（ChunkedSink）  28:EncodedArray  24:全类名 27 29
                            # 28:Signature 24:EnclosingClass 26:EnclosingMethod(value = Lokhttp3/Cache;->urls()Ljava/util/Iterator;) 27:retention
                            if y.get_value().get_value_type() == 24:
                                # print(cla_relation.get_name(), y.get_value().get_value())
                                annotation_rel_class_name = y.get_value().get_value()
                                if annotation_rel_class_name in apk_class_names:
                                    if not annotation_graph.has_edge(class_name, annotation_rel_class_name):
                                        annotation_graph.add_edge(class_name, annotation_rel_class_name)
                            if y.get_value().get_value_type() == 28:
                                for t in y.get_value().get_value().get_values():
                                    if t.get_value_type() == 24:  # 23:signature 24:memberClass 27:字段？
                                        # print(cla_relation.get_name(), t.get_value())
                                        annotation_arr_rel_class_name = t.get_value()
                                        if annotation_arr_rel_class_name in apk_class_names:
                                            if not annotation_graph.has_edge(class_name, annotation_arr_rel_class_name):
                                                annotation_graph.add_edge(class_name, annotation_arr_rel_class_name)
    # nx.write_gexf(annotation_graph, "annotation_class.gexf")
    return annotation_graph


def get_method_classes():
    start_time = time.perf_counter()
    method_graph = nx.DiGraph()
    for me in dx.get_methods():
        caller_class = me.get_method().get_class_name()
        if caller_class not in apk_class_names:
            continue
        # to
        for _, callee_to, _ in me.get_xref_to():
            callee_class = callee_to.get_class_name()
            if callee_class not in apk_class_names:
                continue
            if caller_class != callee_class and not method_graph.has_edge(caller_class, callee_class):
                method_graph.add_edge(caller_class, callee_class)
        # from
        for _, callee_from, _ in me.get_xref_from():
            callee_class = callee_from.get_class_name()
            if callee_class not in apk_class_names:
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
            if class_name in apk_class_names and field_class_name in apk_class_names:
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
            if class_name in apk_class_names and field_class_name in apk_class_names:
                if not method_graph.has_edge(class_name, field_class_name):
                    method_graph.add_edge(class_name, field_class_name)

        # new_instance (class int)
        # new-instance v0, Lokhttp3/HttpUrl$Builder;
        for new_instance_class, _ in me.get_xref_new_instance():
            class_name = new_instance_class.name
            if caller_class == class_name:
                continue
            if class_name in apk_class_names:
                if not method_graph.has_edge(caller_class, class_name):
                    method_graph.add_edge(caller_class, class_name)

        # const_class (class int)
        # const-class v0, Lokhttp3/internal/http2/Http2;
        for const_class, _ in me.get_xref_const_class():
            class_name = const_class.name
            if caller_class == class_name:
                continue
            if class_name in apk_class_names:
                if not method_graph.has_edge(caller_class, class_name):
                    method_graph.add_edge(caller_class, class_name)
    end_time = time.perf_counter()
    print('method', end_time - start_time)
    # nx.write_gexf(method_graph, "method_class.gexf")
    return method_graph


def get_field_classes():
    field_graph = nx.DiGraph()
    fields = dx.get_fields()
    for field in fields:
        ori_filed = field.get_field()
        caller_field_class = ori_filed.get_class_name()
        if caller_field_class not in apk_class_names:
            continue
        # read
        for _, method_read in field.get_xref_read():
            ori_method = method_read.get_method()
            callee_field_class = ori_method.get_class_name()
            if callee_field_class not in apk_class_names:
                continue
            if caller_field_class != callee_field_class and not field_graph.has_edge(caller_field_class,
                                                                                     callee_field_class):
                field_graph.add_edge(caller_field_class, callee_field_class)
        # write
        for _, method_write in field.get_xref_write():
            ori_method = method_write.get_method()
            callee_field_class = ori_method.get_class_name()
            if callee_field_class not in apk_class_names:
                continue
            if caller_field_class != callee_field_class and not field_graph.has_edge(caller_field_class,
                                                                                     callee_field_class):
                field_graph.add_edge(caller_field_class, callee_field_class)

    # nx.write_gexf(field_graph, "field_class.gexf")
    return field_graph


class DependencyTread(threading.Thread):
    def __init__(self, func):
        super(DependencyTread, self).__init__()
        self.func = func

    def run(self):
        self.dependency_result = self.func()

    def get_dependency_result(self):
        try:
            return self.dependency_result
        except Exception as e:
            print(e)


def compose_graph():
    start_time = time.perf_counter()

    print('Info: construct class dependency graph')
    superclass_thread = DependencyTread(get_extends_classes)
    annotation_thread = DependencyTread(get_annotation_classes)
    method_thread = DependencyTread(get_method_classes)
    field_thread = DependencyTread(get_field_classes)
    # 开启线程
    superclass_thread.start()
    annotation_thread.start()
    method_thread.start()
    field_thread.start()
    # 等待线程结束
    superclass_thread.join()
    annotation_thread.join()
    method_thread.join()
    field_thread.join()
    # 获取结果
    superclass_graph = superclass_thread.get_dependency_result()
    method_graph = method_thread.get_dependency_result()
    field_graph = field_thread.get_dependency_result()
    annotation_graph = annotation_thread.get_dependency_result()

    # superclass_graph = get_extends_classes()
    # annotation_graph = get_annotation_classes()
    # method_graph = get_method_classes()
    # field_graph = get_field_classes()
    graph_list = [superclass_graph, method_graph, field_graph, annotation_graph]
    all_graph = nx.compose_all(graph_list)

    dependency_graph = nx.to_undirected(all_graph)
    print('all图中连通分量的个数为：', nx.number_connected_components(dependency_graph))  # 输出图中连通图的数量，也就是候选实例的个数
    print('all_class {}'.format(all_graph.number_of_nodes()))

    end_time = time.perf_counter()
    print(end_time - start_time)

    # nx.write_gexf(all_graph, "all_class.gexf")
    return dependency_graph


# tpl_feature_hash_info: [[cla_count, fined_features],...] 该方法在比较核心特征时使用
def CFG_opcode():
    apk_candidate_feature_info = []
    dependency_graph = compose_graph()
    for con_components in nx.connected_components(dependency_graph):
        cla_list = []
        for cla in con_components:
            cla = dx.classes[cla]
            cla_list.append(cla.name)
        cla_count, fined_features = generate_feature.generate_fined_feature_cfg(dx, cla_list)
        apk_candidate_feature_info.append([cla_count, fined_features])
    return dependency_graph, apk_candidate_feature_info


def main():
    apk_candidate_tpl_features = []
    apk_candidate_course_features = []
    apk_candidate_feature_info = []
    dependency_graph = compose_graph()
    for con_components in nx.connected_components(dependency_graph):
        cla_list = []
        cla_name_list = []
        for cla in con_components:
            cla = dx.classes[cla]
            cla_list.append(cla)
            cla_name_list.append(cla.name)
        all_class_list = generate_feature.preprocess(dx, cla_list)
        candidate_tpl_feature, candidate_course_features = generate_feature.get_two_feature(all_class_list)
        apk_candidate_tpl_features.append(candidate_tpl_feature)
        apk_candidate_course_features.append(candidate_course_features)

        cla_count, fined_features = generate_feature.generate_fined_feature_cfg(dx, cla_name_list)
        apk_candidate_feature_info.append([cla_count, fined_features])

    found_tpls = compere_tpl_feature(apk_candidate_tpl_features)
    compere_course_feature(apk_candidate_course_features, found_tpls, apk_candidate_feature_info)


def compere_tpl_feature(apk_candidate_tpl_features):
    found_tpls = []
    for db_tpl_item in db_tpl_feature_info:
        tpl_name = db_tpl_item['tpl_name']
        tpl_class_count = db_tpl_item['cla_count']
        tpl_feature = db_tpl_item['tpl_feature']
        if tpl_feature in apk_candidate_tpl_features:
            print('%-80s %20s  %s' % (tpl_name, 1.0, 'tpl_feature'))
            # 将数据加入excel_data，写入excel
            excel_data.append([tpl_name, tpl_class_count, 1.0])
            found_tpls.append(tpl_name)
    return found_tpls


def compere_course_feature(apk_candidate_course_feature_list, found_tpls, apk_candidate_feature_info):
    COURSE_FEATURE_THRESHOLD = 0.7
    for db_tpl_item in db_tpl_feature_info:
        tpl_name = db_tpl_item['tpl_name']
        tpl_class_count = db_tpl_item['cla_count']
        db_course_features = db_tpl_item['course_feature']  # 粗粒度特征集合

        if found_tpls and tpl_name in found_tpls:
            continue

        course_feature_similarity_list = []
        if db_course_features:
            for apk_candidate_course_features in apk_candidate_course_feature_list:
                match_course_features = []
                for db_course_feature in db_course_features:
                    if db_course_feature in apk_candidate_course_features:
                        match_course_features.append(db_course_feature)

                course_feature_similarity = len(match_course_features) / len(db_course_features)

                course_feature_similarity_list.append(course_feature_similarity)
                if 1.0 in course_feature_similarity_list:
                    break  # 不再继续比较其他apk_candidate_course_features
            if max(course_feature_similarity_list) == 1.0:
                print('%-80s %20s  %s' % (tpl_name, 1.0, 'course_feature'))
                # 将数据加入excel_data，写入excel
                excel_data.append([tpl_name, tpl_class_count, 1.0])
            elif max(course_feature_similarity_list) >= COURSE_FEATURE_THRESHOLD:
                # pass
                # print('%-80s %s  %s' % (tpl_name, max(course_feature_similarity_list), 'course_feature'))
                # 继续比较细粒度特征
                compare_single_fine_grained_feature(db_tpl_item, apk_candidate_feature_info)
            else:
                # print('%-80s %s' % (tpl_name, max(course_feature_similarity_list)))
                pass


def compare_single_fine_grained_feature(db_tpl_item, apk_candidate_feature_info):
    METHOD_SIM_THRESHOLD = 0.85
    TPL_SIM_THRESHOLD = 0.95

    db_tpl_name = db_tpl_item['tpl_name']
    db_tpl_class_count = db_tpl_item['cla_count']
    # 方法生成的细粒度特征的集合
    db_tpl_fine_grained_feature = db_tpl_item['fined_feature']

    tpl_similarity_comparison_list = []
    for apk_candidate_item in apk_candidate_feature_info:  # apk中
        apk_candidate_class_count = apk_candidate_item[0]
        apk_candidate_fine_grained_feature = apk_candidate_item[1]

        # apk中候选类的数量 / 数据库tpl中类的数量 < 0.4 不继续比较这个candidate
        if apk_candidate_class_count / int(db_tpl_class_count) < 0.4:
            continue

        method_similarity_score_list = []
        for db_tpl_method_feature in db_tpl_fine_grained_feature:  # database tpl method feature
            for apk_candidate_method_feature in apk_candidate_fine_grained_feature:  # apk candidate method feature
                # 计算两个方法特征值的编辑距离
                distance = Levenshtein.distance(apk_candidate_method_feature, db_tpl_method_feature)
                method_similarity_score = 1 - distance / max(len(apk_candidate_method_feature),
                                                             len(db_tpl_method_feature))
                if method_similarity_score >= METHOD_SIM_THRESHOLD:
                    method_similarity_score_list.append(method_similarity_score)
                    # db_tpl_method_feature 找到之后不再寻找，继续比较下一个 db_tpl_method_feature
                    break

        # 计算细粒度特征匹配的比例
        tpl_similarity_comparison = len(method_similarity_score_list) / len(db_tpl_fine_grained_feature)

        tpl_similarity_comparison_list.append(tpl_similarity_comparison)
        # tpl相似度大于设置阈值
        if max(tpl_similarity_comparison_list) >= TPL_SIM_THRESHOLD:
            break  # 不在剩余candidate中比较，继续比较数据库

    if tpl_similarity_comparison_list:
        if max(tpl_similarity_comparison_list) >= TPL_SIM_THRESHOLD:
            print('%-80s %20s  %s' % (db_tpl_name, max(tpl_similarity_comparison_list), 'fine_grained_feature1'))
            # 将数据加入excel_data，写入excel
            # excel_data.append([db_tpl_name, tpl_class_count, max(tpl_similarity_comparison_list)])
        else:
            pass
            # print('%-80s %20s  %s' % (db_tpl_name, max(tpl_similarity_comparison_list), 'fine_grained_feature2'))
        # 将数据加入excel_data，写入excel
        excel_data.append([db_tpl_name, db_tpl_class_count, max(tpl_similarity_comparison_list)])
    else:
        pass


# 在比较全部细粒度特征时使用
def compare_all_fine_grained_feature():
    dependency_graph, apk_candidate_feature_info = CFG_opcode()

    METHOD_SIM_THRESHOLD = 0.85
    TPL_SIM_THRESHOLD = 0.92

    start_time = time.perf_counter()

    # 数据库中的每一条特征记录
    for db_tpl_item in db_tpl_feature_info:
        db_tpl_name = db_tpl_item['tpl_name']
        db_tpl_class_count = db_tpl_item['cla_count']
        db_tpl_method_count = db_tpl_item['method_count']
        # 方法生成的细粒度特征的集合
        db_tpl_fine_grained_feature = db_tpl_item['fined_feature']

        tpl_similarity_comparison_list = []
        for apk_candidate_item in apk_candidate_feature_info:  # apk中
            apk_candidate_class_count = apk_candidate_item[0]
            apk_candidate_fine_grained_feature = apk_candidate_item[1]

            # apk中候选类的数量 / 数据库tpl中类的数量 < 0.4 不继续比较这个candidate
            if apk_candidate_class_count / int(db_tpl_class_count) < 0.4:
                continue

            method_similarity_score_list = []
            for db_tpl_method_feature in db_tpl_fine_grained_feature:  # database tpl method feature
                for apk_candidate_method_feature in apk_candidate_fine_grained_feature:  # apk candidate method feature
                    # 计算两个方法特征值的编辑距离
                    distance = Levenshtein.distance(apk_candidate_method_feature, db_tpl_method_feature)
                    method_similarity_score = 1 - distance / max(len(apk_candidate_method_feature),
                                                                 len(db_tpl_method_feature))
                    if method_similarity_score >= METHOD_SIM_THRESHOLD:
                        method_similarity_score_list.append(method_similarity_score)
                        # db_tpl_method_feature 找到之后不再寻找，继续比较下一个 db_tpl_method_feature
                        break

            # 计算细粒度特征匹配的比例
            tpl_similarity_comparison = len(method_similarity_score_list) / len(db_tpl_fine_grained_feature)

            tpl_similarity_comparison_list.append(tpl_similarity_comparison)
            # tpl相似度大于设置阈值
            if max(tpl_similarity_comparison_list) >= TPL_SIM_THRESHOLD:
                break  # 不在剩余candidate中比较，继续比较数据库

        if tpl_similarity_comparison_list:
            if max(tpl_similarity_comparison_list) >= TPL_SIM_THRESHOLD:
                print('%-80s %20s  %s' % (db_tpl_name, max(tpl_similarity_comparison_list), 'fine_grained_feature1'))
                # 将数据加入excel_data，写入excel
                # excel_data.append([db_tpl_name, tpl_class_count, max(tpl_similarity_comparison_list)])
            else:
                print('%-80s %20s  %s' % (db_tpl_name, max(tpl_similarity_comparison_list), 'fine_grained_feature2'))
            # 将数据加入excel_data，写入excel
            excel_data.append(
                [db_tpl_name, db_tpl_class_count, db_tpl_method_count, max(tpl_similarity_comparison_list)])
        else:
            pass
    end_time = time.perf_counter()
    print('\n{}个TPL完成检测，花费时间{}秒'.format(len(excel_data), end_time - start_time))


def compare_core_feature():
    dependency_graph, apk_candidate_feature_info = CFG_opcode()

    METHOD_SIM_THRESHOLD = 0.85
    TPL_SIM_THRESHOLD = 0.95

    for db_tpl_item in db_tpl_feature_info:

        db_tpl_name = db_tpl_item['tpl_name']
        db_tpl_core_class_count = db_tpl_item['core_cla_count']
        db_tpl_core_method_count = db_tpl_item['core_method_count']
        db_tpl_core_fine_grained_feature = db_tpl_item['core_fined_feature']

        # core_feature可能为空
        if db_tpl_core_class_count == 0 or db_tpl_core_fine_grained_feature is None or len(
                db_tpl_core_fine_grained_feature) == 0:
            continue

        tpl_similarity_comparison_list = []
        for item in apk_candidate_feature_info:
            apk_candidate_class_count = item[0]
            apk_candidate_fine_grained_feature = item[1]

            # if apk_candidate_class_count / db_tpl_core_class_count < 0.4:
            #     continue

            method_similarity_score_list = []
            for db_tpl_method_feature in db_tpl_core_fine_grained_feature:  # dex文件method hash
                for apk_candidate_method_feature in apk_candidate_fine_grained_feature:  # APK中 method hash
                    distance = Levenshtein.distance(apk_candidate_method_feature, db_tpl_method_feature)
                    method_similarity_score = 1 - distance / max(len(apk_candidate_method_feature),
                                                                 len(db_tpl_method_feature))
                    if method_similarity_score >= METHOD_SIM_THRESHOLD:
                        method_similarity_score_list.append(method_similarity_score)
                        break  # 找到之后不再寻找

            tpl_similarity_comparison = len(method_similarity_score_list) / len(db_tpl_core_fine_grained_feature)

            tpl_similarity_comparison_list.append(tpl_similarity_comparison)
            # tpl相似度大于设置阈值
            if max(tpl_similarity_comparison_list) >= TPL_SIM_THRESHOLD:
                break  # 不在剩余candidate中比较，继续比较数据库

        if tpl_similarity_comparison_list:
            if max(tpl_similarity_comparison_list) >= TPL_SIM_THRESHOLD:
                print('%-80s %s' % (db_tpl_name, max(tpl_similarity_comparison_list)))
            else:
                print('%-80s %s' % (db_tpl_name, max(tpl_similarity_comparison_list)))
            excel_data.append([db_tpl_name, db_tpl_core_method_count, max(tpl_similarity_comparison_list)])
        else:
            pass


def format_features_from_db():
    data = feature_business_utils.get_all_tpl_feature()
    for tpl_info in data:
        tpl_info['course_feature'] = ast.literal_eval(tpl_info['course_feature'])
        tpl_info['fined_feature'] = ast.literal_eval(tpl_info['fined_feature'])
        if tpl_info['core_fined_feature']:
            tpl_info['core_fined_feature'] = ast.literal_eval(tpl_info['core_fined_feature'])
    return data


if __name__ == '__main__':
    get_class_names()
    db_tpl_feature_info = format_features_from_db()
    # main()
    # compare_all_fine_grained_feature()
    compare_core_feature()

    write_file_flag = True
    path = r"D:\zc\第三方库检测实验数据\2023-06-22-multi-version.xlsx"
    if write_file_flag:
        write_excel_xlsx(path, "core-compare-union", excel_data)
