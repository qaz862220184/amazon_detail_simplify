import random
from user_agents import parse
from common.helpers import get_value
from common.utils.sundry_utils import UrlParse
from common.exceptions.exception import ConfiguredException
from fake_useragent import UserAgent

ua = UserAgent()


class UserAgent(object):
    # browser
    BROWSER_FIREFOX = 'firefox'
    BROWSER_CHROME = 'chrome'
    BROWSER_SAFARI = 'safari'
    BROWSERS = [
        BROWSER_FIREFOX,
        BROWSER_CHROME,
        BROWSER_SAFARI
    ]
    # os
    OS_MACOS = 'macOs'
    OS_WINDOWS = 'windows'
    OS_IOS = 'ios'
    OS_ANDROID = 'android'
    OS = [
        OS_MACOS,
        OS_WINDOWS,
        OS_IOS,
        OS_ANDROID
    ]
    # 平台 platform
    PLATFORM_PC = 'pc'
    PLATFORM_PHONE = 'phone'
    PLATFORM = [PLATFORM_PC, PLATFORM_PHONE]

    def __init__(
            self,
            user_agent,
            se_platform_version=None,
            se_platform=None,
            se_user_agent=None
    ):
        # 解析ua
        self.user_agent = user_agent
        self.user_agent_obj = parse(
            self.user_agent
        )
        self.browser, self.os, self.platform = self.__init()
        # se信息赋值
        self.se_platform_version = se_platform_version
        self.se_platform = se_platform
        self.se_user_agent = se_user_agent

    def get_browser(self):
        return self.browser

    def get_os(self):
        return self.os

    def get_platform(self):
        return self.platform

    def get_se_platform_version(self):
        return self.se_platform_version

    def get_se_platform(self):
        if not self.se_platform:
            if self.browser in [self.BROWSER_CHROME, self.BROWSER_SAFARI]:
                # 谷歌或苹果浏览器
                self.se_platform = self.os
        return self.se_platform

    def get_se_user_agent(self):
        if not self.se_user_agent:
            if self.browser in [self.BROWSER_CHROME, self.BROWSER_SAFARI] and self.platform == self.PLATFORM_PC:
                # pc 并且 谷歌或苹果浏览器
                browser_v = self.user_agent_obj.browser.version[0]
                if self.browser == self.BROWSER_CHROME:
                    # 谷歌浏览器
                    se_ua = '"Chromium";v="{v}", "Not A(Brand";v="24", "Google Chrome";v="{v}"'
                    self.se_user_agent = se_ua.format(v=browser_v)
        return self.se_user_agent

    def __str__(self):
        return self.user_agent

    def __init(self):
        """
        解析用户浏览器标识
        :return:
        """
        user_agent_obj = self.user_agent_obj
        # 浏览器类型
        browser_family = str(user_agent_obj.browser.family).lower()
        browser = browser_family
        for br in self.BROWSERS:
            if br in browser_family:
                browser = br
                break
        # 操作系统类型
        os_family = str(user_agent_obj.os.family).lower()
        os_family = os_family.replace(' ', '')
        os = os_family
        for os_str in self.OS:
            os_str_lower = str(os_str).lower()
            if os_str_lower in os_family:
                os = os_str
                break
        # 平台类型
        platform = self.PLATFORM_PC
        if os in [self.OS_IOS, self.OS_ANDROID]:
            platform = self.PLATFORM_PHONE

        return browser, os, platform


class RequestHeaders:
    # 公共头部参数
    DEFAULT_HEADERS = {
        "sec-fetch-dest": "document",
        "upgrade-insecure-requests": "1",
        "sec-ch-ua-mobile": "?0",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
    }

    def __init__(
            self,
            user_agent,
            se_user_agent=None,
            header=None,
            **kwargs
    ):
        se_user_agent = {} if not se_user_agent else se_user_agent
        self.user_agent = UserAgent(
            user_agent=user_agent,
            **se_user_agent
        )
        self.header = {} if not header else header
        self.item = kwargs

    def get_headers(self):
        """
        获取头部信息
        :return:
        """
        # 默认头部信息
        default_header = self.DEFAULT_HEADERS.copy()
        # ua头部信息
        ua_header = {
            'sec-ch-ua': self.get_user_agent().get_se_user_agent(),
            'sec-ch-ua-platform': self.get_user_agent().get_se_platform(),
            'user-agent': self.get_user_agent().user_agent,
        }
        # 指定的头部信息
        custom_header = self.header
        return {**default_header, **ua_header, **custom_header}

    def get_item(self, name=None, default=None):
        """
        获取item参数
        :param name:
        :param default:
        :return:
        """
        return get_value(
            result=self.item,
            name=name,
            default=default
        )

    def get_user_agent(self):
        """
        获取用户ua
        :return:
        """
        return self.user_agent


class RequestParam:
    # 自定义头部参数
    HEADERS = [
        {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_2_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="89", "Chromium";v="89", ";Not A Brand";v="99"',
                'se_platform': 'macOS',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36 Edg/85.0.564.70',
            'se_user_agent': {
                'se_user_agent': 'Microsoft Edge;v="85", "Chromium";v="85", ";Not A Brand";v="99"',
                'se_platform': 'Windows',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'accept-language': 'en-US',
                'accept-encoding': 'en-US,en;q=0.9,fr;q=0.5',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="55", "Chromium";v="55", ";Not A Brand";v="99"',
                'se_platform': 'Windows',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.6',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Windows NT 6.1; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"',
                'se_platform': 'Windows',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9,de;q=0.5',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="90", "Chromium";v="90", ";Not A Brand";v="99"',
                'se_platform': 'macOS',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9,de;q=0.8',
                'accept-encoding': 'gzip, deflate',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81',
            'se_user_agent': {
                'se_user_agent': 'Microsoft Edge;v="88", "Chromium";v="88", ";Not A Brand";v="99"',
                'se_platform': 'Windows',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'accept-language': 'en-US,it;q=0.6',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="86", "Chromium";v="86", ";Not A Brand";v="99"',
                'se_platform': 'Windows',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'accept-language': 'en-US,fr;q=0.8',
                'accept-encoding': 'gzip, deflate',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="83", "Chromium";v="83", ";Not A Brand";v="99"',
                'se_platform': 'Windows',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'accept-language': 'en-US,de;q=0.7',
                'accept-encoding': 'gzip, deflate',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36',
            'se_user_agent': {
                'se_user_agent': 'Google Chrome;v="84", "Chromium";v="84", ";Not A Brand";v="99"',
                'se_platform': 'macOS',
            },
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'accept-language': 'en-US,en;q=0.5',
                'accept-encoding': 'gzip, deflate',
            },
        },
    ]
    HEADERS_MOBILE = [
        {
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'mozilla/5.0 (linux; android 12; harmonyos; jad-al00; hmscore 6.8.0.332) applewebkit/537.36 (khtml, like gecko) chrome/99.0.4844.88 huaweibrowser/13.0.0.310 mobile safari/537.36',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Linux; U; Android 9; zh-CN; LON-AL00 Build/HUAWEILON-AL00) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/57.0.2987.108 UCBrowser/12.9.0.1070 Mobile Safari/537.36',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (Linux; Android 4.2.1; M040 Build/JOP40D) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.59 Mobile Safari/537.36',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
        {
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 7_0_4 like Mac OS X) AppleWebKit/537.51.1 (KHTML, like Gecko) CriOS/31.0.1650.18 Mobile/11B554a Safari/8536.25',
            'header': {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'accept-language': 'en-US',
                'accept-encoding': 'gzip',
            },
        },
    ]
    MOBILE_RESOLUTION = [
        {'width': 430, 'height': 932},
        {'width': 390, 'height': 844},
        {'width': 414, 'height': 896},
        {'width': 412, 'height': 915},
        {'width': 360, 'height': 780},
        {'width': 360, 'height': 800},
        {'width': 393, 'height': 852},
        {'width': 428, 'height': 923},
    ]
    @classmethod
    def get_headers(cls, header=None, cookies=None, request_url=None, platform=2):
        """
        获取真实的浏览器头（完全模拟）
        :param header:
        :param cookies:
        :param request_url:
        :param platform:
        :return:
        """
        headers_data = cls.HEADERS_MOBILE
        item = random.choice(headers_data)
        if platform == 1:
            item = {
                'user_agent': ua.chrome
            }
        # ua
        if 'user_agent' not in item:
            raise ConfiguredException('The user_agent does not exist')
        user_agent = item['user_agent']
        # 头部参数补充
        header = {} if not header else header
        if 'header' in item and isinstance(item, dict):
            header = {**item['header'], **header}
        # se ua
        se_user_agent = {} if 'se_user_agent' not in item else item['se_user_agent']
        request_headers = RequestHeaders(
            user_agent=user_agent,
            se_user_agent=se_user_agent,
            header=header
        )
        headers = request_headers.get_headers()

        # cookie
        if cookies:
            if isinstance(cookies, dict):
                arr = []
                for key in cookies:
                    arr.append(f"{key}={cookies[key]}")
                cookies = "; ".join(arr)
            headers['cookie'] = cookies

        # host
        if request_url:
            url_parse = UrlParse(request_url)
            domain = url_parse.get_domain()
            if domain:
                headers['host'] = domain

        return headers


if __name__ == '__main__':
    import json
    res = json.dumps(RequestParam.get_headers(
        request_url='https://www.baidu.com',
        cookies={'name': 'Mr Ye', 'age': 18, 'token': 'abcdef'}
    ), sort_keys=True, indent=4, separators=(',', ':'))
    print(res)
