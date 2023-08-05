import json
import queue
import threading
import time
from urllib.parse import urljoin
import requests
from requests import adapters
from bs4 import BeautifulSoup
from threading import Lock

lock = Lock()

MAVEN_METADATA = "maven-metadata.xml"


def extract_page_links(url):
    """
    Extracts all the links in a web page.
    :param url:
    :return:
    """

    try:
        time.sleep(1)
        s = requests.session()
        requests.adapters.DEFAULT_RETRIES = 5
        s.keep_alive = False  # 关闭多余连接
        page_content = s.get(url)
        soup = BeautifulSoup(page_content.text, 'html.parser')
        return soup.find_all('a', href=True)
    except Exception as e:
        print("Cannot explore this path: %s" % url)
        time.sleep(10)
        return None


def extract_pom_url(url, pom_url_queue: queue.Queue):
    """
    Extract all pom urls from a given url
    like：https://repo1.maven.org/maven2/bd/com/ipay/sdk/sdk-android/maven-metadata.xml
    :param url:
    :return:
    """

    urls = extract_page_links(url)
    if urls is None:
        return

    # 处理urls
    links = []
    for ur in urls:
        links.append(ur['href'])

    for link in links:
        # find a maven-metadata file, put to queue
        if MAVEN_METADATA in links:
            # could add queue
            pom_url_queue.put(urljoin(url, MAVEN_METADATA))
            return
        # go on find
        if link != "../" and '/' in link:
            u = urljoin(url, link)
            extract_pom_url(u, pom_url_queue)


def process_pom_file(pom_url):
    """
    Extracts groupID, artifactID from a maven-metadata file.
    :param path:
    :return:
    """
    try:
        time.sleep(1)
        requests.adapters.DEFAULT_RETRIES = 5
        s = requests.session()
        s.keep_alive = False  # 关闭多余连接
        pom = s.get(pom_url)
        soup = BeautifulSoup(pom.text, 'html.parser')
    except Exception as e:
        print("Cannot explore this pom_path: %s" % pom_url)
        time.sleep(10)
        return None

    group_id = None
    artifact_id = None

    # TODO: Fixes a case where a wrong groupID is extracted from the parent tag.
    for g in soup.find_all('groupid'):
        if g.parent.name == 'metadata':
            group_id = g
            break

    # TODO: Fix the case where the artifactID is extracted from the parent tag.
    for a in soup.find_all('artifactid'):
        if a.parent.name == 'metadata':
            artifact_id = a
            break

    if group_id is not None and artifact_id is not None:
        return {"groupId": validate_str(group_id.get_text()), "artifactId": validate_str(artifact_id.get_text())}
    else:
        return None


def validate_str(str):
    """
    This removes all the spaces, new line and tabs from a given string
    :param str:
    :return:
    """
    return ''.join(str.split())


def do_craw(url_queue: queue.Queue, pom_url_queue: queue.Queue):
    """
    use queue to execute craw
    """
    while url_queue:
        url = url_queue.get()
        extract_pom_url(url, pom_url_queue)


def do_parse(pom_url_queue: queue.Queue, f1):
    """
     use queue to execute parse
    """
    while pom_url_queue:
        pom_url = pom_url_queue.get()
        ga = process_pom_file(pom_url)
        # 这里讲获取的ga存入文件，g：groupId   a：artifactId
        if ga:
            with lock:
                groupId = ga["groupId"]
                artifactId = ga["artifactId"]
                # 存入数据库

                # f1.write(json.dumps(ga) + '\n')
        else:
            # 这里表示maven-metadata文件中ga信息不全，存入另一个文件
            with open('./no-ga.txt', 'a', encoding='utf-8') as f:
                f.write(pom_url + '\n')


if __name__ == '__main__':
    base_url = r'https://repo1.maven.org/maven2/'

    url_queue = queue.Queue()
    pom_url_queue = queue.Queue()

    for url in extract_page_links(base_url):
        link = url['href']
        if link != "../" and '/' in link:
            url_queue.put(urljoin(base_url, link))

    # 这里100代表线程数，放到服务器上可以设置大一点
    for idx in range(100):
        t = threading.Thread(target=do_craw, args=(url_queue, pom_url_queue))
        t.start()

    # 这里100代表线程数，放到服务器上可以设置大一点
    f1 = open("./ga.txt", 'w', encoding='utf-8')
    for idx in range(100):
        t = threading.Thread(target=do_parse, args=(pom_url_queue, f1))
        t.start()
