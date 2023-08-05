import os
import gzip
import tarfile
import zipfile

source_path = r'E:\fdroid_downloads\apks-source'


def decompress_dir(path):
    build_gradle = []
    dontobfuscate = []
    dontoptimize = []
    dontshrink = []
    src_count = 0
    for file in os.listdir(path):
        if file.endswith('_src'):
            src_count += 1
            file_path = os.path.join(path, file)
            for root, folders, f in os.walk(file_path):
                flag = False
                for fi in f:
                    if 'build.gradle' == fi or 'build.gradle.kts' == fi:
                        bg = os.path.join(root, fi)
                        with open(bg, 'r') as c:
                            for line in c.readlines():
                                # print(line)
                                if line.strip() == 'minifyEnabled true':
                                    flag = True
                                    # print(bg)
                                    build_gradle.append(file)
                                    break
                    if flag and 'proguard-android-optimize.txt' == fi:
                        print(file)
                    if flag and 'proguard-rules.pro' == fi:
                        pp = os.path.join(root, fi)
                        with open(pp, 'r') as c:
                            for line in c.readlines():
                                # print(line)
                                if line.strip() == '-dontobfuscate':
                                    dontobfuscate.append(file)
                                elif line.strip() == '-dontoptimize':
                                    dontoptimize.append(file)
                                elif line.strip() == '-dontshrink':
                                    dontshrink.append(file)

    print(src_count)
    print(len(build_gradle))
    print(len(set(build_gradle)))

    print()

    print(len(set(dontobfuscate)))
    print(len(set(dontoptimize)))
    print(len(set(dontshrink)))


if __name__ == '__main__':
    decompress_dir(source_path)
