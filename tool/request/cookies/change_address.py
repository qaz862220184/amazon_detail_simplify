# -*- coding: UTF-8 -*-
import functools
import re
import random
import json
import time
import subprocess
import requests
import urllib3
import sys
sys.path.append('..')
sys.path.append('../..')
sys.path.append('../../..')
from lxml import etree
from requests import utils
from tool.config import Config
from common.helpers import get_value
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from tool.request.request_config import RequestParam
from tool.request.validate.captcha import ValidateCaptcha
from scrapy.http import HtmlResponse
from requests.cookies import RequestsCookieJar

"""
指纹标识
"""
ORIGIN_CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)


def retry(max_retries=3, delay=1):
    """
    装饰器：在函数抛出异常时进行重试。
    :param max_retries: 最大重试次数
    :param delay: 每次重试之间的延迟时间（秒）
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    # 尝试执行原函数
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f'change address is error!!! current is {attempt}')
                        time.sleep(delay)
                    else:
                        raise e
        return wrapper
    return decorator


class DESAdapter(HTTPAdapter):
    """
    指纹中间件
    """
    
    def __init__(self, *args, **kwargs):
        """
        A TransportAdapter that re-enables 3DES support in Requests.
        :param args: 
        :param kwargs: 
        """
        ciphers = ORIGIN_CIPHERS.split(':')
        random.shuffle(ciphers)
        ciphers = ':'.join(ciphers)
        self.CIPHERS = ciphers + ':!aNULL:!eNULL:!MD5'
        super().__init__(*args, **kwargs)
        
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=self.CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).init_poolmanager(*args, **kwargs)


class AmazonLocationSession(object):
    address_change_endpoint = (
        "/portal-migration/hz/glow/address-change?actionSource=glow"
    )
    csrf_token_endpoint = (
        "/portal-migration/hz/glow/get-rendered-address-selections?deviceType=desktop"
        "&pageType=Gateway&storeContext=NoStoreName&actionSource=desktop-modal"
    )
    accpt_cookie_endpoint = (
        "/privacyprefs/retail/v1/acceptall"
    )
    accept_cookie_form_id = 'sp-cc'
    SUCCESS_STATUS_CODE = [200]

    def __init__(self, country: str, zip_code: str, proxies=None):
        self.country = country
        self.zip_code = zip_code
        self.proxies = proxies
        self.session = requests.session()
        self.headers = RequestParam.get_headers(
            request_url=self.get_base_url(),
            platform=1,
        )

    @retry(max_retries=3, delay=1)
    def change_address(self, to_string=True):
        """
        Make start request to main Amazon country page.
        :param to_string:
        :return:
        """
        base_url = self.get_address_base_url()
        self.session.mount(base_url, DESAdapter())
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # 请求首页
        response = self._get(
            base_url,
            self.headers
        )
        cookie = response.cookies
        if response.status_code not in self.SUCCESS_STATUS_CODE:
            # 请求错误
            raise ValueError('First step Request failed：' + str(response.status_code))
        else:
            self._update_cookie(response)
        # TODO
        # with open('amazon_test.html', 'w') as f:
        #     f.write(response.text)

        # 解析和获取csrf-token
        csrf_token = self.parse_csrf_token(response)
        print({'csrf-token': csrf_token})
        # 接收cookie， 欧洲国家需要
        self.accept_cookie(response)
        # 设置邮编
        res = self.parse_cookies(csrf_token)
        if res:
            # 设置成功
            if self.session.cookies.get_dict():
                session_cookie = self.session.cookies
            else:
                session_cookie = cookie
            if to_string:
                session_cookie = session_cookie.get_dict()
                session_cookie = '; '.join([f"{key}={value}" for key, value in session_cookie.items()])
                return session_cookie
            else:
                return session_cookie

    def accept_cookie(self, response):
        """
        接收cookie
        :param response:
        :return:
        """
        payload = self._get_form_data(
            response,
            self.accept_cookie_form_id
        )
        if not payload:
            return False
        base_url = self.get_base_url()
        headers = self.headers
        headers['Accept'] = 'application/json'
        headers['Content-type'] = 'application/x-www-form-urlencoded'
        # 请求
        response2 = self.session.post(
            url=base_url + self.accpt_cookie_endpoint,
            headers=headers,
            data=payload,
            cookies=self._get_cookie(),
            proxies=self.proxies,
            verify=False,
        )
        if 'present' in response2.text:
            # 成功
            return True
        else:
            return False

    def parse_cookies(self, csrf_token):
        """
        Parse CSRF token from response and make request to change Amazon location.
        :param csrf_token:
        :return:
        """
        base_url = self.get_base_url()
        headers = self.headers
        payload = {
            'locationType': 'LOCATION_INPUT',
            'zipCode': self.zip_code.replace('+', ' '),
            'storeContext': 'generic',
            'deviceType': 'web',
            'pageType': 'Gateway',
            'actionSource': 'glow',
        }
        headers['anti-csrftoken-a2z'] = csrf_token
        headers['content-type'] = 'application/json'

        # 请求
        response = self.session.post(
            url=base_url + self.address_change_endpoint,
            headers=headers,
            data=json.dumps(payload),
            cookies=self._get_cookie(),
            proxies=self.proxies,
            verify=False
        )
        if 'isValidAddress' in response.text:
            # 成功
            self._update_cookie(response)
            return True
        else:
            # TODO: session 请求失败的话，使用curl尝试一下
            curl_command = [
                "curl", "-X", "POST",
                f"{base_url}{self.address_change_endpoint}",
                "-d", json.dumps(payload),
                "-i",
                "--insecure"  # 跳过 SSL 验证
            ]
            # 添加 headers
            for key, value in headers.items():
                curl_command.extend(["-H", f"{key}: {value}"])

            # 添加 cookies
            if self._get_cookie():
                cookie_string = "; ".join([f"{key}={value}" for key, value in self._get_cookie().items()])
                curl_command.extend(["--cookie", cookie_string])

            # 添加代理
            if self.proxies:
                curl_command.extend(["--proxy", self.proxies['http']])

            # 执行 curl 命令
            result = subprocess.run(curl_command, capture_output=True, text=True, encoding='latin1')
            curl_cookies = re.findall(r'set-cookie: (.*?);', result.stdout)
            cookie_jar = RequestsCookieJar()
            if curl_cookies:
                for cookie in curl_cookies:
                    key, value = cookie.split("=", 1)  # 以等号分隔，最多分割一次
                    cookie_jar.set(key, value)

            # 写入某些数据
            response = HtmlResponse(
                f"{base_url}{self.csrf_token_endpoint}",
                status=200,
                headers=headers,
                body=result.stdout,
                encoding='utf-8',
            )
            if 'isValidAddress' in response.text:
                # 成功
                response.cookies = cookie_jar
                self._update_cookie(response)
                return True
            else:
                return False

    def parse_csrf_token(self, response):
        """
        Parse ajax token from response.
        :param response:
        :return:
        """
        # 获取csrf-token增加重试
        for i in range(3):
            base_url = self.get_base_url()
            headers = self.headers
            headers = {
                **headers,
                'accept': 'text/html,*/*',
                'anti-csrftoken-a2z': self._get_ajax_token(response=response),
            }
            print({
                'url': base_url + self.csrf_token_endpoint,
                'headers': headers,
                'cookies': self._get_cookie(),
                'proxies': self.proxies,
            })
            response2 = requests.get(
                url=base_url + self.csrf_token_endpoint,
                headers=headers,
                cookies=self._get_cookie(),
                proxies=self.proxies,
                verify=False
            )
            if response2.status_code not in self.SUCCESS_STATUS_CODE:
                continue
            else:
                self._update_cookie(response2)

            csrf_token = self._get_csrf_token(response=response2)
            if csrf_token:
                return csrf_token

        # TODO: session 请求失败的话可以试一下使用curl请求
        base_url = self.get_base_url()
        headers = self.headers
        headers = {
            **headers,
            'Content-Type': 'text/html',
            'Content': 'text/html,*/*',
            'anti-csrftoken-a2z': self._get_ajax_token(response=response),
        }
        curl_command = [
            "curl", "-X", "GET",
            f"{base_url}{self.csrf_token_endpoint}",
            "-i",
            "--compressed",
            "--insecure"  # 跳过 SSL 验证
        ]
        # 添加 headers
        for key, value in headers.items():
            curl_command.extend(["-H", f"{key}: {value}"])

        # 添加 cookies
        if self._get_cookie():
            cookie_string = "; ".join([f"{key}={value}" for key, value in self._get_cookie().items()])
            curl_command.extend(["--cookie", cookie_string])

        # 添加代理
        if self.proxies:
            curl_command.extend(["--proxy", self.proxies['http']])

        # 执行 curl 命令
        result = subprocess.run(curl_command, capture_output=True, text=True, encoding='latin1')
        curl_cookies = re.findall(r'set-cookie: (.*?);', result.stdout)
        cookie_jar = RequestsCookieJar()
        if curl_cookies:
            for cookie in curl_cookies:
                key, value = cookie.split("=", 1)  # 以等号分隔，最多分割一次
                cookie_jar.set(key, value)
        response2 = HtmlResponse(
            f"{base_url}{self.csrf_token_endpoint}",
            status=200,
            headers=headers,
            body=result.stdout,
            encoding='utf-8',
        )
        response2.cookies = cookie_jar
        self._update_cookie(response2)

        csrf_token = self._get_csrf_token(response=response2)
        if csrf_token:
            return csrf_token

        raise ValueError('CSRF token not found')

    def get_base_url(self):
        """
        获取基础链接
        :return:
        """
        return 'https://' + self.get_country_value('domain')

    def get_address_base_url(self):
        """
        获取csrf基础链接
        :return:
        """
        language = self.get_country_value('language') if self.get_country_value('language') else ''
        return 'https://' + self.get_country_value('domain') + '/?language=' + language

    def get_country_value(self, name=None, default=None):
        """
        获取国家对应参数
        :param name:
        :param default:
        :return:
        """
        country_config = Config.get_country()
        if self.country in country_config:
            return get_value(country_config[self.country], name, default)
        else:
            raise ValueError('Country code error!')

    def _get_cookie(self):
        """
        获取当前cookie
        :return:
        """
        return self.session.cookies.get_dict()

    def _update_cookie(self, response):
        """
        更新cookie
        :param response:
        :return:
        """
        if response.cookies:
            cookie_dict = requests.utils.dict_from_cookiejar(response.cookies)
            self.session.cookies.update(cookie_dict)

    def _get(self, url, headers, cookie=None):
        """
        get请求【加上验证码验证】
        :param url:
        :param headers:
        :param cookie:
        :return:
        """
        response = self.session.get(
            url=url,
            headers=headers,
            proxies=self.proxies,
            cookies=cookie,
            timeout=20
        )
        if ValidateCaptcha.is_verification(response.text):
            # 出现验证码，说明需要验证
            validate = ValidateCaptcha(
                response.text,
                url,
                cookie,
                self.proxies,
            )
            submit_url = validate.get_submit_url()
            response = self.session.get(
                url=submit_url,
                headers=headers,
                proxies=self.proxies,
                verify=False
            )

        return response

    @classmethod
    def _get_ajax_token(cls, response):
        """
        Extract ajax token from response
        :param response:
        :return:
        """
        content = etree.HTML(response.text)
        data = content.xpath("//input[@id='glowValidationToken']/@value")
        if not data:
            raise ValueError('Invalid page content')
        return str(data[0])

    @classmethod
    def _get_csrf_token(cls, response):
        """
        Extract CSRF token from
        :param response:
        :return:
        """
        try:
            csrf_token = re.search(r'CSRF_TOKEN : \"([\S]+)\",', response.text).group(1)
        except AttributeError:
            csrf_token = None
        return csrf_token

    @classmethod
    def _get_form_data(cls, response, form_id='sp-cc'):
        """
        获取form表单数据
        :param response:
        :param form_id:
        :return:
        """
        content = etree.HTML(response.text)
        res = content.xpath(f'//form[@id="{form_id}"]//input')
        data = {}
        for input_html in res:
            name = input_html.xpath('@name')[0]
            value = input_html.xpath('@value')[0]
            data[name] = value
        return data


if __name__ == '__main__':
    amazon = AmazonLocationSession('JP', '160-0022', {'http': 'socks5h://192.168.2.84:7157'})
    # amazon = AmazonLocationSession('US', '10017', {'http': 'socks5h://192.168.2.84:7151'})
    # amazon = AmazonLocationSession('DE', '10115', {'http': 'socks5h://192.168.2.84:7165'})
    # amazon = AmazonLocationSession('FR', '75015', {'http': 'socks5h://192.168.2.84:7164'})
    # amazon = AmazonLocationSession('GB', 'WC1N 3AX', {'http': 'socks5h://192.168.2.84:7163'})

    cookies = amazon.change_address()
    print('-' * 200)
    print(cookies)

