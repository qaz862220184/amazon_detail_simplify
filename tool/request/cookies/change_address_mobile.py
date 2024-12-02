# -*- coding: UTF-8 -*-
import re
import random
import json
import requests
import urllib3
from lxml import etree
from requests import utils
from tool.config import Config
from common.helpers import get_value
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context
from tool.request.request_config import RequestParam
from tool.request.validate.captcha import ValidateCaptcha

"""
指纹标识
"""
ORIGIN_CIPHERS = (
    'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:RSA+3DES:!aNULL:'
    '!eNULL:!MD5'
)


class DESAdapter(HTTPAdapter):
    """
    指纹中间件
    """

    def __init__(self, *args, **kwargs):
        """
        A TransportAdapter that re-enables 3DES support in Requests.
        """
        ciphers = ORIGIN_CIPHERS.split(':')
        random.shuffle(ciphers)
        ciphers = ':'.join(ciphers)
        self.CIPHERS = ciphers + ':!aNULL:!eNULL:!MD5'
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context(ciphers=self.CIPHERS)
        kwargs['ssl_context'] = context
        return super(DESAdapter, self).init_poolmanager(* args, ** kwargs)


class AmazonLocationSession:
    address_change_endpoint = (
        "/portal-migration/hz/glow/address-change?actionSource=glow"
    )
    csrf_token_endpoint = (
        "/portal-migration/hz/glow/get-rendered-address-selections?&deviceType=mobile"
        "&pageType=gateway-phone-web&actionSource=mobile-web-subnav&storeContext=NoStoreName"
    )
    accpt_cookie_endpoint = (
        "/privacyprefs/retail/v1/acceptall"
    )
    accept_cookie_form_id = 'sp-cc'
    SUCCESS_STATUS_CODE = [200]

    def __init__(self, country: str, zip_code: str, proxies=None):
        self.country = country.upper()
        self.zip_code = zip_code
        self.proxies = proxies
        self.session = requests.session()
        self.headers = RequestParam.get_headers(
            request_url=self.get_base_url()
        )

    def change_address(self, to_dict=True):
        """
        Make start request to main Amazon country page.
        :param to_dict:
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

        # 解析和获取csrf-token
        csrf_token = self.parse_csrf_token(response)
        # 接受cookie协议【欧洲国家需要】
        self.accept_cookie(response)
        # 设置邮编
        res = self.parse_cookies(csrf_token)
        if res:
            # 设置成功
            if self.session.cookies.get_dict():
                session_cookie = self.session.cookies
            else:
                session_cookie = cookie
            if to_dict:
                # TODO 这里需要对cookie进行进一步的处理
                session_cookie = session_cookie.get_dict()
                session_cookie = '; '.join([f"{key}={value}" for key, value in session_cookie.items()])
                return session_cookie
            else:
                return session_cookie
        else:
            return False

    def parse_csrf_token(self, response):
        """
        Parse ajax token from response.
        """
        # 获取csrf-token增加重试
        for i in range(3):
            base_url = self.get_base_url()
            headers = self.headers
            headers = {
                **headers,
                'anti-csrftoken-a2z': self._get_ajax_token(response=response)
            }
            response2 = self.session.get(
                url=base_url + self.csrf_token_endpoint,
                headers=headers,
                cookies=self._get_cookie(),
                proxies=self.proxies,
                verify=False
            )
            if response2.status_code not in self.SUCCESS_STATUS_CODE:
                continue
                # raise ValueError('Second step Request failed：' + str(response2.status_code))
            else:
                self._update_cookie(response2)

            csrf_token = self._get_csrf_token(response=response2)
            if csrf_token:
                return csrf_token
        raise ValueError("CSRF token not found")

    def accept_cookie(self, response):
        """
        接受cookie
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
            self._update_cookie(response2)
            return True
        else:
            return False

    def parse_cookies(self, csrf_token):
        """
        Parse CSRF token from response and make request to change Amazon location.
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
            verify=False,
        )
        if 'isValidAddress' in response.text:
            # 成功
            self._update_cookie(response)
            return True
        else:
            return False

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
        获取国家对应的参数
        :return:
        """
        country_config = Config.get_country()
        if self.country in country_config:
            return get_value(country_config[self.country], name, default)
        else:
            raise ValueError('Country code error')

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
            cookies=cookie
        )
        if ValidateCaptcha.is_verification(response.text):
            # 出现验证码，说明需要验证
            validate = ValidateCaptcha(
                response.text,
                url,
                cookie,
                self.proxies
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
        Extract ajax token from response.
        """
        content = etree.HTML(response.text)
        data = content.xpath("//input[@id='glowValidationToken']/@value")
        if not data:
            raise ValueError("Invalid page content")
        return str(data[0])

    @classmethod
    def _get_csrf_token(cls, response):
        """
        Extract CSRF token from response.
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
    amazon = AmazonLocationSession('JP', '160-0022', {'https': 'socks5h://localhost:7157'})
    cookies = amazon.change_address()
    print('-' * 200)
    print(cookies)
