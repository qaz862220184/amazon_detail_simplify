from pymongo import MongoClient
from common.settings import DB_MONGODB_CONF


class MongoDb:
    """
    https://cmsblogs.cn/4322.html
    连接类
    """
    pool = {}
    db = 'default'

    @classmethod
    def set_default(cls, default):
        cls.default = default

    @classmethod
    def table(cls, table, db=None):
        if db is None:
            db = cls.db
        return Query(table, cls.database(db), cls.get_config(db))

    @classmethod
    def database(cls, db):
        if db in cls.pool:
            conn = cls.pool[db]
            try:
                res = conn.command('ping')
                if 'ok' in res and res['ok']:
                    return conn
            except Exception:
                # 说明断线
                pass
        config = cls.get_config(db)
        # 连接信息
        uri = config['uri']
        database_name = config['database']
        cls.pool[db] = MongoClient(uri)[database_name]
        return cls.pool[db]

    @classmethod
    def get_config(cls, db):
        if db not in DB_MONGODB_CONF:
            raise ValueError('The mongo configuration does not exist:' + db)
        config = DB_MONGODB_CONF[db]
        return config

    def close(self):
        for conn in self.pool:
            conn.close()


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

    def insert_one(self, data):
        """
        插入单条
        :param data:
        :return:
        """
        return self.get_collection().insert_one(data)

    def insert_many(self, data):
        """
        插入多条
        :param data:
        :return:
        """
        return self.get_collection().insert_many(data)

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

    def close(self):
        self.conn.close()
