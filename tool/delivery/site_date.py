# -*- coding: utf-8 -*-
import datetime
import re
from common.helpers import get_dynamic_class
from common.exceptions.exception import SystemException
from tool.delivery.site_months_map import SiteMonth
from common.utils.date_time import ScrapyDateTimeManage


class BaseDelivery(object):
    """
    日期转化父类
    """
    def __init__(self, delivery_date: dict):
        self.delivery_date = delivery_date
        self.free_delivery = None
        self.fastest_delivery = None

    def get_site_time(self, country):
        default_format = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return ScrapyDateTimeManage.date_transform(default_format, '%Y-%m-%d %H:%M:%S', 'CN', country)

    def get_delivery_date(self, country):
        """
        返回配送时间
        """
        delivery_date = {'free': None, 'fastest': None}
        free_date = self.delivery_date.get('free')
        fastest_date = self.delivery_date.get('fastest')
        try:
            if free_date:
                # 定义一个方法去匹配
                free_days = self.delivery_rule_match(free_date, country)
                delivery_date['free'] = free_days
            if fastest_date:
                fastest_days = self.delivery_rule_match(fastest_date, country)
                delivery_date['fastest'] = fastest_days
        except:
            pass
        return delivery_date

    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        try:
            if 'today' in date_str.lower():
                delivery_days = 0
            else:
                # 将日期转为datetime.date格式
                if '-' in date_str:
                    new_date_str = date_str.split(' ')
                    days = new_date_str[1]
                    months = new_date_str[0]
                else:
                    new_date_str = date_str.split(',')[1].strip()
                    months, days = new_date_str.split(' ')
                months = self.get_month(months.strip(), country)
                days = int(days.split('-')[0].strip())
                this_year = datetime.datetime.now().year
                this_date = datetime.date(int(this_year), int(months), int(days))
                # 获取对应站点的对应时间
                utc_time = self.get_site_time(country)
                utc_date = utc_time.date()
                # 计算相差时间
                delivery_days = (this_date - utc_date).days
                if delivery_days < 0:
                    this_date = datetime.date(this_year+1, months, days)
                    delivery_days = (this_date - utc_date).days

            return delivery_days
        except:
            return None

    def get_month(self, months, country):
        """
        返回月份对应的阿拉伯数字
        :params months
        """
        month_map = SiteMonth.get_months_map(country)
        this_month = None
        # TODO 这里使用正则匹配一下key
        # this_month = month_map.get(months)
        for key in month_map:
            if re.match('^{}'.format(months), key):
                this_month = month_map.get(key)
        return this_month


class UsDelivery(BaseDelivery):
    """
    美国站点
    """
    pass


class DeDelivery(BaseDelivery):
    """
    德国站点
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'heute' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str.lower():
                new_date_str = date_str.split('-')[-1].strip()
                days, months = new_date_str.split(' ')
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class GbDelivery(BaseDelivery):
    """
    英国站点
    """

    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'today' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip())
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class FrDelivery(BaseDelivery):
    """
    法国站点
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if "aujourd'hui" in date_str.lower():
            delivery_days = 0
        elif 'demain le' in date_str.lower():
            delivery_days = 1
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                week, days, months = date_str.split(' ')
                months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class EsDelivery(BaseDelivery):
    """
    西班牙站点
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'hoy' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str.lower():
                new_date_str = date_str.split(' ')
                months = new_date_str[-1]
                days = new_date_str[0]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, de, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class ItDelivery(BaseDelivery):
    """
    意大利站
    """

    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'oggi' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            # 判断是否是时间段
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class PlDelivery(BaseDelivery):
    """
    波兰站点
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'dzisiaj' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            # 判断是否是时间段
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class SeDelivery(BaseDelivery):
    """
    瑞典站
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'idag' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            # 判断是否是时间段
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class CaDelivery(BaseDelivery):
    """
    加拿大站
    """
    pass


class JpDelivery(BaseDelivery):
    """
    日本站
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if '今日' in date_str.lower():
            delivery_days = 0
        elif '明日' in date_str.lower():
            delivery_days = 1
        else:
            # 将日期转为datetime.date格式
            # 判断是否是时间段
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
                months = self.get_month(months.strip(), country)
                days = int(days.split('-')[0].strip().replace('.', ''))
                this_year = datetime.datetime.now().year
            else:
                # 这个使用正则匹配一下
                the_date = re.findall(r'(\d+/\d+/\d+)', date_str)
                the_date = the_date[0] if the_date else None
                if not the_date:
                    return None
                this_year, months, days = the_date.split('/')
            this_date = datetime.date(int(this_year), int(months), int(days))
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class SgDelivery(BaseDelivery):
    """
    新加坡站点
    """

    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'today' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip())
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class NlDelivery(BaseDelivery):
    """
    荷兰站点
    """

    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if 'vandaag' in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str.lower():
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip())
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class MxDelivery(EsDelivery):
    """
    墨西哥站点
    """
    pass


class AuDelivery(SgDelivery):
    """
    澳洲站点
    """


class InDelivery(SgDelivery):
    """
    印度站点
    """


class AeDelivery(BaseDelivery):
    """
    阿联酋站点
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if "اليوم" in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str.lower():
                new_date_str = date_str.split('-')[0].strip()
                days, months = new_date_str.split(' ')
            else:
                week, days, months = date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class SaDelivery(AeDelivery):
    """
    阿拉伯站点
    """
    pass


class EgDelivery(AeDelivery):
    """
    埃及站点
    """
    pass


class TrDelivery(BaseDelivery):
    """
    土耳其站
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if "bugün" in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式
            if '-' in date_str:
                new_date_str = date_str.split(' ')
                days = new_date_str[0]
                months = new_date_str[-1]
            else:
                days, months, week = date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class BrDelivery(EsDelivery):
    """
    巴西站点
    """
    def delivery_rule_match(self, date_str, country):
        """
        使用规则计算出天数
        """
        # 还需要有一个方法返回站点对应时间
        # 先判断日期中是否包含今天，明天的数据
        if "Hoje" in date_str.lower():
            delivery_days = 0
        else:
            # 将日期转为datetime.date格式

            if '-' in date_str:
                new_date_str = date_str.split('-')[0].strip()
                days, week, months = new_date_str.split(' ')
            else:
                new_date_str = date_str.split(',')[1].strip()
                days, week, months = new_date_str.split(' ')
            months = self.get_month(months.strip(), country)
            days = int(days.split('-')[0].strip().replace('.', ''))
            this_year = datetime.datetime.now().year
            this_date = datetime.date(this_year, months, days)
            # 获取对应站点的对应时间
            utc_time = self.get_site_time(country)
            utc_date = utc_time.date()
            # 计算相差时间
            delivery_days = (this_date - utc_date).days
            if delivery_days < 0:
                this_date = datetime.date(this_year + 1, months, days)
                delivery_days = (this_date - utc_date).days

        return delivery_days


class Delivery:
    """
    时间转化类
    """

    def __init__(self, country, delivery_date):
        """
        初始化
        :params country
        :params delivery_date
        """
        self.country = country.upper()
        class_str = f'tool.delivery.site_date.{country.capitalize()}Delivery'
        class_obj = get_dynamic_class(class_str)
        if not class_obj:
            raise SystemException('The parse class does not exist:' + class_str)
        self.extract_handle = class_obj(delivery_date)

    def get_delivery_days(self):
        """
        获取图片结果
        :return:
        """
        return self.extract_handle.get_delivery_date(self.country)

    def __getattr__(self, item):
        """
        方法不存在时调用
        :params item:
        :return:
        """
        if getattr(self.extract_handle, item):
            return getattr(self.extract_handle, item)


if __name__ == '__main__':
    o = Delivery('DE', {
        'fastest': None,
        'free': '3 - 5 Apr '
    })

    # o = Delivery('US', {
    #     "free": "Monday, September 11",
    #     "fastest": "Tomorrow, September 6"
    # })

    # o = Delivery('FR', {
    #     "free": "vendredi 18 août",
    #     "fastest": "jeudi 17 août"
    # })

    # o = Delivery('NL', {
    #     "free": "2 - 6 september",
    # })

    # o = Delivery('IT', {
    #     "free": "28 - 31 agosto",
    #     "fastest": "28 - 31 agosto"
    # })

    # o = Delivery('PL', {
    #     "free": "poniedziałek, 21 sierpnia",
    #     "fastest": "jutro, 19 sierpnia"
    # })

    # o = Delivery('SE', {
    #     "free": "måndag, 21 augusti",
    #     "fastest": "imorgon, 18 augusti"
    # })

    # o = Delivery('JP', {
    #     "free": "8月20日 日曜日にお届け",
    #     "fastest": "明日 16:00 - 19:00の間にお届け"
    # })

    # o = Delivery('BR', {
    #     "free": "28 de Agosto - 25 de Setembro",
    #     "fastest": "28 de Agosto - 25 de Setembro"
    # })

    # o = Delivery('AE', {
    #     "free": "31 أغسطس - 1 سبتمبر",
    #     "fastest": "غداً، 19 أغسطس"
    # })

    data = o.get_delivery_days()
    print(data)
