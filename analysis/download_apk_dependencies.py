import os
from tools import tools
from database.utils import database_utils_pool


def deal_dependency_tree_from_file(dependency_tree_path):
    dependency_list = []
    with open(dependency_tree_path, 'r') as f:
        content = f.readlines()
        for line in content:
            line = line.split('@')[0]
            line = line.replace('|', '').replace('+', '').replace('---', '').replace('\\', '').lstrip()
            if '>' in line:
                line = line.split('->')
                gav = line[0].split(':')
                final_gav = gav[0] + ':' + gav[1] + ':' + line[1].strip().replace('(*)', '').replace('(c)', '').strip()
                dependency_list.append(final_gav)
            else:
                _gav = line.replace('(*)', '').replace('(c)', '').strip()
                dependency_list.append(_gav)
    print('原依赖树依赖项个数', len(dependency_list))
    print('去重之后依赖项个数', len(set(dependency_list)))
    return dependency_list


def query_tpl_front_dependencies(requirement, version):
    sql = "select package_name, package_version from package_info where requirement = '%s' and requirement_version = " \
          "'%s'" % (
              requirement, version)
    dependencies = database_utils_pool.fetchall(sql)
    return dependencies


def query_tpl_front_dependencies_google(gav_name):
    gav = gav_name.split('@')
    group_id = gav[0]
    artifact_id = gav[1]
    version_num = gav[2]
    sql = "SELECT * from google_maven_dependencies where d_group_id = '%s' and d_artifact_id = '%s' and d_version = " \
          "'%s'" % (
              group_id, artifact_id, version_num
          )
    dependencies = database_utils_pool.fetchall(sql)
    print('查询依赖关系共 %s 条' % len(dependencies))
    return dependencies


def multi_download(dependency_tree_path, output):
    dependencies_list = deal_dependency_tree_from_file(dependency_tree_path)
    for dp in sorted(set(dependencies_list)):
        dp = dp.replace(':', '@')
        # tools.download_tpl([dp], os.path.join(output, dp))
        tools.download_tpl([dp], output)

        dependencies = query_tpl_front_dependencies_google(dp)
        deps = []
        for dep in dependencies:
            scope = dep['scope']
            if scope == 'test':
                continue
            g = dep['group_id']
            a = dep['artifact_id']
            v = dep['version']
            tpl_name = g + '@' + a + '@' + v
            deps.append(tpl_name)
        tools.download_tpl(deps, os.path.join(output_path, dp))


if __name__ == '__main__':
    dependencies_tree_path = r'D:\Android-exp\exp-example\faketraveler\multi-version.txt'
    output_path = r'D:\Android-exp\exp-example\faketraveler\multi-dependency'
    multi_download(dependencies_tree_path, output_path)
