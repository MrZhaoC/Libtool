import re

from androguard.misc import AnalyzeAPK

apk_path = r'D:\Android-exp\exp-example\haircomb\apk\app-release-unsigned-shrink-obfuscate.apk'

a, d_list, dx = AnalyzeAPK(apk_path)
print('Info: loading and analysis %s' % apk_path)

main_class = []
library_class = []


def get_class_names():
    apk_main_package = a.get_package().split('.')
    apk_main_activity = a.get_main_activity().split('.')  # ??? 返回结果以 .***开头

    common_prefix = ''
    for i in range(min(len(apk_main_package), len(apk_main_activity))):
        if apk_main_package[i] == apk_main_activity[i]:
            common_prefix += apk_main_package[i] + '/'
        else:
            break
    correct_package_name = 'L' + common_prefix
    print('main package: {}'.format(correct_package_name))

    pattern = re.compile(r'^R\$[a-z]+;$')
    for d in d_list:
        for full_class_name in d.get_classes():
            class_name = full_class_name.name
            end_class_name = str(class_name).split('/')[-1]

            if pattern.search(end_class_name) or end_class_name == 'R;':
                continue
            if str(class_name).startswith(correct_package_name):
                main_class.append(class_name)
            if not str(class_name).startswith(correct_package_name):
                library_class.append(class_name)
    return main_class, library_class


if __name__ == '__main__':
    get_class_names()

    result = set()

    for cla_name in main_class:
        for method_x in dx.classes[cla_name].get_methods():
            # to
            for _, callee_to, _ in method_x.get_xref_to():
                callee_class = callee_to.get_class_name()
                if callee_class in main_class:
                    continue
                if callee_class in library_class:
                    # print(callee_class)
                    result.add(callee_class)
            # from
            for _, callee_from, _ in method_x.get_xref_from():
                callee_class = callee_from.get_class_name()
                if callee_class in main_class:
                    continue
                if callee_class in library_class:
                    # print(callee_class)
                    result.add(callee_class)
            # todo:
            # read (class method _)
            #  iget-object v0, p1, Lokhttp3/Request$Builder;->url:Lokhttp3/HttpUrl;
            for class_analysis, field_analysis, _ in method_x.get_xref_read():
                class_name = class_analysis.name
                field_class_name = field_analysis.class_name
                # 是否需要判断不在class_names中的类，因为super_graph时已经添加了全部类节点
                if class_name in main_class or field_class_name in main_class:
                    continue
                # print(class_name, '->', field_class_name)
                result.add(class_name)
                result.add(field_class_name)
            # write (class method _)
            # iput-object v0, p0, Lokhttp3/Request;->url:Lokhttp3/HttpUrl;
            for class_analysis, field_analysis, _ in method_x.get_xref_write():
                class_name = class_analysis.name
                field_class_name = field_analysis.class_name
                # 是否需要判断不在class_names中的类，因为super_graph时已经添加了全部类节点
                if class_name in main_class or field_class_name in main_class:
                    continue
                # print(class_name, '->', field_class_name)
                result.add(class_name)
                result.add(field_class_name)
            # new_instance (class int)
            # new-instance v0, Lokhttp3/HttpUrl$Builder;
            for new_instance_class, _ in method_x.get_xref_new_instance():
                class_name = new_instance_class.name
                if class_name in main_class:
                    continue
                if class_name in library_class:
                    # print(class_name)
                    result.add(class_name)
            # const_class (class int)
            # const-class v0, Lokhttp3/internal/http2/Http2;
            for const_class, _ in method_x.get_xref_const_class():
                class_name = const_class.name
                if class_name in main_class:
                    continue
                if class_name in library_class:
                    # print(class_name)
                    result.add(class_name)
    for cla in result:
        print(cla)
