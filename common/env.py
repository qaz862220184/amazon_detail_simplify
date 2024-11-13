# -*- coding: UTF-8 -*-
from dotenv import load_dotenv, dotenv_values
from common.helpers import get_absolute_path

# 从当前工作目录加载 .env 文件
load_dotenv()


class ENV(object):

    @classmethod
    def find_env(cls, env_name):
        return dotenv_values().get(env_name)

    @classmethod
    def update_env(cls, env_name, env_data):
        env_file_path = get_absolute_path('.env')
        with open(env_file_path, 'r') as file:
            lines = file.readlines()

        # 修改特定配置项
        for i, line in enumerate(lines):
            if line.startswith('{}='.format(env_name)):
                lines[i] = '{}="{}"\n'.format(env_name, env_data)

        # 将修改后的内容写回.env文件
        with open(env_file_path, 'w') as file:
            file.writelines(lines)

        load_dotenv()

    @classmethod
    def is_debug(cls):
        """
        判断是否为开发环境
        """
        env = cls.find_env('ENV')
        if env == 'debug':
            return True
        return False


if __name__ == '__main__':
    ENV.update_env("COMPUTER_UUID", "45ea0ce1-d1a4-4c97-9028-7b6c6137796f")
    data = ENV.find_env('COMPUTER_UUID')
    print(data)
