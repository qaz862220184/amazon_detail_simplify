# -*- coding: UTF-8 -*-
import time
import pytz
from datetime import datetime


class CountryDateTimeManage(object):
    TIMEZONE = {
        'UTC': "UTC",
        'CN': "Asia/Shanghai",
        'US': "America/Los_Angeles",
        'GB': "Europe/London",
        'CA': "America/Los_Angeles",
        'JP': "Asia/Tokyo",
        'FR': "Europe/Paris",
        'DE': "Europe/Paris",
        # 西班牙
        'ES': "America/Port_of_Spain",
        # 意大利
        'IT': "Europe/Rome",
        # 波兰
        'PL': "Europe/Warsaw",
        # 瑞典
        'SE': "Europe/Stockholm",
        # 新加坡
        'SG': "Asia/Singapore",
        # 墨西哥
        'MX': "America/Mexico_City",
        # 印度
        'IN': "Asia/Kolkata",
        # 巴西
        'BR': "America/Sao_Paulo",
        # 荷兰
        'NL': "Europe/Amsterdam",
        # 澳大利亚
        'AU': "Australia/Sydney",
        # 阿联酋
        'AE': "Asia/Dubai",
        # 阿拉伯
        'SA': "Asia/Riyadh",
        # 埃及
        'EG': "Africa/Cairo",
        # 土耳其
        'TR': "Europe/Istanbul",
    }

    def __init__(self, timezone=None):
        # 设置默认的时区
        self.default_timezone = 'Asia/Shanghai'
        self.set_timezone(timezone)

    def date_time(self, format_str='%Y-%m-%d %H:%M:%S'):
        """
        获取当前日期
        :param format_str:
        :return:
        """
        return datetime.now(tz=pytz.timezone(
            self.default_timezone
        )).strftime(format_str)

    def utc_time(self):
        """
        获取当前utc时间
        :return:
        """
        tz = pytz.timezone(self.default_timezone)
        local_time = tz.localize(datetime.now())
        return local_time.astimezone(pytz.utc)

    def strtotime(self, string, format_str='%Y-%m-%d %H:%M:%S'):
        """
        转化成时间戳
        :param string:
        :param format_str:
        :return:
        """
        try:
            # 转换为时间数组
            date = time.strptime(string, format_str)
            # 转换为UNIX时间戳
            return date.timestamp()
        except [OverflowError, ValueError]:
            return 0

    def timestamp_to_gmt(self, timestamp):
        """
        时间戳转gpt
        :param timestamp:
        :return:
        """
        time_array = time.localtime(timestamp)
        temp_format = '%Y-%m-%d %H:%M:%S'
        date = time.strftime(temp_format, time_array)
        return datetime.strptime(
            date, temp_format
        ).strftime(
            '%a, %d-%b-%Y %H:%M:%S GMT'
        )

    def set_timezone(self, timezone):
        """
        设置时区
        :param timezone:
        :return:
        """
        if timezone:
            self.default_timezone = self.get_zone(
                zone=timezone
            )
        return self

    @classmethod
    def get_zone(cls, zone):
        """
        获取时区
        :param zone:
        :return:
        """
        if zone in cls.TIMEZONE:
            return cls.TIMEZONE[zone]
        return zone


if __name__ == '__main__':
    date = CountryDateTimeManage('CN').utc_time()
    print(date, type(date))
