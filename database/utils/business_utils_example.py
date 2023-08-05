import datetime
from database.utils import database_utils_pool


# 查找所有版本
def find_all_file_version(filename):
    sql = "select version from pypi_info_version_all where file_name='%s' order by update_time desc" % filename
    versions = []
    try:

        versions = database_utils_pool.fetchall(sql)  # 获取所有的数据
    except Exception as e:
        print("db error find_elder_version", e)
    return versions


# 查找当前版本是否存在
def is_exist_in_pypi_info_version_all(filename, file_version):
    sql = "SELECT * FROM pypi_info_version_all WHERE version = '%s' and file_name = '%s' limit 1" % (
        file_version, filename)
    nums = database_utils_pool.fetchone(sql)
    if nums is not None:
        return True
    else:
        return False


# 取出所有数据
def get_pypi_info_version():
    # sql = "SELECT * FROM pypi_info_version limit 10000"
    sql = "SELECT * FROM pypi_info_version"
    nums = database_utils_pool.fetchall(sql)
    return nums


# return: [(version_id, version_name, version, file_name, version_date, f_id),...]
def get_all_pypi_info_version_by(file_name):
    sql = "SELECT * FROM pypi_info_version WHERE file_name = '%s'" % (file_name)
    data = database_utils_pool.fetchall(sql)
    return data


# 取出所有数据
def get_package_info_version():
    # sql = "SELECT DISTINCT f_id, package_name, package_version FROM package_info limit 10000"
    sql = "SELECT DISTINCT f_id, package_name, package_version FROM package_info"
    nums = database_utils_pool.fetchall(sql)
    return nums


def is_exist_in_pakcage_info(name, version):
    sql1 = "SELECT * FROM package_info WHERE package_name = '%s'and package_version = '%s' limit 1" % (name, version)
    try:
        db_deps = database_utils_pool.fetchone(sql1)
        if db_deps is not None:
            return True
        else:
            return False
    except Exception as e:
        print("sql dberror" + str(e))
        # directory_utils.move_file(projectDir, r'D:\ZhangTingwei\watchman-spider-file\sql2-error-file')
        return False


# 从数据库获取某个版本的包的数据
def get_requirement(package_name, package_version):
    sql2 = "select DISTINCT requirement,version_range,id from package_info where  package_name='%s' and package_version='%s'" % (
        package_name, package_version)
    get_requirement_data = []
    try:
        get_requirement_data = database_utils_pool.fetchall(sql2)  # 获取所有的数据
    except Exception as e:
        print("db error", e)
    datalist = []
    for u in get_requirement_data:
        temp = [u['requirement'], u["version_range"], u['id']]
        datalist.append(temp)
    return datalist


# 查找当前库是否存在于表package_info中，不存在则无法检测
def is_exit_in_package_info(file_name, file_version):
    sql = "SELECT * FROM package_info WHERE package_name = '%s' and package_version = '%s' limit 1" % (
        file_name, file_version)
    nums = database_utils_pool.fetchone(sql)
    if nums is not None:
        return True
    else:
        return False


# 将文件名字插入到数据库中
def insert_file_name(file_name_db):
    sql = "SELECT file_id FROM pypi_info WHERE file_name = '%s' limit 1" % file_name_db
    nums = database_utils_pool.fetchone(sql)
    if nums is None:
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        sql_insert = "INSERT INTO pypi_info (file_name, file_date) VALUES ('%s','%s')" % (file_name_db, now)
        database_utils_pool.insert(sql_insert)
        # print("INSERT:" + file_name_db + " TO pypi_info FINISHED")
    else:
        pass
        # print("该文件名已存在：" + file_name_db)


# modify_package_info_requirement_info()
def is_exist_in_package_dependencies(filename, version):
    sql = "SELECT * FROM package_dependencies WHERE package_name = '%s' and package_version = '%s' limit 1" % (
        filename, version)
    nums = database_utils_pool.fetchone(sql)
    if nums is not None:
        return True
    else:
        return False


def is_exist_in_no_dependencies(filename, version):
    sql = "SELECT * FROM no_dependencies WHERE package_name = '%s' and package_version = '%s' limit 1" % (
        filename, version)
    nums = database_utils_pool.fetchone(sql)
    if nums is not None:
        return True
    else:
        return False
