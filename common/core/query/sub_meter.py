
from datetime import datetime
import datetime as dt
import math
from common.utils.date_time import ScrapyDateTimeManage

class SubMeterQuery:
    CYCLE_HOURLY = 'hourly'
    CYCLE_DAILY = 'daily'
    CYCLE_WEEKLY = 'weekly'
    CYCLE_MONTHLY = 'monthly'
    CYCLE_QUARTERLY = 'quarterly'
    CYCLE_YEARLY = 'yearly'
    CYCLES = {
        CYCLE_HOURLY:'时',
        CYCLE_DAILY:'天',
        CYCLE_WEEKLY:'周',
        CYCLE_MONTHLY:'月',
        CYCLE_QUARTERLY:'季',
        CYCLE_YEARLY:'年',
    }

    def __init__(self, table:str, cycle:str, along_day:int=0):
        self.table = table
        if cycle not in self.CYCLES:
            raise ValueError('cycle absent')
        self.cycle = cycle
        self.along_day = along_day

    def get_tables(self, date:str=None) -> tuple:
        """
        获取插入表
        :param date:
        :return:
        """
        if date is None:
            current_datetime = datetime.now()
            date = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
        now_table = self.get_query_table_by_date_time(
            date
        )
        along_date = ScrapyDateTimeManage.date_for_timestamp(
            ScrapyDateTimeManage.strtotime(date) + (self.along_day * 86400)
        )
        along_table = self.get_query_table_by_date_time(
            along_date
        )
        if now_table != along_table:
            return now_table, along_table,
        else:
            return (now_table, )

    def get_query_table_by_date_time(self, date:str) -> str:
        """
        获取查询表名
        :param date:
        :return:
        """
        # 时间格式
        if ':' in date:
            _format = '%Y-%m-%d %H:%M:%S'
        else:
            _format = '%Y-%m-%d'
        # 时间转化
        date_obj = datetime.strptime(
            date,
            _format
        )
        # 获取后缀
        suffix = ''
        if self.cycle is self.CYCLE_WEEKLY:
            suffix = ScrapyDateTimeManage.calculate_week_number(
                date_obj.year,
                date_obj.month,
                date_obj.day
            )
            suffix = 'w' + str(suffix)
        elif self.cycle is self.CYCLE_MONTHLY:
            suffix = date_obj.month
        elif self.cycle is self.CYCLE_QUARTERLY:
            month = date_obj.month
            suffix = math.ceil(month / 3)
        elif self.cycle is self.CYCLE_DAILY:
            suffix = date_obj.timetuple().tm_yday
            suffix = 'd' + str(suffix)
            pass
        suffix = str(suffix)

        # 日期
        date = "{year}".format(
            year=date_obj.year,
        )
        arr = [self.table, date, suffix]
        arr = list(filter(lambda x: x, arr))
        return "_".join(arr)


if __name__ == '__main__':
    subMeterQuery = SubMeterQuery(
        'scrapy_sub_task',
        SubMeterQuery.CYCLE_DAILY,
        1
    )
    res = subMeterQuery.get_tables()
    print(res)



