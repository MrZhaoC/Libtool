import os
import shutil
import zipfile

DOT_DEX = '.dex'
DOT_APK = '.apk'


def batch_decompile_apk(apk_dir, decompile_apk_dir):
    if not os.path.exists(apk_dir):
        print("apk文件夹不存在...")
        return

    if not os.path.exists(decompile_apk_dir):
        os.makedirs(decompile_apk_dir)

    for root, folders, files in os.walk(apk_dir):
        for file in files:
            # 判断文件是否apk结尾
            if not file.endswith(DOT_APK):
                continue
            apk_file = os.path.join(root, file)
            apk_output_dir = os.path.join(decompile_apk_dir, file[:-4])

            if not os.path.exists(apk_output_dir):
                os.makedirs(apk_output_dir)

            # 打印反编译输出路径
            print(apk_output_dir)

            # 这里解决问题是真费劲 -f参数覆盖文件夹，血泪史
            cmd = "java -jar {0} -f d {1} -o {2}".format('../../libs/apktool.jar', apk_file, apk_output_dir)
            os.system(cmd)

    print("\n", "All apks decompile finished...")


def batch_decompile_dex(dex_dir, decompile_dex_dir):
    if not os.path.exists(dex_dir):
        print("dex文件夹不存在...")
        return

    if not os.path.exists(decompile_dex_dir):
        os.makedirs(decompile_dex_dir)

    for root, folders, files in os.walk(dex_dir):
        for file in files:
            # 判断文件是否dex结尾
            if not str(file).endswith(DOT_DEX):
                continue
            dex_file = os.path.join(root, file)
            dex_output_dir = os.path.join(decompile_dex_dir, file[:-4])
            if not os.path.exists(dex_output_dir):
                os.makedirs(dex_output_dir)

            # 打印反编译输出路径
            print(dex_output_dir)

            cmd = 'java -jar {0} d -o {1} {2}'.format('../../libs/baksmali-2.5.2.jar', dex_output_dir, dex_file)
            os.system(cmd)

    print("\n", "All dex decompile finished...")


def batch_decompress_apk(apk_dir, depress_apk_dir):
    if not os.path.exists(apk_dir):
        print("apk文件夹不存在...")
        return

    if not os.path.exists(depress_apk_dir):
        os.makedirs(depress_apk_dir)

    for root, folders, files in os.walk(apk_dir):
        for file in files:
            if str(file).endswith(DOT_APK):

                file_name = str(file).replace(DOT_APK, ".zip")
                try:
                    old_name = os.path.join(root, file)
                    new_name = os.path.join(root, file_name)
                    shutil.copy(old_name, new_name)

                    depress_path = os.path.join(depress_apk_dir, file_name[:-4])

                    # 打印文件输出路径
                    print(depress_path)

                    if not os.path.exists(depress_path):
                        os.makedirs(depress_path)

                    # 解压
                    f = zipfile.ZipFile(new_name, 'r')  # 压缩文件位置
                    for fe in f.namelist():
                        f.extract(fe, depress_path)  # 解压位置
                    f.close()

                except Exception as e:
                    print(e)
    print("All apk depress finished...")


if __name__ == '__main__':
    dex_path = r'D:\Android-exp\exp-example\faketraveler\core\validate'
    dex_output_path = r'D:\Android-exp\exp-example\faketraveler\core\decompile'
    batch_decompile_dex(dex_path, dex_output_path)
