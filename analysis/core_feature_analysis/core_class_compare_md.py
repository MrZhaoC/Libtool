import os

import networkx as nx

from analysis.tpl_to_dex import preprocessing, deal_dependency_tree_from_file
from androguard.misc import AnalyzeAPK, AnalyzeDex, get_default_session
from tools.tools import write_excel_xlsx
from memory_profiler import profile
from analysis.module_decoupling import module_decoupling_for_apk


# # 清空session，减少内存占用
# session = get_default_session()
# session.reset()

def get_annotation_classes(tdx, class_analysis, annotation_classes, td_class_names):
    # 递归结束条件
    if class_analysis.name in annotation_classes:
        return

    annotation_classes.add(class_analysis.name)

    cla_relation = class_analysis.get_vm_class()
    annotation_dir = cla_relation.annotations_directory_item
    if annotation_dir:
        annotation_set_item = annotation_dir.get_annotation_set_item()
        if annotation_set_item:
            for x in annotation_set_item.get_annotation_off_item():
                for y in x.get_annotation_item().get_annotation().get_elements():
                    if y.get_value().get_value_type() == 24:
                        annotation_rel_class_name = y.get_value().get_value()
                        if annotation_rel_class_name in td_class_names:
                            # 递归
                            next_class_analysis = tdx.classes[annotation_rel_class_name]
                            get_annotation_classes(tdx, next_class_analysis, annotation_classes, td_class_names)

                    if y.get_value().get_value_type() == 28:
                        for t in y.get_value().get_value().get_values():
                            if t.get_value_type() == 24:
                                annotation_arr_rel_class_name = t.get_value()
                                if annotation_arr_rel_class_name in td_class_names:
                                    next_arr_class_analysis = tdx.classes[annotation_arr_rel_class_name]
                                    get_annotation_classes(tdx, next_arr_class_analysis, annotation_classes,
                                                           td_class_names)


def get_extend_imple_classes(tdx, class_analysis, ex_im_classes, td_class_names):
    # 递归结束条件
    if class_analysis.name in ex_im_classes:
        return

    ex_im_classes.add(class_analysis.name)

    cla_relation = class_analysis.get_vm_class()
    superclass_name = cla_relation.get_superclassname()
    if superclass_name in td_class_names:
        # 递归
        nsu_class_analysis = tdx.classes[superclass_name]
        get_extend_imple_classes(tdx, nsu_class_analysis, ex_im_classes, td_class_names)

    interface_name_list = cla_relation.get_interfaces()
    for interface_class_name in interface_name_list:
        if interface_class_name in td_class_names:
            # 递归
            nim_class_analysis = tdx.classes[interface_class_name]
            get_extend_imple_classes(tdx, nim_class_analysis, ex_im_classes, td_class_names)


def get_method_invoke_classes(tdx, class_analysis, method_invoke_classes, td_class_names):
    # 递归退出条件
    if class_analysis.name in method_invoke_classes:
        return

    method_invoke_classes.add(class_analysis.name)

    for method_analysis in class_analysis.get_methods():
        for class_ana, field_analysis, _ in method_analysis.get_xref_read():
            class_name = class_ana.name
            field_class_name = field_analysis.class_name
            if class_name in td_class_names:
                get_method_invoke_classes(tdx, class_ana, method_invoke_classes, td_class_names)
            if field_class_name in td_class_names:
                field_class_analysis = tdx.classes[field_class_name]
                get_method_invoke_classes(tdx, field_class_analysis, method_invoke_classes, td_class_names)

        for class_ana, field_analysis, _ in method_analysis.get_xref_write():
            class_name = class_ana.name
            field_class_name = field_analysis.class_name
            if class_name in td_class_names:
                get_method_invoke_classes(tdx, class_ana, method_invoke_classes, td_class_names)
            if field_class_name in td_class_names:
                field_class_analysis = tdx.classes[field_class_name]
                get_method_invoke_classes(tdx, field_class_analysis, method_invoke_classes, td_class_names)

        for new_instance_class, _ in method_analysis.get_xref_new_instance():
            class_name = new_instance_class.name
            if class_name in td_class_names:
                get_method_invoke_classes(tdx, new_instance_class, method_invoke_classes, td_class_names)

        for const_class, _ in method_analysis.get_xref_const_class():
            class_name = const_class.name
            if class_name in td_class_names:
                get_method_invoke_classes(tdx, const_class, method_invoke_classes, td_class_names)

        for _, callee_to, _ in method_analysis.get_xref_to():
            class_name = callee_to.name
            if class_name in td_class_names:
                get_method_invoke_classes(tdx, callee_to, method_invoke_classes, td_class_names)


def construct_self_classes(tdx, td_ref_class, td_class_names):
    # 注解关系 类继承实现 方法 字段（递归）
    annotation_classes = set()
    ex_im_classes = set()
    method_invoke_classes = set()
    for class_analysis in td_ref_class:
        class_analysis = tdx.classes[class_analysis.name]
        get_annotation_classes(tdx, class_analysis, annotation_classes, td_class_names)
        get_extend_imple_classes(tdx, class_analysis, ex_im_classes, td_class_names)
        # for method_analysis in class_analysis.get_methods():
        get_method_invoke_classes(tdx, class_analysis, method_invoke_classes, td_class_names)
    # print(len(annotation_classes), len(ex_im_classes), len(method_invoke_classes))
    core_classes = []
    core_classes.extend(annotation_classes)
    core_classes.extend(ex_im_classes)
    core_classes.extend(method_invoke_classes)
    return set(core_classes)


# fdp: front_dependencies_path
def batch_analysis(tdx, target_dex_fdp, td_name, td_class_names):
    union_core_classes = []
    for root, folders, files in os.walk(target_dex_fdp):
        for file in files:
            ext = os.path.splitext(file)[-1]
            # 排除target_dex
            if ext == '.dex' and file != td_name:
                fd_dex_file = os.path.join(root, file)
                # print(file)
                # current_dex_up_dependency_info = [file]
                _, fd_d, fd_dx = AnalyzeDex(fd_dex_file)

                # 得到所有在td_class_names中的类名
                td_reference_class = []
                for class_x in fd_dx.get_classes():
                    class_name = class_x.name
                    if class_name in td_class_names:
                        td_reference_class.append(class_x)

                # 清空session，减少内存占用
                session = get_default_session()
                session.reset()

                # 根据td_reference_class构建自身的类集合
                core_classes = construct_self_classes(tdx, td_reference_class, td_class_names)
                # print(len(fd_d.get_classes()), len(core_classes))
                for core_cla in core_classes:
                    if core_cla not in union_core_classes:
                        union_core_classes.append(core_cla)
    return union_core_classes


def simple_analysis():
    pass


def module_decoupling_compare(apk_modules, td_name, td_names, un_core_class, un_core_method):
    match_result = []
    for con_components in nx.connected_components(apk_modules):
        cla_list = []
        match_class_names = []
        for cla in con_components:
            # cla = apk_dx.classes[cla]
            cla_list.append(cla)

        # 判断当前dex的所有类名是否在当前的连通分量（模块）中
        for c in un_core_class:
            if c in cla_list:
                match_class_names.append(c)

        match_result.append(match_class_names)
    print(td_name, len(td_names), len(un_core_class), len(un_core_method), len(max(match_result, key=len)))
    return [td_name, len(td_names), len(un_core_class), len(un_core_method), len(max(match_result, key=len))]


# 核心类所构建的方法在模块解耦之后比较
def module_decoupling_compare_method(apk_dvm_x, apk_modules, tdx, td_name, td_class_names, td_method_names,
                                     un_core_class, un_core_method):
    match_result = []
    for con_components in nx.connected_components(apk_modules):
        method_list = []
        match_method_names = []
        for cla in con_components:
            cla = apk_dvm_x.classes[cla]
            for apk_class_method in cla.get_methods():
                method_list.append(apk_class_method.full_name)

        # 判断当前dex的所有方法名是否在当前的连通分量（模块）中
        for c in un_core_class:
            c = tdx.classes[c]
            for m in c.get_methods():
                if m.full_name in method_list:
                    match_method_names.append(m.full_name)
        match_result.append(match_method_names)
    print(td_name, len(td_class_names), len(td_method_names), len(un_core_class), len(un_core_method),
          len(max(match_result, key=len)))
    return [td_name, len(td_class_names), len(td_method_names), len(un_core_class), len(un_core_method),
            len(max(match_result, key=len))]


def no_module_decoupling_compare(apk_dex_list, td_name, td_names, un_core_class, un_core_method):
    apk_classes_names = []
    for apk_d in apk_dex_list:
        for class_super in apk_d.get_classes():
            apk_classes_names.append(class_super.name)
    match_apk_class_names = []
    for c in un_core_class:
        if c in apk_classes_names:
            match_apk_class_names.append(c)
    print(td_name, len(td_names), len(un_core_class), len(un_core_method), len(match_apk_class_names))
    return [td_name, len(td_names), len(un_core_class), len(un_core_method), len(match_apk_class_names)]


if __name__ == '__main__':
    excel_data = []
    apk_path = r'H:\maven-data\apks\haircomb\app-release-unsigned-shrink.apk'
    apk_d_list, apk_dx, modules = module_decoupling.get_connected_components(apk_path)
    # a, apk_d_list, apk_dx = AnalyzeAPK(apk_path)

    dex_dir = r'H:\maven-data\haircomb\dependencies'
    project_dependencies_file = r'C:\Users\DELL\Desktop\haircomb_dependencies.txt'
    # 获取一个项目的所有依赖项
    dependencies_list = deal_dependency_tree_from_file(project_dependencies_file)
    # 处理依赖
    project_dependencies = []
    for dep in dependencies_list:
        project_dependencies.append(dep.replace(':', '@'))
    # 遍历文件
    for filename in os.listdir(dex_dir):
        if filename in project_dependencies:
            # dex_file_path 依赖项文件夹
            dex_file_path = os.path.join(dex_dir, filename)
            for f_name in os.listdir(dex_file_path):
                # 寻找dex文件夹处理
                if f_name == 'dex':
                    dex_folder = os.path.join(dex_file_path, f_name)
                    # fs = os.listdir(dex_folder)  # 判断文件数量用
                    # 获取目标dex文件
                    target_dex_name = filename + '.dex'
                    target_dex_file = os.path.join(dex_folder, target_dex_name)

                    # print(target_dex_file)

                    # 分析target_dex_file
                    try:
                        target_class_names = []
                        target_method_names = []
                        _, target_dvm, target_dx = AnalyzeDex(target_dex_file)
                        # 获取target_dex_file中的所有类名
                        for cla_rel in target_dvm.get_classes():
                            target_class_names.append(cla_rel.name)
                            for meth_rel in cla_rel.get_methods():
                                target_method_names.append(meth_rel.full_name)
                        # 并集
                        union_core_class = batch_analysis(target_dx, dex_folder, target_dex_name, target_class_names)

                        union_core_method = []
                        for cla_rel in target_dvm.get_classes():
                            if cla_rel.name in union_core_class:
                                for method in cla_rel.get_methods():
                                    union_core_method.append(method.full_name)
                        # print(len(target_dvm.get_classes()), len(union_core_class))
                        # res = module_decoupling_compare(modules, target_dex_name, target_class_names, union_core_class,
                        #                                 union_core_method)
                        res = module_decoupling_compare_method(apk_dx, modules, target_dx, target_dex_name,
                                                               target_class_names, target_method_names,
                                                               union_core_class, union_core_method)
                        excel_data.append(res)
                    except Exception as e:
                        print(e)
    # write_excel_xlsx(r'C:\Users\DELL\Desktop\new.xlsx', '压缩后核心类解耦比较', excel_data)
