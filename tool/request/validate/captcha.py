#!/usr/bin/python
# -*- coding: UTF-8 -*-
import requests
import random
import time
import os
import urllib3
from common.helpers import get_absolute_path, get_list_value, file_put_contents
from common.utils.encryption import Md5Encrytion
from amazoncaptcha import AmazonCaptcha
from lxml import etree
from urllib.parse import urlparse, urlencode
from common.core.downloader.headers.request_headers import RequestParam


class SourceDownload:
    """
    资源下载
    sample：https://images-na.ssl-images-amazon.com/captcha/usvmgloq/Captcha_chxgjzwmbv.jpg
    """

    def __init__(self, root_path=None):
        """
        初始化
        :param root_path:
        """
        if not root_path:
            root_path = get_absolute_path('') + '/runtime/temp/'
        else:
            root_path = get_absolute_path(root_path)
        if os.path.isdir(root_path) is False:
            # 创建
            os.makedirs(root_path)
        self.root_path = root_path
        self.default_ext = 'png'

    def download(self, url, filename=None):
        """
        下载
        :param url:
        :param filename:
        :return:
        """
        source = self._get_source(url)
        if not source:
            return None
        content, ext, file_md5 = source
        # 文件名称
        if not filename:
            filename = f"{file_md5}.{ext}"
        elif '.' not in filename:
            filename = f"{filename}.{ext}"
        # 绝对路径
        absolute_path = f"{self.root_path}{filename}"
        relative_path = f'runtime/temp/{filename}'
        file_put_contents(relative_path, content, 'wb', None)

        return absolute_path

    def _get_source(self, url):
        """
        获取资源
        :param url:
        :return:
        """
        if not url:
            return None
        try:
            response = SourceDownload.get(url, )
        except Exception:
            return None
        # 响应结果
        content = response.content
        # 解析响应头
        if 'Content-Type' in response.headers:
            content_type = response.headers['Content-Type']
            ext = get_list_value(content_type.split('/'), 1, self.default_ext)
        else:
            ext = self.default_ext

        return content, ext, self._get_file_md5(response.text)

    def _get_file_md5(self, source):
        """
        获取文件md5
        :param source:
        :return:
        """
        try:
            md5 = Md5Encrytion.md5_lower32(source)
        except Exception:
            md5 = Md5Encrytion.md5_lower32(f"{time.time()}-{random.random()}")
        return md5

    @classmethod
    def get(cls, url, headers=None, proxies=None, timeout=15):
        # 避免https报错
        urllib3.disable_warnings()
        if headers is None:
            headers = RequestParam.get_headers()
        return requests.get(url=url, headers=headers, proxies=proxies, timeout=timeout, verify=False)


class ValidateCaptcha:
    """
    验证码验证类
    """
    PAGE_TAG = 'errors/validateCaptcha'

    def __init__(self, content, current_page_url, cookies=None, proxy=None):
        self.content = content
        self.current_page_url = current_page_url
        self.cookies = cookies
        self.proxy = proxy
        self.html = None

        # 初始化html解析
        self._init_html()

    def _init_html(self):
        """
        初始化html解析
        :return:
        """
        if self.PAGE_TAG not in self.content:
            # 当前错误的html不存在验证码
            try:
                # 请求头部
                cookie = self.cookies
                headers = RequestParam.get_headers(True, cookie)
                response = SourceDownload.get(
                    url=self._get_baseurl() + self._get_validate_captcha_uri(),
                    headers=headers,
                    proxies=self.proxy
                )
                content = response.text
            except Exception as e:
                content = ''
            self.content = content
        if not self.content:
            raise Exception('No verification code is required')
        # html解析
        self.html = etree.HTML(self.content)

    @classmethod
    def is_verification(cls, content):
        """
        是否需要验证
        :param content:
        :return:
        """
        if cls.PAGE_TAG in content:
            return True
        return False

    def get_submit_url(self):
        """
        获取提交的url
        :return:
        """
        amazon_code = self.get_amazon_code()
        if not amazon_code:
            return None
        inputs = self._get_form_inputs()
        inputs['field-keywords'] = amazon_code
        # 重定向路由获取
        if self.PAGE_TAG not in self.current_page_url:
            url_obj = urlparse(self.current_page_url)
            amzn_r = url_obj.path + '?' + url_obj.query
            if amzn_r:
                inputs['amzn-r'] = amzn_r
        return self._get_form_url() + '?' + urlencode(inputs)

    def get_amazon_code(self):
        """
        获取识别的亚马逊验证码
        :return:
        """
        source_download = SourceDownload()
        img = source_download.download(self._get_img_url())
        if not img:
            return None
        try:
            captcha = AmazonCaptcha(img)
            solution = captcha.solve()
            # 删除文件
            if os.path.exists(img):
                os.remove(img)
        except Exception:
            return None
        return solution

    def _get_img_url(self):
        """
        获取图片连接
        :return:
        """
        images = self.html.xpath('//div[@class="a-box-inner"]//img/@src')
        url = get_list_value(images, 0)
        return url

    def _get_form_inputs(self):
        """
        获取表单
        :return:
        """
        values = self.html.xpath('//form//input[@type="hidden"]/@value')
        names = self.html.xpath('//form//input[@type="hidden"]/@name')
        # 重新组装
        forms = {}
        i = 0
        for name in names:
            if values[i]:
                forms[name] = values[i]
            i += 1
        return forms

    def _get_baseurl(self):
        """
        获取当前域名
        :return:
        """
        url = self.current_page_url
        if '://' in url:
            url_obj = urlparse(url)
            return f"{url_obj.scheme}://{url_obj.netloc}"
        elif url:
            return f"https://{url}"
        else:
            return "https://www.amazon.com"

    def _get_form_url(self):
        """
        获取表单的提交url
        :return:
        """
        form_urls = self.html.xpath('//form/@action')
        form_url = get_list_value(form_urls, 0)
        if not form_url:
            form_url = self._get_validate_captcha_uri()
        if '://' in form_url:
            return form_url
        else:
            return self._get_baseurl() + form_url

    def _get_validate_captcha_uri(self):
        return '/' + self.PAGE_TAG
