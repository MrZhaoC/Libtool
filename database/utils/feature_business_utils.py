from database.utils import database_utils_pool

TABLE_NAME = 'haircomb'


def get_all_tpl_feature():
    sql = 'SELECT * FROM %s' % TABLE_NAME
    feature_info = database_utils_pool.fetchall(sql)
    return feature_info


# 获取等于tpl_name的数据
def get_feature_info_by_tpl_name(tpl_name):
    sql = "SELECT * FROM %s WHERE tpl_name = '%s'" % (TABLE_NAME, tpl_name)
    one_feature = database_utils_pool.fetchall(sql)
    return one_feature


# 根据表名等于table_name获取等于tpl_name的数据
def get_all_by_tpl_name_and_table_name(table_name, tpl_name):
    sql = "SELECT * FROM %s WHERE tpl_name = '%s'" % (table_name, tpl_name)
    one_feature = database_utils_pool.fetchall(sql)
    return one_feature


def insert_core_feature(tpl_name, core_class_count, core_method_count, core_fined_feature_list):
    sql = "INSERT INTO {} (tpl_name, core_cla_count, core_method_count, core_fined_feature) VALUES (%s, %s, %s, %s)".format(TABLE_NAME)
    value = [tpl_name, core_class_count, core_method_count, str(core_fined_feature_list)]
    database_utils_pool.insert_one(sql, value)


def update_core_feature(tpl_name, core_class_count, core_method_count, core_fined_feature_list):
    sql = "UPDATE {} SET core_cla_count = %s, core_method_count = %s, core_fined_feature = %s WHERE tpl_name = %s".format(
        TABLE_NAME)
    value = [core_class_count, core_method_count, str(core_fined_feature_list), tpl_name]
    database_utils_pool.insert_one(sql, value)
    print('Core Feature更新数据成功!')


def update_core_methods(tpl_name, core_method_count):
    sql = "UPDATE {} SET core_method_count = %s WHERE tpl_name = %s".format(TABLE_NAME)
    value = [core_method_count, tpl_name]
    database_utils_pool.insert_one(sql, value)
    print('Core Feature更新数据成功!')


def update_complete_feature(tpl_name, method_count):
    sql = "UPDATE {} SET method_count = %s WHERE tpl_name = %s".format(TABLE_NAME)
    value = [method_count, tpl_name]
    database_utils_pool.insert_one(sql, value)
    print('Complete Feature更新数据成功!')


def insert_complete_feature(tpl_name, class_count, method_count, tpl_feature, course_features, fined_features):
    sql = "INSERT INTO {} (tpl_name, cla_count, method_count, tpl_feature, course_feature, fined_feature) " \
          "VALUES (%s, %s, %s, %s, %s, %s) ".format(TABLE_NAME)
    value = [tpl_name, class_count, method_count, tpl_feature, str(course_features), str(fined_features)]
    database_utils_pool.insert_one(sql, value)
    print('插入数据成功!')


if __name__ == '__main__':
    print(get_all_tpl_feature())
