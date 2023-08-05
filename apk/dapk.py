import requests
from bs4 import BeautifulSoup
import os
import subprocess


# 获取网页内容
def get_content(url):
    r = requests.get(url)
    r.encoding = 'utf-8'
    return r.text


# 下载 APK 文件
def download_apk(url, apk_dir):
    apk_name = url.split('/')[-1]
    apk_path = os.path.join(apk_dir, apk_name)
    r = requests.get(url, stream=True)
    with open(apk_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    print('Downloaded APK:', apk_name)


# 下载源代码
def download_source(url, source_dir):
    cmd = 'git clone ' + url + ' ' + source_dir
    print(cmd)
    subprocess.call(cmd, shell=True)
    print('Downloaded source code:', url)


# 获取应用信息
def get_app_info(url):
    html = get_content(url)
    soup = BeautifulSoup(html, 'html.parser')
    app_name = soup.find('h1').text
    apk_url = soup.select_one('.package-header .package-download a')['href']
    source_url = soup.select_one('.details-advanced .source-code a')['href']
    return app_name, apk_url, source_url


# 获取应用列表
def get_app_links():
    page_num = 0
    app_links = []
    while len(app_links) < 1:
        url = f'https://f-droid.org/en/packages/?page={page_num}'
        html = get_content(url)
        soup = BeautifulSoup(html, 'html.parser')
        for app in soup.select('.package-header'):
            # app_url = app.select_one('a')['href']
            app_link = app.select_one('a')
            if app_link:
                app_url = app_link['href']
                print(app_url)
                app_links.append(app_url)
            else:
                pass

        page_num += 1
    return app_links


# 下载前1000个应用的 APK 和源代码
def download_apps(apk_path, apk_source_path):
    os.makedirs(apk_path, exist_ok=True)
    os.makedirs(apk_source_path, exist_ok=True)
    app_links = get_app_links()  # [:1000]
    for i, app_link in enumerate(app_links):
        try:
            app_name, apk_url, source_url = get_app_info(app_link)
            # apk_path = os.path.join(apk_path, app_name + '.apk')
            source_path = os.path.join(apk_source_path, app_name)
            # if not os.path.exists(apk_path):
            #     download_apk(apk_url, apk_path)
            if not os.path.exists(source_path):
                download_source(source_url, source_path)
            print(f'[{i + 1}/{len(app_links)}] Downloaded:', app_name)
        except:
            print(f'[{i + 1}/{len(app_links)}] Download failed:', app_link)


if __name__ == '__main__':
    apks_path = r'D:\apk&source\apks'
    apks_source_path = r'D:\apk&source\apk-source'
    download_apps(apks_path, apks_source_path)
