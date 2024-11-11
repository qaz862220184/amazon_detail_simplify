import requests
from common.settings import PROXY_POOL
from common.helpers import get_value
from urllib.parse import urlencode


class Proxy:
    def __init__(self, params=None):
        self.params = params

    def get_scrapy_proxy(self):
        """
        获取scrapy格式的代理
        :return:
        """
        proxys = None
        if self.is_success():
            type = 'https' if self.get_https() else 'http'
            proxys = f"{type}://{self.get_proxy()}"
        return proxys

    def get_check_count(self):
        return self.__get(
            name='check_count'
        )

    def get_fail_count(self):
        return self.__get(
            name='fail_count'
        )

    def get_https(self):
        return self.__get(
            name='https'
        )

    def get_last_time(self):
        return self.__get(
            name='last_time'
        )

    def get_proxy(self):
        return self.__get(
            name='proxy'
        )

    def is_success(self):
        """
        是否成功
        :return:
        """
        if self.__get('proxy'):
            return True
        return False

    def __get(self, name=None, default=None):
        """
        获取值
        :param name:
        :param default:
        :return:
        """
        return get_value(
            result=self.params,
            name=name,
            default=default
        )

    def __str__(self):
        type = 'https' if self.get_https() else 'http'
        return f'<proxy {type} {self.get_proxy()}>'


class ProxyPool:

    @classmethod
    def get_available(cls, retry_count=5):
        """
        获取可用的代理
        :param retry_count:
        :return:
        """
        while retry_count > 0:
            proxy1 = cls.get()
            if proxy1.is_success():
                return proxy1
            else:
                retry_count -= 1
        return None

    @classmethod
    def get(cls, type=None):
        """
        获取代理
        :param type:
        :return:
        """
        params = {}
        if type:
            params['type'] = type
        res = cls.request(
            uri='get',
            **params
        )
        return Proxy(res)

    @classmethod
    def delete(cls, proxy1):
        """
        删除代理
        :param proxy1:
        :return:
        """
        params = {'proxy': proxy1}
        res = cls.request(
            uri='delete',
            **params
        )
        if 'src' in res:
            status = res['src']
            return True if status == 1 else False
        return False

    @classmethod
    def pop(cls, type=None):
        """
        获取并删除代理
        :param type:
        :return:
        """
        params = {}
        if type:
            params['type'] = type
        res = cls.request(
            uri='pop',
            **params
        )
        return Proxy(res)

    @classmethod
    def all(cls, type=None):
        """
        获取所有代理
        :param type:
        :return:
        """
        params = {}
        if type:
            params['type'] = type
        res = cls.request(
            uri='all',
            **params
        )
        result = []
        if isinstance(res, list):
            for item in res:
                result.append(Proxy(item))
        return result

    @classmethod
    def count(cls):
        """
        获取个数
        :return:
        """
        res = cls.request(
            uri='count'
        )
        if 'count' in res:
            return res
        return False

    @classmethod
    def request(cls, uri, **params):
        """
        请求
        :param uri:
        :param params:
        :return:
        """
        api = cls.__get_conf('api')
        if str(uri).startswith('/') is False:
            uri = '/' + uri
        url = api + uri
        # 参数
        if params:
            param = urlencode(params)
            url = url + '?' + param
        response = requests.get(
            url=url
        )
        return response.json()

    @classmethod
    def __get_conf(cls, name=None, default=None):
        """
        获取配置
        :param name:
        :param default:
        :return:
        """
        conf = PROXY_POOL
        return get_value(
            result=conf,
            name=name,
            default=default
        )


if __name__ == '__main__':
    proxy = ProxyPool.get_available()
    print(proxy)
