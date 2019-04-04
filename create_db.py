import pymysql

from app import db
from config import Config

conn = pymysql.connect(host=Config.D_HOST, port=Config.D_PORT, user=Config.D_USER, passwd=Config.D_PASSWORD)
cursor = conn.cursor()
cursor.execute("show databases like 'lightreader'")
create_db = cursor.fetchall()
if not create_db:
    cursor.execute('create database lightreader')
cursor.close()
conn.close()

db.create_all()
