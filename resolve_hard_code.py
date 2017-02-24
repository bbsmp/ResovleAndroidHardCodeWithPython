import os
import re
from pypinyin import lazy_pinyin
from random import Random

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def get_layout_files(path):
    '''
    获取所有的布局文件
    :param path: 布局文件路径
    :return:
    '''
    res = []
    files = os.listdir(path)
    for file in files:
        res.append(path + "/" + file)

    return res

def generate_random_string(random_length):
    '''
    生成随机字符串
    :param random_length: 长度
    :return:
    '''
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz'
    length = len(chars) - 1
    random = Random()
    for i in range(random.randint(1, random_length)):
        if len(str) != 0:
            str += "_"
        str += chars[random.randint(0, length)]
    return str

def get_file_element_tree(file):
    '''
    更具文件名（路径）返回ElementTree根节点
    :param file:
    :return:
    '''
    tree = ET.ElementTree(file=file)
    return tree.getroot()


def find_hard_code_attribute_value(tree_root, attrs):
    '''
    获取属性值
    :param tree_root: ElementTree树根
    :param attr: 要获取值的属性
    :return: set() 返回值， 用集合保存，可以去掉重复的元素
    '''
    res = set()
    for attr in attrs:
        root_hard_code = tree_root.get(attr) #  获取根节点的硬编码
        if root_hard_code is not None and len(root_hard_code) and str(root_hard_code).find("@string/") == -1:
            # 如果属性值不会空且不是软编码（）则就是我们要找的硬编码字符串
            res.add(root_hard_code)
        children = tree_root.findall(".//*[@" + attr + "]")
        for child in children:
            hard_code = child.get(attr) # 获取属性值
            if hard_code is not None and len(hard_code) and str(hard_code).find("@string/") == -1:
                # 如果属性值不会空且不是软编码（）则就是我们要找的硬编码字符串
                res.add(hard_code)
    return res

def generate_name_of_hard_code_string(hard_codes):
    '''
    根据硬编码字符串生成符合规范的名字，这里我们根据这样的规则生成名字：
    1、英文字符串，则用其本省（出去空格、标点等）
    2、中文字符串，则为其单字节拼音用"_"连接，如"硬编码"对应的名称为"yin_bian_ma"，
        这里的拼音转换我们通过pypinyin库来实现，如果涉及到分词，还需要安装jieba
    :param hard_codes:
    :return: 返回类型为字典，字典的键为硬编码的值，值则为根据硬编码生成的符合strings资源文件命名规范的字符串
    '''
    res = dict()
    for hard_code in hard_codes:
        hc = re.sub("""[\s+\.\!\/_,\{\}:$%^*()?+\"\']+|[+——＋！：，\\\ 。？、~@#￥%……&*（）]+""", "", hard_code) #去除特殊字符
        py = ''
        if hc is None or len(hc) == 0: #如果去除字符后为，则硬编码为特殊字符，这是我们就要随机命名
            py = generate_random_string(15)
        else:
            py = lazy_pinyin(hc)
            py = '_'.join(py)[0:25].strip() #限制长度，去除空格
        try:
            res[str(hard_code)] = py
        except Exception as e:
            print(e)
            pass

    return res


def generate_strings_xml(file, dict):
    '''
    根据字典生成strings.xml文件
    :param file: 文件路径
    :param dict: 硬编码字符串和其名称构成的字典
    :return:
    '''
    f = open(file,"w")
    strings = []
    strings.append('<resources>\n')
    for (k, v) in dict.items():
        temp = '\t<string name="' + v + '">' + k + '</string>\n'
        strings.append(temp)
    strings.append("</resources>")
    try:
        f.writelines(strings)
        f.close()
        print("strings.xml文件生成成功")
    except Exception as e:
        print(e)
        print("strings.xml文件生成失败")
        pass

def replace_hard_code(src_file, des_dir, dicts):
    '''
    用字符串引用替换所有的字符
    :param src_file: 带替换的布局文件
    :param des_file: 替换后的文件
    :param dict: 硬编码字典
    :return:
    '''
    lines = open(src_file).readlines()
    new_lines = []
    for line in lines:
        for (k, v) in dicts.items():
            line = line.replace('="' + k +'"',  '="' + "@string/" + v + '"')
        if len(line.strip()) > 0:
            new_lines.append(line)
    if not os.path.lexists(des_dir):
        os.makedirs(des_dir)
    des_file = file.replace("layout/", des_dir)
    with open(des_file, "w") as d_f:
        d_f.writelines(new_lines)


def get_string_and_name_from_stringXML(file):
    '''
    读取strings.xml中的字符串资源，用字典保存
    :param file:
    :return:
    '''
    res = {}
    root = get_file_element_tree(file)
    strings = root.findall(".//string")
    for str in strings:
        res[str.text] = str.get("name")
    return res

if __name__ == '__main__':

    #属性
    attrs = (
        "{http://schemas.android.com/apk/res/android}text",
        "{http://schemas.android.com/apk/res/android}hint",
        "{http://schemas.android.com/tools}text",
    )
    #1、获取所有布局文件
    layout_files = get_layout_files("layout")

    #2、根文件获取ElementTree的根节点
    layout_roots = []
    for file in layout_files:
        try:
            root = get_file_element_tree(file)
        except:
            pass
        if root is not None:
            layout_roots.append(root)

    #3、找出所有的硬编码字符串
    hard_codes = []
    for root in layout_roots:
        hard_codes.extend(find_hard_code_attribute_value(root, attrs))

    #4、根硬编码字符串生成符合命名规则的名称，用字典保存，字典key为硬编码字符串,value为对应的名称
    hard_codes_dict = generate_name_of_hard_code_string(hard_codes)

    #5、生成strings.xml文件
    generate_strings_xml("strings.xml", hard_codes_dict)

    #6、读取strings.xml中的字符串资源，之所以不复用上一部的hard_codes_dict，是因为要手动修复strings.xml可能产生的错误
    h_d_dict = get_string_and_name_from_stringXML("strings.xml")

    #7、替换布局文件中的硬编码
    for file in layout_files:
        # des_file = file.replace("layout/", "layout_copy/")
        des_dir = "layout_replaced/"
        replace_hard_code(file, des_dir, h_d_dict)


    #8、ok 大功告成
    print("ok，大功告成！！嘿嘿")