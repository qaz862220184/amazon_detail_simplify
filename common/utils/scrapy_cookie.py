from common.helpers import get_absolute_path, file_get_contents, file_put_contents, get_value
from common.utils.date_time import ScrapyDateTimeManage
from common.utils.sundry_utils import UrlParse
import time
import json
import os


def domain_contain(page_domain, cookie_domain):
    """
    判断域名是否包含
    :param page_domain:
    :param cookie_domain:
    :return:
    """
    cookie_domain = str(cookie_domain)
    if cookie_domain.startswith('.'):
        cookie_domain = cookie_domain[1:]
    if cookie_domain in page_domain:
        return True
    else:
        return False


class ScrapyCookie(object):
    # 源字段: 别名
    COOKIE_FIELD_CONVERSION = {
        'name': 'name',
        'value': 'value',
        'max-age': 'max-age',
        'expires': 'expires',
        'domain': 'domain',
        'path': 'path',
        'version': 'version',
    }

    def __init__(self, url=None, is_filter=True, **kwargs):
        self.url = url
        url_parse = UrlParse(
            url=self.url
        )
        item = {}
        if is_filter:
            # 过滤
            for field in kwargs:
                lower_field = str(field).lower()
                if lower_field in self.COOKIE_FIELD_CONVERSION:
                    new_field = self.COOKIE_FIELD_CONVERSION[lower_field]
                    item[new_field] = kwargs[field]
            # 补充字段
            if 'domain' in item and item['domain']:
                domain = item['domain']
            else:
                domain = url_parse.get_domain()
            item['domain'] = domain
            item['scheme'] = url_parse.get_scheme()
            item['port'] = url_parse.get_port()
        else:
            # 不过滤
            item = kwargs

        # 判断重要字段是否存在
        if 'name' not in item or 'value' not in item:
            raise ValueError('The name or value in the cookie must be set')
        self.url_parse = url_parse
        self.item = item

    def get_name(self):
        """
        获取cookie名称
        :return:
        """
        return self.get_item('name')

    def get_value(self):
        """
        获取cookie值
        :return:
        """
        return self.get_item('value')

    def get_domain(self):
        """
        获取域名
        :return:
        """
        return self.get_item('domain')

    def get_item(self, name=None, default=None):
        """
        获取值
        :param name:
        :param default:
        :return:
        """
        return get_value(
            result=self.item,
            name=name,
            default=default
        )

    def get_expires_by_timestamp(self):
        """
        获取过期的时间戳
        :return:
        """
        timestamp = 0
        expires = self.get_item('expires')
        if expires:
            time_array = time.strptime(
                expires,
                '%a, %d-%b-%Y %H:%M:%S GMT'
            )
            try:
                timestamp = time.mktime(time_array)
            except OverflowError:
                timestamp = -1
        return timestamp

    def is_available(self):
        """
        当前cookie是否可用
        :return:
        """
        if (
                (self.is_expired() is False)
                and (self.is_scope() is True)
                and (self.is_homologous() is True)
        ):
            # 可用
            return True
        else:
            # 不可用
            return False

    def is_homologous(self):
        """
        是否同源
        :return:
        """
        if (
                (self.url_parse.get_port() == self.get_item('port'))
                and (self.url_parse.get_scheme() == self.get_item('scheme'))
                and domain_contain(self.url_parse.get_domain(), self.get_domain())
        ):
            return True
        else:
            return False

    def is_expired(self):
        """
        是否过期
        :return:
        """
        now_timestamp = ScrapyDateTimeManage.date_time().timestamp()
        timestamp = self.get_expires_by_timestamp()
        if timestamp == 0 or timestamp > now_timestamp:
            # 未过期
            return False
        else:
            # 已过期
            return True

    def is_scope(self):
        """
        是否存在域
        :return:
        """
        path = self.get_item('path')
        if not path or path in self.url:
            # 存在域中
            return True
        return False

    def get(self):
        """
        获取当前cookie的字典
        :return:
        """
        fields = dict(
            [val, key] for key, val in self.COOKIE_FIELD_CONVERSION.items()
        )
        # 生成新cookie
        new_cookies = {}
        for field in self.get_item():
            if field in fields:
                new_field = fields[field]
            else:
                new_field = field
            new_cookies[new_field] = self.get_item(field)
        return new_cookies

    def __str__(self):
        return json.dumps(self.get())

    def __repr__(self):
        return "<Cookie %s for %s>" % (self.get_name(), self.get_value())


class ScrapyCookieManage(object):
    def __init__(self, url, path='/runtime/scrapy/scrapy_cookies.json'):
        self.url = url
        self.url_parse = UrlParse(
            url=url
        )
        self.path = path

    def get_cookies_by_dict(self):
        """
        获取字段cookie
        :return:
        """
        cookies = self.get_cookies()
        result = {}
        for cookie in cookies:
            result[cookie.get_name()] = cookie.get_value()
        return result

    def get_cookies(self, is_obj=True):
        """
        获取cookie
        :param is_obj:
        :return:
        """
        current_domain = self.url_parse.get_domain()
        all_cookies = self.__read_cookie()
        new_cookies = []
        for domain in all_cookies:
            cookies = all_cookies[domain]
            if domain_contain(current_domain, domain):
                # 同域
                for cookie in cookies:
                    scrapy_cookie = self.__make_scrapy_cookie(
                        cookie=cookie,
                        is_filter=False
                    )
                    if scrapy_cookie.is_available() is False:
                        # cookie不可用
                        continue
                    if is_obj is False:
                        scrapy_cookie = scrapy_cookie.get()
                    new_cookies.append(
                        scrapy_cookie
                    )
        return new_cookies

    def set_cookies(self, cookies, type=0):
        """
        设置cookie
        :param cookies:
        :param type:
        :return:
        """
        if type == 0:
            cookies = self.__get_scrapy_cookie(
                cookies=cookies
            )
        else:
            cookies = self.__get_request_cookie(
                cookies=cookies
            )
        return self.__put_cookie(
            cookies=cookies
        )

    def clear_cookies(self):
        """
        清空当前cookie
        :return:
        """
        all_cookies = self.__read_cookie()
        all_cookies2 = all_cookies.copy()
        current_domain = self.url_parse.get_domain()
        for domain in all_cookies2:
            if domain_contain(current_domain, domain):
                # 删除包含的cookie
                del all_cookies[domain]

        # cookie存储路径
        path, dir_name = self.__get_storage_path()

        return file_put_contents(
            filepath=path,
            content=json.dumps(all_cookies),
            mode='w'
        )

    def __make_scrapy_cookie(self, cookie, is_filter=True):
        """
        创建cookie对象
        :param cookie:
        :return:
        """
        return ScrapyCookie(
            url=self.url,
            is_filter=is_filter,
            **cookie
        )

    def __read_cookie(self):
        """
        读取cookie
        :return:
        """
        path, dir_name = self.__get_storage_path()
        if os.path.exists(path) is False:
            return {}
        all_cookies = file_get_contents(
            filepath='runtime/scrapy/scrapy_cookies.json'
        )
        try:
            res = json.loads(all_cookies)
        except TypeError:
            res = {}
        return res

    def __put_cookie(self, cookies):
        """
        写入cookie
        :param cookies:
        :return:
        """
        # 格式化cookie
        all_cookies = self.__read_cookie()
        for cookie in cookies:
            domain = cookie.get_domain()
            if domain in all_cookies:
                # 说明存在旧cookie，需要比较
                i = 0
                for all_cookie in all_cookies[domain]:
                    if all_cookie['name'] == cookie.get_name():
                        del all_cookies[domain][i]
                        break
                    i += 1

            if cookie.is_available():
                if domain not in all_cookies:
                    all_cookies[domain] = []
                all_cookies[domain].append(
                    cookie.get()
                )

        # cookie存储路径
        path, dir_name = self.__get_storage_path()

        return file_put_contents(
            filepath=path,
            content=json.dumps(all_cookies),
            mode='w'
        )

    def __get_storage_path(self):
        """
        获取缓存路径
        :return:
        """
        path = get_absolute_path(self.path)
        dir_name = os.path.dirname(
            path
        )
        if os.path.exists(dir_name) is False:
            # 目录不存在
            os.makedirs(dir_name, exist_ok=True)
        return path, dir_name

    def __get_cookie(self, cookies):
        """
        获取普通cookie
        :param cookies:
        :return:
        """
        # 去重
        cookie_dicts = {}
        for cookie in cookies:
            name = cookie['name']
            if name in cookie_dicts:
                # 存在旧
                old_cookie = cookie_dicts[name]
                if (
                        ('domain' in old_cookie)
                        and (old_cookie['domain'])
                        and (domain_contain(self.url_parse.get_domain(), old_cookie['domain']))
                ):
                    cookie = old_cookie
            cookie_dicts[str(name).lower()] = cookie

        # 创建cookie对象
        new_cookies = []
        for name in cookie_dicts:
            scrapy_cookie = self.__make_scrapy_cookie(
                cookie=cookie_dicts[name]
            )
            new_cookies.append(scrapy_cookie)
        return new_cookies

    def __get_request_cookie(self, cookies):
        """
        获取request请求cookie
        :param cookies:
        :return:
        """
        # response.cookies
        new_cookies = []
        all_cookies = cookies.__dict__['_cookies']
        for domain in all_cookies:
            scope_cookies = all_cookies[domain]
            for scope in scope_cookies:
                for name in scope_cookies[scope]:
                    # from http.cookiejar import Cookie
                    cookie = scope_cookies[scope][name]
                    new_cookies.append(
                        {
                            'name': name,
                            'value': cookie.value,
                            'version': cookie.version,
                            'domain': cookie.domain,
                            'path': cookie.path,
                            'expires': time.strftime('%a, %d-%b-%Y %H:%M:%S GMT', time.localtime(cookie.expires)),
                        }
                    )
        return self.__get_cookie(
            cookies=new_cookies
        )

    def __get_scrapy_cookie(self, cookies):
        """
        传入scrapy的response对象，其中的cookie
        :param cookies
        :return:
        """
        return self.__get_cookie(
            self.__convert_cookies_to_dict(
                cookies=cookies
            )
        )

    @classmethod
    def __convert_cookies_to_dict(cls, cookies, is_decode=True):
        result = []
        for cookie in cookies:
            if is_decode:
                # 转码
                cookie = cookie.decode()
            item = [(str(i.split('=', 1)[0].replace(' ', '')).lower(), i.split('=', 1)[1]) for i
                    in cookie.split(';') if '=' in i]
            name, value = item.pop(0)
            item.append(("name", name))
            item.append(("value", value))
            item = dict(item)
            # 放入结果集中
            result.append(item)
        return result
