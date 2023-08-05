import os.path
import requests
from tqdm import tqdm
from os.path import split, dirname
from urllib.parse import urlparse
from database.utils import database_utils_pool


def query_target_pom_url(group_id, artifact_id, version_num):
    sql = "select * from maven_pkg_info where groupId = '%s' and artifactId = '%s' and version = '%s'" % (
        group_id, artifact_id, version_num)
    res = database_utils_pool.fetchone(sql)
    if res:
        return res['pom_url']
    else:
        print("数据库中不存在该条记录groupId = %s, artifactId = %s, version = %s" % (group_id, artifact_id, version_num))


def query_pom_urls(gav_list):
    pom_urls = set()
    for gav in gav_list:
        groupId = gav['groupId']
        artifactId = gav['artifactId']
        version = gav['version']
        sql = "select * from maven_pkg_info where groupId = '%s' and artifactId = '%s' and version = '%s'" % (
            groupId, artifactId, version)
        res = database_utils_pool.fetchone(sql)
        if res:
            pom_urls.add(res['pom_url'])
        else:
            print("数据库中不存在该条记录 %s" % gav)
    return pom_urls


def query_target_dependencies(group_id, artifact_id, version_num):
    requirement = group_id + ":" + artifact_id
    sql = "select package_name, package_version from package_info where requirement = '%s' and " \
          "requirement_version = '%s'" % (requirement, version_num)
    # and (scope = 'compile' or scope = 'runtime')
    dependencies = database_utils_pool.fetchall(sql)
    return dependencies


def download_jar_aar(urls, out_path):

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    for url in urls:
        if convert_pom_url_to_jar_aar_url(url):
            jar_url, aar_url = convert_pom_url_to_jar_aar_url(url)
            # 转换成 jar 或 aar 的格式
            jar_name = split(urlparse(jar_url).path)[-1]
            aar_name = split(urlparse(aar_url).path)[-1]
            # 有可能都找不到
            jar_file = requests.get(jar_url)
            aar_file = requests.get(aar_url)

            if 200 == jar_file.status_code:
                jar_size = int(jar_file.headers['Content-Length'])   # kb to byte
                with open(out_path + jar_name, 'wb') as f:
                    for tq in tqdm(range(jar_size), desc='%s 下载中' % jar_name):
                        f.write(jar_file.content)
            # if 404 == jar_file.status_code:
            #     print('error url %s' % jar_url)

            if 200 == aar_file.status_code:
                aar_size = int(aar_file.headers['Content-Length'])
                with open(out_path + aar_name, 'wb') as f:
                    for tq in tqdm(range(aar_size), desc='%s 下载中' % aar_name):
                        f.write(aar_file.content)
            # if 404 == aar_file.status_code:
            #     print('error url %s' % aar_url)


def convert_pom_url_to_jar_aar_url(pom_url):
    base_url = dirname(pom_url)
    pom_name = split(urlparse(pom_url).path)[-1]
    if pom_name.endswith(".pom"):
        jar_name = pom_name.replace(".pom", ".jar")
        aar_name = pom_name.replace(".pom", ".aar")
        jar_url = base_url + '/' + jar_name
        aar_url = base_url + '/' + aar_name
        return jar_url, aar_url
    return None


if __name__ == '__main__':
    output_path = './tpl_dir/'

    groupId = 'org.greenrobot'
    artifactId = 'eventbus'
    version = '3.1.1'

    # groupId = 'com.squareup.okio'
    # artifactId = 'okio'
    # version = '1.14.0'

    target_pom_url = query_target_pom_url(groupId, artifactId, version)
    print(target_pom_url)
    # download_jar_aar(list(target_pom_url), out_path=output_path)

    # dependencies = query_target_dependencies(groupId, artifactId, version)
    # gav_list = list()
    # for dep in dependencies:
    #     gav_dict = dict()
    #     ga = dep['package_name'].split(":")
    #     groupId = ga[0]
    #     artifactId = ga[1]
    #     version = dep['package_version']
    #     gav_dict['groupId'] = groupId
    #     gav_dict['artifactId'] = artifactId
    #     gav_dict['version'] = version
    #     gav_list.append(gav_dict)
    # pom_urls = query_pom_urls(gav_list)
    # download_jar_aar(pom_urls, out_path=output_path)


    # test download
    # pom_urls = [
    #     'https://repo1.maven.org/maven2/ch/exense/step/step-controller-server/3.18.3/step-controller-server-3.18.3.pom',
    #     'https://repo1.maven.org/maven2/classworlds/classworlds/1.0-beta-5/classworlds-1.0-beta-5.pom',
    #     'https://repo1.maven.org/maven2/cloud/altemista/fwk/archetype/cloud-altemistafwk-core-integration-jpa-archetype/3.0.0.RELEASE/cloud-altemistafwk-core-integration-jpa-archetype-3.0.0.RELEASE.pom'
    # ]
    # download_jar_aar(pom_urls, out_path=output_path)

