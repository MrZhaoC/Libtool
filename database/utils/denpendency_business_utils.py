from database.utils import database_utils_pool


# 注意不是同一个数据库
def get_front_dependencies_from_mvn(requirement, version):
    sql = "select package_name, package_version from package_info where requirement = '%s' and requirement_version = " \
          "'%s'" % (
              requirement, version)
    dependencies = database_utils_pool.fetchall(sql)
    print('查询依赖关系共 %s 条' % len(dependencies))
    return dependencies


# 根据三坐标查询
def get_front_dependencies_from_mvn_by_gav(groupId, artifactId, version):
    requirement = groupId + ":" + artifactId
    sql = "select package_name, package_version from package_info where requirement = '%s' and " \
          "requirement_version = '%s'" % (requirement, version)
    dependencies = database_utils_pool.fetchall(sql)
    return dependencies


# single
def get_gav_pom_url(groupId, artifactId, version):
    pass


# all
def get_all_pom_urls():
    pass


# part
def get_part_pom_urls(gav_list):
    pass


# google
def get_front_dependencies_from_google(group_id, artifact_id, version):
    sql = "SELECT * from google_maven_dependencies where d_group_id = '%s' and d_artifact_id = '%s' and d_version = " \
          "'%s'" % (group_id, artifact_id, version)
    dependencies = database_utils_pool.fetchall(sql)
    print('查询依赖关系共 %s 条' % len(dependencies))
    return dependencies
