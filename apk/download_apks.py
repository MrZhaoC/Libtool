import time
from urllib import parse

import requests
from bs4 import BeautifulSoup
import os

base_url = 'https://f-droid.org'

# 获取应用列表页面
app_list_url = f'{base_url}/categories/development/'
app_list_page = requests.get(app_list_url)
soup = BeautifulSoup(app_list_page.content, 'html.parser')

# 获取前1000个应用的详情页面链接
app_links = []
for link in soup.find_all('a'):
    # if 'href' in link.attrs and link.attrs['href'].startswith('/zh_Hans/packages/'):
    if 'href' in link.attrs and link.attrs['href'].startswith('/en/packages/'):
        # print(link.attrs['href'])
        app_links.append(link.attrs['href'])
        if len(app_links) == 100:
            break

if '/zh_Hans/packages/' in app_links:
    app_links.remove('/zh_Hans/packages/')
if '/en/packages/' in app_links:
    app_links.remove('/en/packages/')

# 创建下载目录
download_dir = r'D:\apkandsource'
os.makedirs(download_dir, exist_ok=True)

apk_path = os.path.join(download_dir, 'apks')
apk_source_path = os.path.join(download_dir, 'apks-source')

if not os.path.exists(apk_path):
    os.makedirs(apk_path)
if not os.path.exists(apk_source_path):
    os.makedirs(apk_source_path)

apks = []
apks_source = []

for filename in os.listdir(apk_path):
    apks.append(filename)

for filename in os.listdir(apk_source_path):
    apks_source.append(filename)

# 下载APK和源代码
for i, app_link in enumerate(app_links):
    app_url = f'{base_url}{app_link}'
    app_link = app_link.split('/')[-2]

    # 获取应用详情页面
    app_page = requests.get(app_url)
    time.sleep(0.1)
    soup = BeautifulSoup(app_page.content, 'html.parser')

    # 获取应用名称和包名
    app_name = soup.find('h3').get_text().strip()
    package_name = app_link[len('/packages/'):]
    # print(app_name)
    # print(package_name)

    for lk in soup.find_all('a'):
        if 'href' in lk.attrs:
            # print(lk.attrs['href'])
            # 下载APK
            # if app_link in lk.attrs['href'] and lk.attrs['href'].endswith('.apk'):
            #     apk_url = lk.attrs['href']
            #     print(apk_url)
            #     apk_name_version = apk_url.split('/')[-1]
            #     if apk_name_version in apks:
            #         continue
            #     try:
            #         apk_response = requests.get(apk_url, stream=True)
            #         time.sleep(0.1)
            #         with open(os.path.join(download_dir, 'apks') + '/' + apk_name_version, 'wb') as apk_fp:
            #             # for chunk in apk_response.iter_content(chunk_size=1024):
            #             #     if chunk:
            #             #         apk_fp.write(chunk)
            #             apk_fp.write(apk_response.content)
            #     except Exception as e:
            #         time.sleep(1)
            # 下载源代码
            if app_link in lk.attrs['href'] and lk.attrs['href'].endswith('src.tar.gz'):
                source_code_url = lk.attrs['href']
                print(source_code_url)
                apk_source_name_version = source_code_url.split('/')[-1]
                if apk_source_name_version in apks_source:
                    continue
                source_code_file = f"{os.path.join(download_dir, 'apks-source')}/{apk_source_name_version}"
                try:
                    source_code_response = requests.get(source_code_url, stream=True)
                    time.sleep(0.1)
                    with open(source_code_file, 'wb') as source_code_fp:
                        # for chunk in source_code_response.iter_content(chunk_size=1024):
                        #     if chunk:
                        #         source_code_fp.write(chunk)
                        source_code_fp.write(source_code_response.content)
                except Exception as e:
                    time.sleep(1)
                break

    print(f'Downloaded {app_name} APK and source code. ({i + 1}) -------------')
