import time
import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup

from database.utils import database_utils_pool

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Mobile Safari/537.36'
}


def group_id_master_index():
    groupIds = []
    master_index_path = r'H:\maven-data\google\master-index.xml'

    tree = ET.parse(master_index_path)
    root = tree.getroot()

    for child in root:
        groupIds.append(child.tag)
    return groupIds


def artifact_id_version_index():
    gaId_versions = []
    groupIds = group_id_master_index()
    artifactId_version_url = r'https://maven.google.com/{}/group-index.xml?hl=zh-cn'
    for groupId in groupIds:
        aid_version_url = artifactId_version_url.format(groupId.replace('.', '/'))
        print(aid_version_url)
        group_index = requests.get(aid_version_url, headers=headers)
        root = ET.fromstring(group_index.content)

        for child in root:
            versions = child.attrib['versions']
            all_version = versions.split(',')
            for v in all_version:
                gav = '{}:{}:{}'.format(groupId, child.tag, v)
                gaId_versions.append(gav)
    return gaId_versions


def process_pom_file():
    pom_urls = []
    gaId_versions = artifact_id_version_index()
    base_url = r'https://maven.google.com/{}/{}/{}/{}-{}.pom?hl=zh-cn'
    for gav in gaId_versions:
        gav = gav.split(':')
        gid = gav[0]
        aid = gav[1]
        version = gav[2]
        pom_url = base_url.format(gid.replace('.', '/'), aid, version, aid, version)
        print(pom_url)
        pom_urls.append(pom_url)
    return pom_urls


def pom_dependencies():
    dependencies_relation = []
    pom_urls = process_pom_file()
    for pom_url in pom_urls:
        try:
            time.sleep(0.5)
            # requests.keep_alive = False  # 关闭多余连接
            pom_response = requests.get(pom_url)
            soup = BeautifulSoup(pom_response.text, features='xml')
        except Exception as e:
            print("pom_url error".format(pom_url))
            time.sleep(10)
            continue
        project_info = []
        project_group_id = None
        project_artifact_id = None
        project_version = None

        for g in soup.find_all('groupId'):
            if g.parent.name == 'project':
                project_group_id = g.text
                break
            elif g.parent.name == 'parent':
                project_group_id = g.text

        for a in soup.find_all('artifactId'):
            if a.parent.name == 'project':
                project_artifact_id = a.text
                break

        for v in soup.find_all('version'):
            if v.parent.name == 'project':
                project_version = v.text
                break
            elif v.parent.name == 'parent':
                project_version = v.text

        jar_with_dependencies = False
        descriptorRef = soup.find('descriptorRef')
        if descriptorRef and descriptorRef.parent.name == 'descriptorRefs' and descriptorRef.text == 'jar-with-dependencies':
            jar_with_dependencies = True

        project_dependencies = []
        for dependency in soup.find_all('dependency'):
            if dependency.parent.name == 'dependencies':
                try:
                    dependency_group_id = dependency.groupId.text
                    dependency_artifact_id = dependency.artifactId.text
                    dependency_version = dependency.version.text
                    dependency_scope = None
                    if dependency.scope:
                        dependency_scope = dependency.scope.text
                    project_dependencies.append([
                        dependency_group_id, dependency_artifact_id, dependency_version, dependency_scope
                    ])
                except Exception as e:
                    print('dependencies error {}'.format(dependency))

        if project_group_id and project_artifact_id and project_version:
            print('success {}'.format(pom_url))

            project_info.append(project_group_id)
            project_info.append(project_artifact_id)
            project_info.append(project_version)
            project_info.append(jar_with_dependencies)
            project_info.append(pom_url)
            project_info.append(project_dependencies)
        else:
            print('{}:{}:{}'.format(project_group_id, project_artifact_id, project_version))
            continue
        dependencies_relation.append(project_info)
    return dependencies_relation


def save_to_database():
    dependencies_relation = pom_dependencies()
    sql1 = "INSERT INTO google_maven_infos (group_id, artifact_id, version, jar_with_dependencies, pom_url) " \
           "VALUES" \
           " (%s, %s, %s, %s, %s)"
    sql2 = "INSERT INTO google_maven_dependencies (group_id, artifact_id, version, d_group_id, d_artifact_id, " \
           "d_version, scope) VALUES (%s, %s, %s, %s, %s, %s, %s) "
    p_info = []
    d_info = []
    for dr in dependencies_relation:
        p_info.append([dr[0], dr[1], dr[2], dr[3], dr[4]])
        database_utils_pool.insert_one(sql1, [dr[0], dr[1], dr[2], dr[3], dr[4]])
        if dr[5]:
            for d in dr[5]:
                d_info.append([dr[0], dr[1], dr[2], d[0], d[1], d[2], d[3]])
                database_utils_pool.insert_one(sql2, [dr[0], dr[1], dr[2], d[0], d[1], d[2], d[3]])

    # database_utils_pool.insert_batch(sql1, p_info)
    # database_utils_pool.insert_batch(sql2, d_info)


if __name__ == '__main__':
    save_to_database()
