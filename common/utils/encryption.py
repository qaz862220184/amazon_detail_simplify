import hashlib
import base64
import json
from collections.abc import Iterable
from common.settings import API_CONF


class Md5Encrytion:

    @classmethod
    def md5(cls):
        return hashlib.md5()

    @classmethod
    def md5_upper32(cls, content):
        md5 = cls.md5()
        md5.update(content.encode("utf-8"))
        return md5.hexdigest().upper()

    @classmethod
    def md5_upper16(cls, content):
        md5 = cls.md5()
        md5.update(content.encode("utf-8"))
        return (md5.hexdigest())[8:-8].upper()

    @classmethod
    def md5_lower32(cls, content):
        md5 = cls.md5()
        md5.update(content.encode("utf-8"))
        return (md5.hexdigest()).lower()

    @classmethod
    def md5_lower16(cls, content):
        md5 = cls.md5()
        md5.update(content.encode("utf-8"))
        return (md5.hexdigest())[8:-8].lower()


class Base64Encrytion:
    """
    base64
    """

    @classmethod
    def _to_format(cls, string):
        """
        格式化
        :param string:
        :return:
        """
        if not string:
            return None
        if isinstance(string, str):
            res = string.encode()
        elif isinstance(string, bytes):
            res = string
        else:
            raise Exception('Wrong encoding type')
        return res

    @classmethod
    def encode(cls, string):
        """
        编码
        :param string:
        :return:
        """
        res = cls._to_format(string)
        if not res:
            return res
        return base64.b64encode(res).decode('ascii')

    @classmethod
    def decode(cls, string):
        """
        解码
        :param string:
        :return:
        """
        res = cls._to_format(string)
        if not res:
            return res
        return base64.b64decode(res).decode('ascii')


class ApiSign:
    API_KEY = API_CONF['apikey']

    @classmethod
    def ver_sign(cls, params: dict) -> bool:
        """
        验证签名
        :param params:
        :return:
        """
        if 'sign' not in params:
            return False
        sign = params['sign']
        del params['sign']
        if sign == cls.create_sign(params):
            return True
        else:
            return False

    @classmethod
    def create_sign(cls, params: dict):
        """
        生成api秘钥
        :param params:
        :return:
        """
        arr = []
        for tup in sorted(params.items(), key=lambda params: params[0]):
            name, value = tup
            if isinstance(value, Iterable) and not isinstance(value, str):
                value = Base64Encrytion.encode(json.dumps(value, separators=(',', ':'), ensure_ascii=False))
            if value is None:
                value = ''
            arr.append(f"{name}={value}")
        signstr = "&".join(arr) + '&api_key=' + cls.API_KEY
        return Md5Encrytion.md5_lower32(signstr)

    @classmethod
    def set_api_key(cls, api_key):
        cls.API_KEY = api_key
