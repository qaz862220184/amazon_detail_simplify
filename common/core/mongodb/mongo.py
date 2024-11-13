from pymongo import MongoClient
from common.settings import DB_MONGODB_CONF
from common.core.query.sub_meter import SubMeterQuery
from pymongo.write_concern import WriteConcern


class MongoDb:
    """
    https://cmsblogs.cn/4322.html
    连接类
    """
    pool = {}
    db = 'default'

    @classmethod
    def set_db(cls, db):
        if db:
            cls.db = db
        else:
            cls.db = 'default'

    @classmethod
    def table(cls, table, db=None):
        """
        获取一个数据库对象
        :param table:
        :param db:
        :return:
        """
        cls.set_db(db)
        return Query(table, cls._database(), cls._get_config())

    @classmethod
    def sub_table(cls, table, cycle, db=None):
        """
        获取一个分库的数据对象
        :param table:
        :param cycle:
        :param db:
        :return:
        """
        tables = cls.get_sub_tables(
            table,
            cycle,
            0
        )
        return cls.table(tables[0], db)

    @classmethod
    def sub_table_last(cls, table, cycle, db=None):
        """
        获取一个分库的数据对象
        :param table:
        :param cycle:
        :param db:
        :return:
        """
        tables = cls.get_sub_tables(
            table,
            cycle,
            365
        )
        return cls.table(tables[1], db)

    @classmethod
    def sub_table_by_week(cls, table, cycle, db=None):
        """
        获取一个分库的数据对象（增加一周的数据）
        :param table:
        :param cycle:
        :param db:
        :return:
        """
        tables = cls.get_sub_tables(
            table,
            cycle,
            7
        )
        return cls.table(tables[1], db)

    @classmethod
    def sub_table_by_days(cls, table, cycle, along=1, db=None):
        """
        获取一个分库的数据对象（增加一周的数据）
        :param table:
        :param cycle:
        :param along:
        :param db:
        :return:
        """
        tables = cls.get_sub_tables(
            table,
            cycle,
            along
        )
        return cls.table(tables[1], db)

    @classmethod
    def get_sub_tables(cls, table, cycle, along_day):
        """
        获取分库的表名称
        :param table:
        :param cycle:
        :param along_day:
        :return:
        """
        subMeterQuery = SubMeterQuery(
            table,
            cycle,
            along_day
        )
        return subMeterQuery.get_tables()

    @classmethod
    def _database(cls):
        if cls.db in cls.pool:
            conn = cls.pool[cls.db]
            try:
                res = conn.command('ping')
                if 'ok' in res and res['ok']:
                    return conn
            except Exception:
                # 说明断线
                pass
        config = cls._get_config()
        # 连接信息
        uri = config['uri']
        database_name = config['database']
        cls.pool[cls.db] = MongoClient(uri)[database_name]
        return cls.pool[cls.db]

    @classmethod
    def _get_config(cls):
        if cls.db not in DB_MONGODB_CONF:
            raise ValueError('The mongo configuration does not exist:' + cls.db)
        config = DB_MONGODB_CONF[cls.db]
        return config

    @classmethod
    def close(cls):
        for conn in cls.pool:
            conn.close()

    def __del__(self):
        self.close()


class Query:
    """
    查询类
    """

    def __init__(self, table, conn, config):
        self.table = table
        self.conn = conn
        self.prefix = config['prefix']

    def get_collection(self):
        """
        返回数据库对象
        :return:
        """
        return self.get_conn()[self.get_table_name()]

    def get_conn(self):
        """
        返回连接
        :return:
        """
        return self.conn

    def write_concern_collection(self, w=1, timeout=5000):
        """
        获取写关注对象
        """
        # 设定写关注级别
        write_concern = WriteConcern(w=w, wtimeout=timeout)
        return self.get_collection().with_options(write_concern=write_concern)

    def insert_one(self, data, is_write_concern=False):
        """
        插入单条
        :param data:
        :param is_write_concern:
        :return:
        """
        if is_write_concern is True:
            # 开启写关注
            collection = self.write_concern_collection()
        else:
            collection = self.get_collection()
        return collection.insert_one(data)

    def insert_many(self, data, is_write_concern=False, ordered=False):
        """
        插入多条
        :param data:
        :param is_write_concern:
        :param ordered:
        :return:
        """
        if is_write_concern is True:
            # 开启写关注
            collection = self.write_concern_collection()
        else:
            collection = self.get_collection()
        return collection.insert_many(data, ordered=ordered)

    def find_one(self, filter, *args, **kwargs):
        """
        单个搜索
        :param filter:
        :param args:
        :param kwargs:
        :return:
        """
        return self.get_collection().find_one(filter, *args, **kwargs)

    def find(self, filter, *args, **kwargs):
        """
        多个搜索
        :param filter:
        :param args:
        :param kwargs:
        :return:
        """
        return self.get_collection().find(filter, *args, **kwargs)

    def get_table_name(self):
        """
        获取表名称
        :return:
        """
        if self.prefix in self.table:
            return self.table
        return self.prefix + self.table

    def __getattr__(self, item):
        """
        方法不存在时调用
        :param item:
        :return:
        """
        if getattr(self.get_collection(), item):
            return getattr(self.get_collection(), item)

    # def __del__(self):
    #     self.close()
    #
    # def close(self):
    #     self.conn.close()


if __name__ == '__main__':

    # data = MongoDb.get_sub_tables(table='scrapy_sub_task', cycle=SubMeterQuery.CYCLE_YEARLY, along_day=0)
    # data = MongoDb.sub_table(table='scrapy_sub_task', cycle=SubMeterQuery.CYCLE_YEARLY)
    # print(data)
    data = MongoDb.sub_table_by_days(table='scrapy_sub_task', cycle=SubMeterQuery.CYCLE_DAILY)
    print(data)
