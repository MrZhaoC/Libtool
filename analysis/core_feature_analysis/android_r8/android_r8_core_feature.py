import os

from androguard.misc import AnalyzeDex

from database.utils.feature_business_utils import update_core_feature
from generate_feature import generate_fined_feature_cfg
from tools import tools

DOT_DEX = '.dex'


def android_r8_shrink_union(target_tpl_fdp, out_path, kr_path):
    files = tools.list_all_files(target_tpl_fdp)
    for file in files:
        if file.endswith(DOT_DEX):
            continue
        tpl_name = tools.get_filename_from_path(file)
        pg_conf = os.path.join(kr_path, '{}-keep-rule.cfg'.format(tpl_name))
        tools.android_r8_shrink(out_path, pg_conf, file, tpl_name)


def android_r8_shrink_single(target_tpl_fdp, out_path, kr_path):
    files = tools.list_all_files(target_tpl_fdp)

    for file in files:
        if file.endswith(DOT_DEX):
            continue
        tpl_name = tools.get_filename_from_path(file)
        tpl_item_output_path = os.path.join(out_path, tpl_name)

        # 输出文件夹
        if not os.path.exists(tpl_item_output_path):
            os.makedirs(tpl_item_output_path)

        # 输入文件夹
        tpl_item_input_path = os.path.join(kr_path, tpl_name)
        if not os.path.exists(tpl_item_input_path):
            continue
        cfg_files = tools.list_all_files(tpl_item_input_path)

        for cfg_file in cfg_files:
            tools.android_r8_shrink(tpl_item_output_path, cfg_file, file, tpl_name)


def save_core_feature(dex_path):
    files = tools.list_all_files(dex_path)
    for file in files:
        if file.endswith(DOT_DEX):
            filename = tools.get_filename_from_path(file).replace('@', ':')
            try:
                target_class_names = []
                _, target_dvm, target_dx = AnalyzeDex(file)
                # 获取target_dex_file中的所有类名
                for cla_rel in target_dvm.get_classes():
                    target_class_names.append(cla_rel.name)
                core_method_count = target_dvm.get_len_methods()
                print(filename, len(target_class_names), core_method_count)
                # 生成核心特征
                core_cla_count, core_fined_feature = generate_fined_feature_cfg(target_dx, target_class_names)
                # 更新数据库
                update_core_feature(filename, core_cla_count, core_method_count, core_fined_feature)
            except Exception as e:
                print(e)


if __name__ == '__main__':
    tpl_path = r'D:\Android-exp\exp-example\faketraveler\libraries'
    output_path = r'D:\Android-exp\exp-example\faketraveler\core\r8-all-dependency'
    keep_rule_path = r'D:\Android-exp\exp-example\faketraveler\keep-rules\test'
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    # Android R8工具代码收缩，生成Dex
    android_r8_shrink_union(tpl_path, output_path, keep_rule_path)
    # 核心特征存储数据库
    save_core_feature(output_path)
