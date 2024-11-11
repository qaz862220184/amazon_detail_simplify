# -*- coding: utf-8 -*-
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from common.core.mongodb.mongo import MongoDb
from common.utils.date_time import ScrapyDateTimeManage
from abc import ABCMeta, abstractmethod
from common.helpers import get_dynamic_class
from common.utils.distribution_lock import RedisLock
from datetime import datetime


def get_utc_time():
    """
    获取utc时间
    :return:
    """
    res = ScrapyDateTimeManage.date_time().date_time()
    return datetime.strptime(res, "%Y-%m-%d %H:%M:%S")


class DropdownPipeline:
    def __init__(self):
        self.lock_time = 30
        self.lock = RedisLock(
            lock_name='dropdown',
            lock_timeout=self.lock_time
        )

    def process_item(self, item, spider):
        """
        :param item:
        :param spider:
        :return:
        """
        class_str = f"dropdown.pipelines.{spider.name.capitalize()}PipelineHandle"
        class_obj = get_dynamic_class(class_str)
        if not class_obj:
            raise Exception(f"class does not exist:{class_str}")
        # 处理
        obj = class_obj(item, spider)

        # 加进程锁
        identifier = self.lock.acquire_lock(
            acquire_timeout=self.lock_time
        )
        try:
            if obj.handle():
                # 成功
                spider.set_execute_status(
                    status=spider.EXECUTE_STATUS_SUCCESS
                )
        except Exception as exception:
            # 发生错误
            raise exception
        finally:
            # 解锁
            self.lock.release_lock(
                identifier=identifier
            )


class BasePipelineHandle(metaclass=ABCMeta):
    # 表
    table = ''

    def __init__(self, item, spider):
        """
        初始化
        :param item:
        :param spider:
        """
        self.item = item
        self.spider = spider

    @abstractmethod
    def handle(self):
        """
        处理函数
        :return:
        """
        pass


class KeywordPipelineHandle(BasePipelineHandle):
    """
    搜索下拉关键词
    """

    table = 'dropdown_keyword_result'

    def handle(self):
        if 'result' in self.item:
            result = self.item['result']
            # if not result:
            #     raise ValueError('No drop-down results')
            sql = []
            for item in result:
                if item['value']:
                    # 不存在才更新【存量更新】
                    new_item = {
                        # 'relation_id': self.spider.get_task('relation_id'),
                        'sort': item['sort'],
                        'scrapy_sub_task_id': self.spider.sub_task_id,
                        'type': item['type'],
                        'value': item['value'],
                        'created_at': get_utc_time(),
                    }
                    sql.append(new_item)
            # 插入
            if sql:
                MongoDb.table(self.table, 'brand').insert_many(sql)
        return True
