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
    D_HOST = os.environ.get('D_HOST') or '127.0.0.1'
    D_PORT = 3306
    D_DATABASE = 'lightreader'
    # sql连接字符串
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%s:%s@%s:%s/%s' % (D_USER, D_PASSWORD, D_HOST, D_PORT, D_DATABASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis设置
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    # 缓存设置
    CACHE_TYPE = os.environ.get('CACHE_TYPE') or 'simple'
    CACHE_REDIS_HOST = os.environ.get('CACHE_REDIS_HOST') or '127.0.0.1'
    CACHE_REDIS_PORT = os.environ.get('ACHE_REDIS_PORT') or 6379
    CACHE_REDIS_PASSWORD = os.environ.get('CACHE_REDIS_PASSWORD')
    CACHE_REDIS_DB = os.environ.get('CACHE_REDIS_DB')

    # config admin email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.qq.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or 1
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = [os.environ.get('ADMINS_MAIL')]

    # log file
    LOG_FILE = 'logs/microblog.log'

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

