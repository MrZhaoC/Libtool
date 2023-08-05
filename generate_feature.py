import ast
import hashlib
import os
import pyssdeep
from androguard.misc import AnalyzeDex
from database.utils import database_utils_pool, feature_business_utils

# dex_path = r'F:\maven-data\haircomb\format_jar\nnnDex'
dex_path = r'D:\Android-exp\exp-example\faketraveler\mv-libraries'


def get_all_feature():
    db_library_names = []
    features = feature_business_utils.get_all_tpl_feature()
    for item in features:
        db_library_names.append(item['tpl_name'])
    return db_library_names


def process_dex_files():
    db_library_names = get_all_feature()
    for root, folders, files in os.walk(dex_path):
        for file in files:
            if not file.endswith(".dex"):
                continue
            dex_file = os.path.join(root, file)
            # format dex file name
            tpl_name = file.split('.dex')[0].replace('@', ':')
            if tpl_name in db_library_names:  # 数据库中存在该记录跳过
                print('数据库中已经存在该记录 %s' % tpl_name)
                continue
            _, dex_dvm, dex_dx = AnalyzeDex(dex_file)
            print(tpl_name)
            generate_feature(dex_dvm, dex_dx, tpl_name)


def generate_feature(d, dx, tpl_name):
    class_names = []
    for cla_rel in d.get_classes():
        class_names.append(cla_rel.name)
    # 添加tpl方法数量字段
    method_count = d.get_len_methods()
    cla_count, fined_features = generate_fined_feature_cfg(dx, class_names)
    all_cla_list = preprocess(dx, dx.get_classes())

    tpl_feature, course_features = get_two_feature(all_cla_list)
    # database insert complete feature info
    feature_business_utils.insert_complete_feature(tpl_name, cla_count, method_count, tpl_feature, course_features, fined_features)
    # feature_business_utils.update_complete_feature(tpl_name, method_count)


def generate_fined_feature(dx, class_names):
    method_hash = []
    for cla in class_names:
        for method in dx.classes[cla].get_methods():
            if method.is_external():
                continue
            m = method.get_method()
            method_op = []
            for idx, ins in m.get_instructions_idx():
                method_op.append(ins.get_name())
            m_hash = ''.join(sorted(method_op))
            # todo: 没有方法体的方法要不要生成特征
            # if m_hash == '':  # 对于没有方法体的方法处理
            #     continue
            method_hash.append(pyssdeep.get_hash_buffer(m_hash))
    cla_count = len(class_names)
    return cla_count, method_hash


# td: target_dvm    union_core_class: 构建核心类的并集
def generate_core_feature(td, union_core_class):
    method_hash = []
    for cla_rel in td.get_classes():
        if cla_rel.name in union_core_class:
            # 生成核心特征
            for method in cla_rel.get_methods():
                method_ops = []
                # for idx, ins in method.get_instructions_idx():
                #     method_ops.append(ins.get_name())
                # m_hash = ''.join(sorted(method_ops))
                # # if m_hash == '':
                # #     continue
                # method_hash.append(pyssdeep.get_hash_buffer(m_hash))
                for DVMBasicMethodBlock in method.basic_blocks.gets():  # 获取当前方法的所有基本块
                    if DVMBasicMethodBlock:
                        instructions = []
                        for ins in DVMBasicMethodBlock.get_instructions():
                            instructions.append(ins.get_name())
                        bb_op_code = ''.join(instructions)
                        method_ops.append(bb_op_code)
                method_op_code = ''.join(method_ops)
                method_hash.append(pyssdeep.get_hash_buffer(method_op_code))
    cla_count = len(union_core_class)
    return cla_count, method_hash


# 目前是使用这个方法构建核心特征
def generate_fined_feature_cfg(dx, class_names):
    method_hash = []
    for cla in class_names:
        for method in dx.classes[cla].get_methods():
            # for method in cla.get_methods():
            if method.is_external():
                continue
            method_ops = []
            for DVMBasicMethodBlock in method.basic_blocks.gets():  # 获取当前方法的所有基本块
                if DVMBasicMethodBlock:
                    instructions = []
                    for ins in DVMBasicMethodBlock.get_instructions():
                        instructions.append(ins.get_name())
                    bb_op_code = ''.join(instructions)
                    method_ops.append(bb_op_code)
            method_op_code = ''.join(method_ops)
            method_hash.append(pyssdeep.get_hash_buffer(method_op_code))
    cla_count = len(class_names)
    return cla_count, method_hash


def get_cfg_adjacency_list(meth):
    meth_cfg_list = []
    # all_basic_blocks = []
    # for DVMBasicMethodBlock in meth.basic_blocks.gets():  # 获取当前方法的所有基本块
    #     all_basic_blocks.append(DVMBasicMethodBlock)
    # all_basic_blocks = sorted(all_basic_blocks, key=lambda e: e.get_nb_instructions())  # 按照每个basic_block中的操作码数量进行排序
    for DVMBasicMethodBlock in meth.basic_blocks.gets():
        adjacency_dict = {}
        if DVMBasicMethodBlock:
            # print(DVMBasicMethodBlock.get_nb_instructions())
            instructions = []
            for ins in DVMBasicMethodBlock.get_instructions():
                instructions.append(ins.get_name())
            # 排序连接
            instruction = ''.join(sorted(instructions))  # 父节点
            child = []
            for bb_next in DVMBasicMethodBlock.get_next():
                # child.append(bb_next[2].get_name())
                next_instructions = []
                for ins in bb_next[2].get_instructions():
                    next_instructions.append(ins.get_name())
                # 排序连接
                next_instruction = ''.join(sorted(next_instructions))  # 孩子节点
                child.append(next_instruction)
            adjacency_dict[instruction] = sorted(child)  # cfg邻接表表示
            meth_cfg_list.append(adjacency_dict)
    return meth_cfg_list


def preprocess(dx, classes):
    all_cla_list = []  # all_class [class[[method],[method],[],[]],class[[method],[method],[],[]]]
    for cla in classes:
        if cla.is_external():
            continue
        cla_meth_list = []  # 每个类中方法的集合 class[[method],[method],[],[]]
        for me in cla.get_methods():
            meth = dx.get_method(me.get_method())
            meth_cfg_adjacency_list = get_cfg_adjacency_list(meth)  # 获取每个方法的邻接链表
            if meth_cfg_adjacency_list:  # 排除没有方法体的方法
                cla_meth_list.append(meth_cfg_adjacency_list)
        if cla_meth_list:  # 排除不包含任何方法的类 interface
            all_cla_list.append(cla_meth_list)
    return all_cla_list


def generate_tpl_feature(method_hashs):
    method_hashs = sorted(method_hashs)  # method_hashs : [hash1, hash2,...] sort
    connect_hash = ''.join(method_hashs)  # connect
    tpl_feature = hashlib.sha256(connect_hash.encode('utf-8')).hexdigest()
    return tpl_feature


def get_two_feature(all_cla_list):
    course_features = []  # 类粒度为特征建立特征值
    for cla_meth_list in all_cla_list:  # cla_meth_list : class[[method],[method],[],[]]
        method_hashs = []  # 每个类中所包含的方法hash
        for method_cfg_aj_list in cla_meth_list:  # method_cfg_aj_list : [parent1_op:[child1_op, child2_op],...]
            # if method_cfg_aj_list:  # method_cfg_aj_list 为空也生成hash
            adjacency_list_format = str(method_cfg_aj_list)
            meth_aj_list_hash = hashlib.sha256(adjacency_list_format.encode('utf-8')).hexdigest()  # 每个方法邻接链表生成hash
            method_hashs.append(meth_aj_list_hash)
        # 排序 连接 hash
        class_hash_feature = hashlib.sha256(''.join(sorted(method_hashs)).encode('utf-8')).hexdigest()
        course_features.append(class_hash_feature)
    # 粗粒度特征 排序 连接 hash
    tpl_feature = hashlib.sha256(''.join(sorted(course_features)).encode('utf-8')).hexdigest()
    return tpl_feature, course_features


if __name__ == '__main__':
    process_dex_files()
