import pymysql
from common.settings import DB_MYSQL_CONF



class MysqlDb:
    pool = {}
    db = 'default'

    @classmethod
    def set_db(cls, db):
        cls.db = db

    @classmethod
    def table(cls, table, db=None):
        if db is None:
            db = cls.db
        return Query(table, cls.database(db), cls.get_config(db))

    @classmethod
    def database(cls, db):
        # 数据库连接
        if db in cls.pool:
            conn = cls.pool[db]
            try:
                res = conn.ping()
                if 'ok' in res and res['ok']:
                    return conn
            except Exception:
                # 说明断线
                pass
        config = cls.get_config(db)
        # 新建一个数据库连接
        cls.pool[db] = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            passwd=config['passwd'],
            db=config['db'],
            charset=config['charset'],
            cursorclass=config['cursor_class']
        )
        return cls.pool[db]

    @classmethod
    def get_config(cls, db):
        """
        获取配置
        :param db:
        :return:
        """
        if db not in DB_MYSQL_CONF:
            raise ValueError('The mongo configuration does not exist:' + db)
        config = DB_MYSQL_CONF[db]
        return config

    def close(self):
        for conn in self.pool:
            conn.close()


class Query:
    """
    查询类
    """

    def __init__(self, table, conn, config):
        self.conn = conn
        self.cursor = self.conn.cursor()
        self.table = table
        self.prefix = config['prefix']
        self.where_parse = WhereParse()
        self.orders = {}
        self.fields = []
        self.limits = None

    def exec(self, sql, param=None):
        """
        执行
        :param sql:
        :param param:
        :return:
        """
        try:
            status = self.cursor.execute(sql, param)
            self.conn.commit()
        except Exception as exception:
            self.conn.rollback()
            raise exception
        return status

    def query(self, sql, param=None):
        """
        查询
        :param sql:
        :param param:
        :return:
        """
        self.cursor.execute(sql, param)
        return self.cursor.fetchall()

    def get_cursor(self):
        """
        返回游标
        :return:
        """
        return self.cursor

    def insert(self, data):
        """
        插入
        :param data:
        :return:
        """
        data_values = "(" + "%s," * (len(data)) + ")"
        data_values = data_values.replace(',)', ')')

        db_field = data.keys()
        data_tuple = tuple(data.values())
        db_field = str(tuple(db_field)).replace("'", '')
        sql = """ insert into %s %s values %s """ % (self.get_table_name(), db_field, data_values)
        return self.exec(sql, data_tuple)

    def update(self, data):
        """
        更新
        :param data:
        :return:
        """
        fields = data.keys()
        update_sql = []
        param = []
        for field in fields:
            update_sql.append(f'{field}=%s')
            param.append(data[field])
        where_sql, where_param = self.where_parse.parse()

        # 拼接完整sql
        sql = f'UPDATE `{self.get_table_name()}` SET {",".join(update_sql)} {where_sql}'
        param.extend(where_param)
        return self.exec(sql, param)

    def where(self, **kwargs):
        """
        条件
        :param kwargs:
        :return:
        """
        self.where_parse.append_where(**kwargs)
        return self

    def where_raw(self, sql, param):
        """
        原生条件
        :param sql:
        :param param:
        :return:
        """
        self.where_parse.append_rawsql(sql, param)
        return self

    def field(self, fields=None):
        """
        字段
        :param fields:
        :return:
        """
        new_field = []
        if fields is not None:
            for f in fields:
                new_field.append(f"`{f}`")
        else:
            new_field = []
        self.fields = new_field
        return self

    def limit(self, limit=None):
        """
        条数
        :param limit:
        :return:
        """
        if isinstance(limit, tuple):
            self.limits = limit
        else:
            self.limits = (0, limit)
        return self

    def order(self, **kwargs):
        """
        排序
        :param kwargs:
        :return:
        """
        self.orders = kwargs
        return self

    def find(self):
        """
        查询当个结果
        :return:
        """
        self.limit((0, 1))
        res = self.get()
        if res:
            return res.pop()
        return None

    def get(self):
        """
        查询
        :return:
        """
        # 字段
        if self.fields:
            field_sql = ','.join(self.fields)
        else:
            field_sql = '*'
        # 排序
        order_sql = ''
        if self.orders:
            order_sql_arr = []
            for f in self.orders:
                order_sql_arr.append(f'{f} {self.orders[f]}')
            if order_sql_arr:
                order_sql = "ORDER BY " + ", ".join(order_sql_arr)
        # 条数
        limit_sql = ''
        if self.limits:
            start, limit = self.limits
            limit_sql = f"LIMIT {start},{limit}"
        # 组装sql
        where_sql, where_param = self.where_parse.parse()
        sql = f"SELECT {field_sql} FROM {self.get_table_name()} {where_sql} {order_sql} {limit_sql}"

        return self.query(sql, where_param)

    def get_table_name(self):
        """
        获取表名称
        :return:
        """
        if self.prefix in self.table:
            return self.table
        return self.prefix + self.table

    def close(self):
        """
        关闭连接
        :return:
        """
        self.conn.close()
        self.cursor.close()


class WhereParse:
    """
    where条件解析
    """

    def __init__(self):
        self.wheres = {}
        self.sql = ''
        self.params = []

    def append_where(self, **kwargs):
        """
        追加条件
        :param kwargs:
        :return:
        """
        op = '='
        boolean = 'and'
        for field in kwargs:
            value = kwargs[field]
            if isinstance(value, tuple):
                # 元祖
                if len(value) == 3:
                    # 说明指定条件类型
                    op, val, boolean = value
                else:
                    op, val = value
            else:
                val = value
            if boolean in self.wheres:
                self.wheres[boolean].append((field, op, val))
            else:
                self.wheres.update({boolean: [(field, op, val)]})
        return self

    def append_rawsql(self, sql, param, boolean='and'):
        """
        追加原生sql
        :param sql:
        :param param:
        :param boolean:
        :return:
        """
        self.__merge_sql(sql, boolean)
        for tup in param:
            self.params.append(tup)
        return self

    def parse(self):
        """
        解析
        :return:
        """
        for boolean in self.wheres:
            # 条件
            sql_arr = []
            for where in self.wheres[boolean]:
                field, op, val = where
                sql_arr.append(f'{field}{op}%s')
                self.params.append(val)
            if sql_arr:
                self.__merge_sql(f" {boolean} ".join(sql_arr), boolean)
        if self.sql:
            self.sql = f"WHERE {self.sql}"
        return self.sql, self.params

    def __merge_sql(self, sql, boolean='and'):
        """
        合并sql
        :param sql:
        :param boolean:
        :return:
        """
        if self.sql:
            self.sql = self.sql + ' ' + boolean + ' ' + sql
        else:
            self.sql = sql
        return self.sql