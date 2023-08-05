import time
import traceback

from tqdm import tqdm
import os
from database.utils import database_utils_pool
import requests

key_list = ["1a705ade5a15dca63defb51170f64a58",  # xmq
            "10e2ea78cd92ee26ec9105730879c393",  # hhy github
            "ed4c58592e1e41183ff2444de08154b0",  # huk521 github
            "4182b1a70e1fb0f6e58f00b7fc0d36b9",  # hu420 github
            "facdcee355da70a1bb759188f8fe852b",  # wwtecdev github
            "a54c237182ea1921fca69b8b288f89f5",  # SIA-hhy
            "b589c52affd3a56da5838cae319aba5f",  # 1024085213@qq.com
            "4be087ca0f8e3ded136d428c43434f52",  # xumeiqiu2019@stumail.neu.edu.cn
            "a3a89224a3bf2f85d3a35e26e0d6c621",  # 1910472@stu.neu.edu.cn
            "5621e1932583e6f468f62cc8f20f91a2",  # xumeiqiu2017@qq.com
            "1844eae9c1c7cbf03fa3e1c159f28947",
            "c8b3e5d2209a89d0ad380817648f5d15",
            "916d108dc30aac79a26ea9a2cdc4c67e",
            "687cb16aa6dd544f0fb5084b1081e1d5",
            "bb3b8290dff2d4855d3277ab0400bdcc",
            "434c23888e65270bc3d0178b90528b27",
            "e9785152f3bd02e9e7ea079932665e62",
            "ee825767f0925788b984168383a81447",
            "097f8c4a6f3c2f3cd2f64812847bd09b",
            "2413ecc2a9fc8c201eb834d45b1e6adf",
            "423953110adc3679bb2837c6294c1c94",  # huk522@163.com
            "c370b16b51fd61c085ebc23bfa7e1af9",  # huk523@163.com
            "38e916ce78481b055078abc21e97245a",  # huk524@163.com
            "ad153d280e9d359567ed53604967db74",  # huk525@163.com
            "6495dc43d11eb5684158c3652d367b7f",  # huk527
            "a38d68eaa5b92aa47cebeaff2bbe2e77",  # huk528
            "35d001efcc6674bf0837aaf28c338874",  # huk529
            "fa3f891184654cfcf6e92167f37d87ba",  # huk530
            ]

base_url = "https://libraries.io/api/maven/{query}/dependencies?api_key={key}"


def query_dependencies_from_database(requirement, version):
    sql = "select package_name, package_version from package_info where requirement = '%s' and requirement_version = " \
          "'%s'" % (
              requirement, version)
    dependencies = database_utils_pool.fetchall(sql)
    print('查询依赖关系共 %s 条' % len(dependencies))
    return dependencies


def convert_download_url(latest_download_url, package_manager_url, artifactId, version):
    name_version = latest_download_url.split("/")[-1]
    # name = name_version.rsplit("-", 1)[0]
    version_ext = name_version.rsplit("-", 1)[1]
    ext = version_ext.split(".")[-1]
    # https://repo1.maven.org/maven2/com/squareup/okhttp3/okhttp/5.0.0-alpha.10/okhttp-5.0.0-alpha.10
    download_url = package_manager_url + "/" + version + "/" + artifactId + "-" + version
    return download_url


def download_tpl(requirement, version, output_path):
    temp_url = base_url.format(query=requirement + "/" + version, key=key_list[0])
    try:
        response = requests.get(temp_url)
        if 200 == response.status_code:
            json_content = response.json()
            latest_download_url = json_content['latest_download_url']
            package_manager_url = json_content['package_manager_url']
            artifactId = requirement.split(":")[1]
            download_url = convert_download_url(latest_download_url, package_manager_url, artifactId, version)
            print(requirement + '-' + version)
            print(latest_download_url)
            download_url1 = download_url + ".jar"
            download_url2 = download_url + ".aar"
            tpl_response1 = requests.get(download_url1)
            tpl_response2 = requests.get(download_url2)
            tpl_response = tpl_response1 if 200 == tpl_response1.status_code else tpl_response2
            name_version = tpl_response.url.split("/")[-1]
            print(tpl_response.url)
            if 200 == tpl_response.status_code:
                # tpl_size = int(tpl_response.headers['Content-Length'])  # kb to byte
                ga = requirement.replace(":", "-")
                final_path = output_path + ga
                if not os.path.exists(final_path):
                    os.makedirs(final_path)
                with open(final_path + '\\' + name_version, 'wb') as f:
                    # for tq in tqdm(range(tpl_size), desc='%s 下载中' % requirement + ":" + version):
                    f.write(tpl_response.content)
            else:
                print('error url %s' % download_url)
    except Exception as e:
        time.sleep(10)
        traceback.print_exc()


if __name__ == '__main__':

    # target_requirement = 'com.squareup.okhttp3:okhttp'
    # target_version = '3.11.0'
    # download_tpl(target_requirement, target_version)

    target_requirement = 'com.github.bumptech.glide:glide'
    target_version = '3.8.0'

    output_path = r'H:\maven-data\maven\glide-' + target_version + '-dependencies\\'

    download_tpl(target_requirement, target_version, output_path)

    dependencies = query_dependencies_from_database(target_requirement, target_version)
    for dep in dependencies:
        download_tpl(dep['package_name'], dep['package_version'], output_path)

