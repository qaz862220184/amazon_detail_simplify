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
        'IT': "Europe/Paris",
        # 波兰
        'PL': "Europe/Paris",
        # 瑞典
        'SE': "Europe/Paris",
        # 新加坡
        'SG': "Asia/Singapore",
        # 墨西哥
        'MX': "Europe/Paris",
        # 印度
        'IN': "Europe/Paris",
        # 巴西
        'BR': "Europe/Paris",
        # 荷兰
        'NL': "Europe/Paris",
        # 澳大利亚
        'AU': "Europe/Paris",
        # 阿联酋
        'AE': "Europe/Paris",
        # 阿拉伯
        'SA': "Europe/Paris",
        # 埃及
        'EG': "Europe/Paris",
        # 土耳其
        'TR': "Europe/Paris",
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


class ScrapyDateTimeManage:
    # 对象
    date_times = {}

    @classmethod
    def date_time(cls, timezone=None):
        """
        获取时间对象
        :param timezone:
        :return:
        """
        if timezone:
            if timezone in CountryDateTimeManage.TIMEZONE:
                timezone = CountryDateTimeManage.TIMEZONE[timezone]
        if timezone not in cls.date_times:
            date_time_obj = CountryDateTimeManage(timezone)
            cls.date_times[timezone] = date_time_obj
        return cls.date_times[timezone]

    @classmethod
    def date_transform(cls, date, s_format, from_zone, to_zone):
        """
        时间转化
        :param date:
        :param s_format:
        :param from_zone:
        :param to_zone:
        :return:
        """
        us_time = datetime.strptime(date, s_format).replace(
            tzinfo=pytz.timezone(
                CountryDateTimeManage.get_zone(zone=from_zone)
            )
        )
        to_zone = pytz.timezone(
            CountryDateTimeManage.get_zone(zone=to_zone)
        )
        return us_time.astimezone(to_zone)


if __name__ == '__main__':
    res = ScrapyDateTimeManage.date_time('CN').date_time()
    print(res)
    # default_format = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print(default_format)
    data = ScrapyDateTimeManage.date_transform(res, "%Y-%m-%d %H:%M:%S", 'CN', 'UTC')
    print(data, type(data))

    res1 = ScrapyDateTimeManage.date_time().utc_time()
    print(res1)
    # data = ScrapyDateTimeManage.date_transform(res1, "%Y-%m-%d %H:%M:%S", 'UTC', 'CN')
    # print(data, type(data))
