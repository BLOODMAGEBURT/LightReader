import os

from dotenv import load_dotenv

# 加载根目录的.env文件
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # database config
    D_USER = os.environ.get('D_USER') or 'you will never known'
    D_PASSWORD = os.environ.get('D_PASSWORD') or '123456test'
    D_HOST = '127.0.0.1'
    D_PORT = 3306
    D_DATABASE = 'lightreader'
    # sql连接字符串
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%s:%s@%s:%s/%s' % (D_USER, D_PASSWORD, D_HOST, D_PORT, D_DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis设置
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    # 语言设置
    LANGUAGES = ['zh-CN']

    # 每页显示的数量
    CHAPTER_PER_PAGE = 50

    # api url
    # 书籍详情页
    # BOOK_DETAIL = 'http://novel.juhe.im/book-info/{book_id}'
    BOOK_DETAIL = 'http://api.zhuishushenqi.com/book/{book_id}'
    # 章节列表
    # CHAPTER_LIST = 'http://novel.juhe.im/book-chapters/{book_id}'
    CHAPTER_LIST = 'http://api.zhuishushenqi.com/mix-atoc/{book_id}?view=chapters'
    # 章节详情
    # CHAPTER_DETAIL = 'http://novel.juhe.im/chapters/{0}'
    CHAPTER_DETAIL = 'http://chapter2.zhuishushenqi.com/chapter/{0}'

    # 文件目录
    UPLOADS_DEFAULT_DEST = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'files')

    # headers
    headers = {
        'User-Agent': 'ZhuiShuShenQi/3.172.1 (Android 5.1.1; Meizu X86 / Meizu Mx5; China Mobile GSM)'
                      '[preload=false;locale=zh_CN;clientidbase=]'
    }
