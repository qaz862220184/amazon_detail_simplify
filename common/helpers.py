import json
from importlib import import_module
import os
import html
import random


def get_absolute_path(path):
    """
    获取指定的完整路径
    :return:
    """
    # 根目录
    root_path = os.path.dirname(os.path.dirname(__file__))
    if root_path not in path:
        sep = os.sep
        if not path.startswith(sep):
            path = sep + path
        path = root_path + path
    return os.path.abspath(path)


def get_dynamic_class(name):
    """
    动态导入类并获取类对象
    :param name:
    :return:
    """
    if '.' not in name:
        return False
    arr = name.split('.')
    module_name = '.'.join(arr[0:len(arr) - 1])
    class_name = arr[-1]
    try:
        import_obj = import_module(module_name)
    except Exception as ex:
        return False
    return getattr(import_obj, class_name)


def file_put_contents(filepath, content, mode='a', encoding='UTF-8'):
    """
    往文件里写入内容
    :param filepath:
    :param content:
    :param mode:
    :param encoding:
    :return:
    """
    file_object = open(file=get_absolute_path(filepath), mode=mode, encoding=encoding)
    try:
        res = file_object.write(content)
        file_object.flush()
        return res
    finally:
        file_object.close()


def file_get_contents(filepath, mode='r', encoding='UTF-8'):
    """
    读取本地文件内容
    :param filepath:
    :param mode:
    :param encoding:
    :return:
    """
    file_object = open(file=get_absolute_path(filepath), mode=mode, encoding=encoding)
    try:
        all_the_text = file_object.read()
    finally:
        file_object.close()
    if all_the_text:
        return all_the_text
    else:
        return False


def get_list_value(item, key, default=None):
    """
    获取列表中的值
    :param item:
    :param key:
    :param default:
    :return:
    """
    if item and key <= len(item) and item[key] is not None:
        return item[key]
    return default


def get_value(result, name=None, default=None):
    """
    获取值【支持.操作符】
    :param result:
    :param name:
    :param default:
    :return:
    """
    value = result
    if name is None:
        return value
    if name:
        name = name.split('.')
        for val in name:
            if val in value:
                value = value[val]
            else:
                value = None
                break
    return default if value is None else value


def html_decode(content):
    """
    html解码
    :param content:
    :return:
    """
    return html.unescape(content)


def lists_column(lists, column_key=None, index_key=None):
    """
       返回输入字典中单个列的值
       :param lists:
       :param column_key:
       :param index_key:
       :return:
    """
    if isinstance(lists, list) is False:
        raise Exception('The data has to be list')
    result = None
    for item in lists:
        if isinstance(item, dict) is False:
            raise Exception('The item has to be dict')
        if column_key:
            if column_key in item:
                value = get_value(item, column_key)
            else:
                raise ValueError('column_key does not exist:%s' % column_key)
        if index_key:
            if index_key in item:
                key = get_value(item, index_key)
            else:
                raise ValueError('index_key does not exist:%s' % index_key)
        if 'value' in locals().keys() and 'key' in locals().keys():
            if not result:
                result = {}
            result[key] = value
            del key, value
        elif 'value' in locals().keys() or 'key' in locals().keys():
            if not result:
                result = []
            if 'value' in locals().keys():
                result.append(value)
                del value
            elif 'key' in locals().keys():
                result.append(key)
                del key
    return lists if not result and not column_key and not column_key else result


def is_json(content):
    """
    是否是json字符串
    :param content:
    :return:
    """
    try:
        json.loads(content)
    except Exception as e:
        return False
    return True


def bool_to_int(value):
    """
    bool转int
    :param value:
    :return:
    """
    if value is True or value:
        return 1
    else:
        return 0


def json_print(dicts):
    """
    输出json
    :param dicts:
    :return:
    """
    result = json.dumps(dicts, sort_keys=True, indent=4, separators=(',', ': '))
    print(result)


def convert(data):
    """
    数据格式转化
    :param data:
    :return:
    """
    if isinstance(data, bytes):
        return data.decode('ascii')
    if isinstance(data, dict):
        return dict(map(convert, data.items()))
    if isinstance(data, tuple):
        return map(convert, data)
    if isinstance(data, list):
        return list(map(convert, data))
    return data


def generate_random_str(random_length=16):
    """
    生成一个指定长度的随机字符串
    """
    random_str = ''
    base_str = 'ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghigklmnopqrstuvwxyz0123456789'
    length = len(base_str) - 1
    for i in range(random_length):
        random_str += base_str[random.randint(0, length)]
    return random_str


def value_of_empty(value):
    """
    判断值是否为空
    :param value:
    :return:
    """
    if value is None or value == '' or value is False or value == [] or value == {}:
        return True
    return False
