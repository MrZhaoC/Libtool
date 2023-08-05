import os
import zipfile
import tools
from tools.tools import list_all_files

DOT_DEX = '.dex'
DOT_AAR = '.aar'
DOT_JAR = '.jar'


# param : t_version_skip 测试版本是否跳过
def preprocessing(tpl_file_path, output_path, t_version_skip):
    print(tpl_file_path)
    files = list_all_files(tpl_file_path)
    for file in files:
        parent_dir = os.path.dirname(file)

        # aar处理
        if file.endswith(DOT_AAR) and file.replace(DOT_AAR, DOT_JAR) not in files:
            # 解压 提取classes.jar 文件
            arr_file = file.split("\\")[-1]
            aar_name = os.path.splitext(arr_file)[0]  # 分离文件名 和 后缀名
            zip_file = zipfile.ZipFile(file)

            for names in zip_file.namelist():
                if names == "classes.jar":
                    zip_file.extract(names, parent_dir)
                    old_path = os.path.join(parent_dir, names)
                    jar_path = os.path.join(parent_dir, aar_name) + DOT_JAR
                    try:
                        os.rename(old_path, jar_path)
                    except Exception as e:
                        os.remove(jar_path)
                        os.rename(old_path, jar_path)
                    jar_to_dex(jar_path, output_path, t_version_skip)

        # jar处理
        if file.endswith(DOT_JAR):
            jar_to_dex(file, output_path, t_version_skip)


def jar_to_dex(jar_file, output_path, t_version_skip):
    # 转换jar to dex
    full_name = jar_file.split("\\")[-1]
    jar_name = os.path.splitext(full_name)[0]
    dex_file_name = jar_name + DOT_DEX

    # 所有 alpha beta rc版本跳过
    if t_version_skip:
        version_num = jar_name.split('@')[-1]
        if '-' in version_num:
            return

    print(full_name)

    if not os.path.exists(output_path):
        os.makedirs(output_path)
    try:
        cmd = r"d8 {0} --release  --intermediate --output {1} --libs E:\android\sdk\platforms\android-33\android.jar".format(
            jar_file, output_path)
        os.system(cmd)
        try:
            os.rename(os.path.join(output_path, 'classes.dex'), os.path.join(output_path, dex_file_name))
        except Exception as e:
            os.remove(os.path.join(output_path, dex_file_name))
            os.rename(os.path.join(output_path, 'classes.dex'), os.path.join(output_path, dex_file_name))
    except Exception as e:
        print(e)


def multiple_dependencies_dir(path, deps_tree_path):
    dependencies = tools.deal_dependency_tree_from_file(dependencies_tree_path)
    format_dependencies = []
    for dep in sorted(set(dependencies)):
        format_dependencies.append(dep.replace(':', '@'))
    for filename in os.listdir(path):
        if filename in format_dependencies:
            tpl_path = os.path.join(path, filename)

            print(tpl_path)

            output_path = os.path.join(tpl_path, 'dex')

            if os.path.exists(output_path):
                continue
            #     shutil.rmtree(output_path)

            if not os.path.exists(output_path):
                os.makedirs(output_path)
            preprocessing(tpl_path, output_path, True)
            # else:
            #     # 存在的不处理
            #     print(tpl_path, 'dex文件已经存在')
    print("tpl to dex finished...")


if __name__ == '__main__':
    # library_path = r'D:\Android-exp\google_libraries'
    # dex_path = r'D:\Android-exp\google_dex'
    # test_version_skip = False
    # preprocessing(library_path, dex_path, test_version_skip)

    tpl_dir = r'D:\Android-exp\exp-example\faketraveler\multi-dependency'
    dependencies_tree_path = r'D:\Android-exp\exp-example\faketraveler\multi-version.txt'
    multiple_dependencies_dir(tpl_dir, dependencies_tree_path)
