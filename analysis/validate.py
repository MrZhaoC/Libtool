import os
import networkx as nx
from tools.tools import write_excel_xlsx
from androguard.misc import AnalyzeAPK, AnalyzeDex
from analysis.module_decoupling.module_decoupling_for_apk import get_connected_components


apk_path = r'D:\Android-exp\exp-example\faketraveler\apk\app-release-unsigned.apk'
class_names = []
candidate_cla_list = []
candidate_me_list = []

d_list, apk_dx, modules = get_connected_components(apk_path)


def compare_classes(dex_path):
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if not str(file).endswith(".dex"):  # 非dex结尾，跳过
                continue
            dex_file = os.path.join(root, file)
            dex_hash, d, t_dx = AnalyzeDex(dex_file)

            similarity_score = []
            for cd_cla_list in candidate_cla_list:
                match_list = []
                for ca in d.get_classes():
                    ca = ca.name
                    if ca in cd_cla_list:
                        match_list.append(ca)
                match_sim = len(match_list) / len(d.get_classes())
                similarity_score.append(match_sim)
            print('{} --> {}'.format(file, max(similarity_score)))


def compare_methods(dex_path):
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if not str(file).endswith(".dex"):  # 非dex结尾，跳过
                continue
            dex_file = os.path.join(root, file)
            dex_hash, d, t_dx = AnalyzeDex(dex_file)
            similarity_score = []
            for cd_method_list in candidate_me_list:
                match_list = []
                for me in d.get_methods():
                    me = me.full_name
                    if me in cd_method_list:
                        match_list.append(me)
                match_sim = len(match_list) / len(d.get_methods())
                similarity_score.append([len(match_list), len(d.get_methods()), match_sim])
            print('{} --> {}'.format(file, max(similarity_score, key=lambda x: x[2])))


def validate_method(dex_path):
    for con_components in nx.connected_components(modules):
        method_list = []
        for cla in con_components:
            cla = apk_dx.classes[cla]
            for method in cla.get_methods():
                method_list.append(method.full_name)
        candidate_me_list.append(method_list)
    compare_methods(dex_path)


def validate_class(dex_path):
    for con_components in nx.connected_components(modules):
        cla_list = []
        for cla in con_components:
            cla = apk_dx.classes[cla]
            cla_list.append(cla.name)
        candidate_cla_list.append(cla_list)
    compare_classes(dex_path)


def validate_method_no_module_decoupling(apk_path, dex_path):
    apk_a, apk_d_list, apk_dx = AnalyzeAPK(apk_path)
    excel_data = []
    methods = []
    for d in apk_d_list:
        for me in d.get_methods():
            methods.append(me.full_name)
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if str(file).endswith(".dex"):
                dex_file = os.path.join(root, file)
                file = file.replace('@', ':')
                dex_hash, t_d, t_dx = AnalyzeDex(dex_file)
                match = set()
                for meth in t_d.get_methods():
                    if meth.full_name in methods:
                        match.add(meth.full_name)
                print('%-70s %-10s %s' % (file, len(t_d.get_methods()), len(match)))
                # excel_data.append([file, len(d.get_methods()), len(match)])
    # write_excel_xlsx(r'C:\Users\DELL\Desktop\new.xlsx', '未解耦方法比较', excel_data)


def validate_class_no_module_decoupling(apk_path, dex_path):
    cur_apk_a, cur_apk_d_list, cur_apk_dx = AnalyzeAPK(apk_path)
    excel_data = []
    classes = []
    for d in cur_apk_d_list:
        for cla in d.get_classes():
            classes.append(cla.name)
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if str(file).endswith(".dex"):
                dex_file = os.path.join(root, file)
                file = file.replace('@', ':')
                dex_hash, d, t_dx = AnalyzeDex(dex_file)
                match = []
                methods = []
                for cla in d.get_classes():
                    if cla.name in classes:
                        match.append(cla.name)
                        for method in cla.get_methods():
                            methods.append(method.full_name)

                print(file, len(d.get_classes()), len(match), len(methods))
                excel_data.append([file, len(d.get_classes()), len(match), len(methods)])
    write_excel_xlsx(r'C:\Users\DELL\Desktop\new.xlsx', '收缩未解耦类比较', excel_data)


# 2023-05-17
def validate_single_dex_no_module_decoupling(single_dex_path):
    classes = []
    for d in d_list:
        for cla in d.get_classes():
            classes.append(cla.name)
    dex_hash, dex_d, dex_dx = AnalyzeDex(single_dex_path)
    match = []
    for cla in dex_d.get_classes():
        if cla.name in classes:
            match.append(cla.name)
    return match


# 2023-05-17
def validate_apk_shrink_class(dex_path):
    """
        此方法用来验证apk在代码收缩模块解耦后比较dex中的class，对于dex中相同类名的类生成特征
        目的是验证类中方法数量的变化，由于收缩之后类中方法会被删除
    """
    # excel_data = [] excel_data.append(['TPL_NAME', 'dex中类数量', 'dex中方法数量', 'dex匹配shrink_APK类数量',
    # 'dex匹配md_shrink_APK类数量', 'apk_dex方法数量', 'dex_apk方法数量'])
    module_item_class_names = []
    for con_components in nx.connected_components(modules):
        cla_list = []
        for cla in con_components:
            cla = apk_dx.classes[cla]
            cla_list.append(cla.name)
        module_item_class_names.append(cla_list)

    for root, folders, files in os.walk(dex_path):
        for file in files:
            if not str(file).endswith(".dex"):  # 非dex结尾，跳过
                continue
            file_name = file[:-4].replace('@', ':')

            dex_file = os.path.join(root, file)
            dex_hash, dex_d, dex_dx = AnalyzeDex(dex_file)

            match_result = []
            for cd_cla_list in module_item_class_names:
                match_list = []
                for ca in dex_d.get_classes():
                    ca_name = ca.name
                    if ca_name in cd_cla_list:
                        match_list.append(ca_name)
                match_result.append(match_list)
            best_match_result = max(match_result, key=len)

            apk_method_names = []
            dex_method_names = []
            for cla_name in best_match_result:
                apk_class = apk_dx.classes[cla_name]
                for apk_method in apk_class.get_methods():
                    apk_method_names.append(apk_method.full_name)
                dex_class = dex_dx.classes[cla_name]
                for dex_method in dex_class.get_methods():
                    dex_method_names.append(dex_method.full_name)
            # real_apk_shrink_dex_class_names: apk代码收缩之后dex在其中比较到类集合，也就是APK代码收缩之后剩余的类
            real_apk_shrink_dex_class_names = validate_single_dex_no_module_decoupling(dex_file)
            # print(['TPL_NAME', 'dex中类数量' 'dex中方法数量', 'dex匹配shrink_APK类数量', 'dex匹配md_shrink_APK类数量', 'apk_dex方法数量',
            #        'dex_apk方法数量'])

            print([file_name, len(dex_d.get_classes()), len(dex_d.get_methods()), len(real_apk_shrink_dex_class_names),
                   len(best_match_result), len(apk_method_names), len(dex_method_names)])

            # # # 生成核心特征
            # core_cla_count, core_fined_feature = generate_feature.generate_fined_feature_cfg(dex_dx, best_match_result)
            # # # 更新数据库
            # feature_business_utils.update_core_feature(file_name, core_cla_count, core_fined_feature)

    #         excel_data.append(
    #             [file_name, len(dex_d.get_classes()), len(dex_d.get_methods()), len(real_apk_shrink_dex_class_names),
    #              len(best_match_result), len(apk_method_names), len(dex_method_names)])
    # # 写入excel
    # write_excel_xlsx(r'C:\Users\DELL\Desktop\2023-05-17.xlsx', 'new_apk收缩dex类比较', excel_data)


def validate_apk_shrink_method(dex_path):
    module_item_class_names = []
    for con_components in nx.connected_components(modules):
        cla_list = []
        for cla in con_components:
            cla = apk_dx.classes[cla]
            cla_list.append(cla.name)
        module_item_class_names.append(cla_list)
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if not str(file).endswith(".dex"):  # 非dex结尾，跳过
                continue
            file_name = file[:-4].replace('@', ':')

            dex_file = os.path.join(root, file)
            dex_hash, dex_d, dex_dx = AnalyzeDex(dex_file)

            # apk模块解耦之后找到最佳匹配的模块，构建类名的集合
            match_result = []
            for cd_cla_list in module_item_class_names:
                match_list = []
                for ca in dex_d.get_classes():
                    ca_name = ca.name
                    if ca_name in cd_cla_list:
                        match_list.append(ca_name)
                match_result.append(match_list)
            best_match_result = max(match_result, key=len)

            # 根据最佳匹配的类名的集合，构建APK方法名的集合
            apk_method_names = []
            apk_methods = []
            for cla_name in best_match_result:
                apk_class = apk_dx.classes[cla_name]
                for apk_method in apk_class.get_methods():
                    if apk_method.is_external():
                        continue
                    apk_method_names.append(apk_method.full_name)
                    apk_methods.append(apk_method)

            # 根据APK方法名的集合，构建dex方法名的集合
            dex_methods = []
            for dex_class in dex_dx.get_classes():
                for dex_method in dex_class.get_methods():
                    if dex_method.is_external():
                        continue
                    if dex_method.full_name in apk_method_names:
                        dex_methods.append(dex_method)

            # res = set(apk_method_names) - set(dex_methods_names)  # R8关于lambda生成得到方法

            # if len(apk_method_names) != 0:
            print('%-60s %-10s %s' % (file_name, len(apk_method_names), len(dex_methods)))
            # print(len(apk_method_names))
            # print(len(dex_methods))

            # # 生成特征
            # method_hash = []
            # for method in dex_methods:
            #     # 不会包含不在dex中方法，无须判断
            #     method_ops = []
            #     for DVMBasicMethodBlock in method.basic_blocks.gets():  # 获取当前方法的所有基本块
            #         if DVMBasicMethodBlock:
            #             instructions = []
            #             for ins in DVMBasicMethodBlock.get_instructions():
            #                 instructions.append(ins.get_name())
            #             bb_op_code = ''.join(instructions)
            #             method_ops.append(bb_op_code)
            #     method_op_code = ''.join(method_ops)
            #     method_hash.append(pyssdeep.get_hash_buffer(method_op_code))
            #
            # cla_count = len(best_match_result)
            # feature_business_utils.update_core_feature(file_name, cla_count, method_hash)


def get_tpl_base_info(dex_path):
    excel_data = []
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if str(file).endswith(".dex"):
                dex_file = root + "\\" + file
                file = file.replace('@', ':')
                dex_hash, d, t_dx = AnalyzeDex(dex_file)

                excel_data.append([file, len(d.get_classes()), len(d.get_methods())])
    write_excel_xlsx(r'C:\Users\DELL\Desktop\new.xlsx', '20230511-apk-base-info', excel_data)


if __name__ == '__main__':
    dex_path = r'D:\Android-exp\exp-example\faketraveler\dex'

    # validate_class(dex_path)
    validate_method(dex_path)

    # validate_class_no_module_decoupling(apk_path, dex_path)
    # validate_method_no_module_decoupling(apk_path, dex_path)

    # get_tpl_base_info(dex_path)

    # validate_apk_shrink_class(dex_path)
    # validate_apk_shrink_method(dex_path)
