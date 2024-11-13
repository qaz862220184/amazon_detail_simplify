from lxml import etree
import re


class VerifyResponse:

    def __init__(self, response):
        self.response = response

    @property
    def status(self):
        return self.response.status

    @property
    def content(self):
        return self.response.text

    def is_error_page(self):
        """
        判断页面是否出错
        :return:
        """
        if (
                (not self.content)
                or ('ERR_TIMED_OUT' in self.content)
                or ("ERR_FAILED" in self.content)
                or ("ERR_EMPTY_RESPONSE" in self.content)
                or ("ERR_NETWORK_CHANGED" in self.content)
                or ("ERR_PROXY_CONNECTION_FAILED" in self.content)
        ):
            return True
        return False if self.is_amazon_page() is True else True

    def is_no_flow_page(self):
        """
        判断是否为无流量
        :return:
        """
        if "ERR_TUNNEL_CONNECTION_FAILED" in self.content:
            return True
        return False

    def is_amazon_page(self):
        """
        判断是否是亚马逊页面
        :return:
        """
        if 'amazon' in self.content:
            return True
        return False

    def is_validate_captcha(self):
        """
        判断是否出现验证码
        :return:
        """
        if 'errors/validateCaptcha' in self.content:
            return True
        return False

    def is_dog_page(self):
        """
        判断是否出现狗页面
        :return:
        """
        texts = [
            'Service Unavailable Error',
            'Toutes nos excuses',
            'Sorry! Something went wrong!',
            'Sorry! Something'
        ]
        for text in texts:
            if str(text).lower() in str(self.content).lower():
                return True
        return False

    def is_blank_page(self):
        """
        判断是否出现空白页面
        :return:
        """
        if 'id="search"' not in self.content.lower() and 'errors/validateCaptcha' not in self.content:
            return True
        return False

    def is_not_sponsored(self):
        """
        判断是否为无广告页面
        :return:
        """
        if 'id="search"' in self.content.lower() and "a-row a-spacing-micro" not in self.content.lower():
            return True
        return False

    def is_not_sponsored_mobile(self):
        """
        判断是否为无广告页面
        :return:
        """
        if not self.content:
            return True
        tree = etree.HTML(self.content)
        data = tree.xpath('//div//span[@class="a-color-secondary"]')
        if 'id="search"' in self.content.lower() and not data:
            return True
        return False

    def is_not_listing(self):
        # 添加个正则判断一下数据是否存在
        rule_list = [
            r'https://images-[a-z]{2}.ssl-images-amazon.com/images/G/[0-9]{2}/x-locale/common/kailey-kitty._TTD_.gif',
            r"Sorry! We couldn't find that page."
        ]
        for rule in rule_list:
            if re.findall(rule, self.content):
                return True
        return False

    def is_not_address(self, country_code, zip_code):
        """
        判断是否没有选择地址
        :return:
        """
        if not self.content:
            return False
        tree = etree.HTML(self.content)
        address_info = tree.xpath('//*[@id="glow-ingress-line2"]/text()')
        if address_info:
            address = address_info[0]
            address = address.strip()
            address = ''.join(address.split())
            if 'GB' == country_code:
                zip_code = zip_code[0:-2]
            if 'CA' == country_code:
                zip_code = zip_code.split(' ')[0]
            if 'PL' == country_code:
                zip_code = ''.join(zip_code.split())
            if zip_code not in address and (zip_code.replace(' ', '') not in address):
                return True
        return False

    def is_not_address_mobile(self, country_code, zip_code):
        """
        判断是否没有选择地址
        :return:
        """
        if not self.content:
            return False
        tree = etree.HTML(self.content)
        # 移动端的地址位置
        address_info = tree.xpath('//*[@id="glow-ingress-single-line"]/text()')
        if address_info:
            address = address_info[0]
            address = address.strip()
            address = ''.join(address.split())
            if 'GB' == country_code:
                zip_code = zip_code[0:-2]
            if 'CA' == country_code:
                zip_code = zip_code.split(' ')[0]
            if 'PL' == country_code:
                zip_code = ''.join(zip_code.split())
            if zip_code not in address and (zip_code.replace(' ', '') not in address):
                return True
        return False
