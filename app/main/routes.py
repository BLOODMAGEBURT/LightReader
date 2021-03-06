import json
import os
import re
import time
from datetime import datetime
from hashlib import md5
from time import sleep
from time import time

import aiohttp
import asyncio
import requests
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from app import create_app, db, text
from app.forms import LoginForm, RegistrationForm, SearchForm, JumpForm
from app.models import User, Subscribe, Download, Task, Record
from config import Config
from app.main import bp


def get_response(url):
    i = 0
    js = None
    while i < 5:
        js = None
        try:
            data = requests.get(url, headers=Config.headers).text
            js = json.loads(data)
            break
        except ConnectionError:
            i += 1
        sleep(0.5)
    return js


async def async_get_response(key, url, res):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=Config.headers) as resp:
            assert resp.status == 200
            res[key] = await resp.json()


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        current_user.user_ip = request.headers.environ.get('REMOTE_ADDR')
        current_user.user_agent = request.headers.environ.get('HTTP_USER_AGENT')
        # 教程上说不需要加这一行，亲测需要
        db.session.add(current_user)
        db.session.commit()


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(name=form.username.data).first()
        if u is None or not u.check_password(form.password.data):
            flash('登录失败')
            return redirect('login')
        login_user(u, remember=form.remember_me.data)
        # 网页回调，使用户登录后返回登录前页面
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).decode_netloc() != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    flash('本站内容需要登录之后才能查看')
    return render_template('login.html', title='登录', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        u = User(name=form.username.data)
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        flash('注册成功')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form, title='注册')


@bp.route('/delete_user/<id>', methods=['GET'])
@login_required
def delete_user(id):
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    u = User.query.get(id)
    db.session.delete(u)
    db.session.commit()
    flash('删除用户成功！')
    return redirect(url_for('main.user_list'))


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
# @login_required
def index():
    dic = {}
    subscribe_lis = []
    res = {}
    # 手动创建事件循环
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    tasks = []
    # 获取订阅信息
    if current_user.is_authenticated:
        dic['subscribe'] = []
        for s in current_user.subscribing.order_by(Subscribe.time.desc()):
            subscribe_lis.append(s)
        if len(subscribe_lis) > 0:
            s_url = 'http://api.zhuishushenqi.com/book?view=updated&id='
            for s in subscribe_lis:
                s_url += s.book_id + ','
            s_url = s_url[:-1]
            tasks.append(async_get_response(key='subscribe', url=s_url, res=res))
    # 获取分类
    # tasks.append(async_get_response(key='classify', url='https://novel.juhe.im/categories', res=res))
    dic['classify'] = get_redis_string('classify')
    if not dic['classify']:
        tasks.append(
            async_get_response(key='classify', url='http://api.zhuishushenqi.com/cats/lv2/statistics', res=res))
    else:
        dic['classify'] = json.loads(dic['classify'])

    # 获取榜单信息
    # tasks.append(async_get_response(key='rank', url='https://novel.juhe.im/rank-category', res=res))
    dic['rank'] = get_redis_string('rank')
    if not dic['rank']:
        tasks.append(async_get_response(key='rank', url='http://api.zhuishushenqi.com/ranking/gender', res=res))
    else:
        dic['rank'] = json.loads(dic['rank'])

    # 异步获取
    if len(tasks) > 0:
        loop.run_until_complete(asyncio.wait(tasks))

    # 处理订阅信息
    js = res.get('subscribe')
    for i in range(0, len(subscribe_lis)):
        t = datetime.strptime(js[i]['updated'], UTC_FORMAT)
        dic['subscribe'].append({
            'title': subscribe_lis[i].book_name,
            '_id': subscribe_lis[i].book_id,
            'last_chapter': js[i]['lastChapter'],
            'updated': t
        })
    if not dic['classify']:
        dic['classify'] = res.get('classify')
        set_redis_string('classify', json.dumps(dic['classify']))

    if not dic['rank']:
        dic['rank'] = res.get('rank')
        set_redis_string('rank', json.dumps(dic['rank']))

    # 搜索框
    form = SearchForm()
    if form.validate_on_submit():
        data = get_response('http://api.zhuishushenqi.com/book/fuzzy-search/?query=' + form.search.data)
        lis = []
        for book in data.get('books'):
            lis.append(book)
        return render_template('search_result.html', data=lis, title='搜索结果', form=form)

    return render_template('index.html', data=dic, form=form, title='印象.读书', limit=Config.CHAPTER_PER_PAGE)


@bp.route('/subscribe/')
@login_required
def subscribe():
    _id = request.args.get('id')
    js = get_response('http://api.zhuishushenqi.com/book/' + _id)
    name = js.get('title')
    data = get_response('http://api.zhuishushenqi.com/toc?view=summary&book=' + _id)

    s = Subscribe(user=current_user, book_id=_id, book_name=name, source_id=data[1]['_id'], chapter=0)
    db.session.add(s)
    db.session.commit()
    flash('订阅成功')
    return redirect(url_for('main.book_detail', book_id=_id))


@bp.route('/unsubscribe/')
@login_required
def unsubscribe():
    _id = request.args.get('id')
    s = current_user.subscribing.filter(Subscribe.book_id == _id).first()
    db.session.delete(s)
    db.session.commit()
    flash('取消订阅成功')
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).decode_netloc() != '':
        next_page = url_for('main.index')
    return redirect(next_page)


def get_source_id(book_id):
    dd = get_response('http://api.zhuishushenqi.com/toc?view=summary&book=' + book_id)
    for i in range(len(dd))[::-1]:
        if dd[i]['source'] != 'zhuishuvip':
            source_id = dd[i]['_id']
            if dd[i]['source'] == 'my176':
                break
    return source_id


@bp.route('/chapter/', methods=['GET', 'POST'])
@login_required
def chapter():
    page = request.args.get('page')
    book_id = request.args.get('book_id')
    source_id = request.args.get('source_id')
    if not source_id:
        source_id = get_source_id(book_id)
    data = get_response('http://api.zhuishushenqi.com/toc/{0}?view=chapters'.format(source_id))
    lis = []
    l = []
    chap = data.get('chapters')
    form = JumpForm()
    if form.validate_on_submit():  # 必须使用post方法才能正产传递参数
        page = form.page.data
    page_count = int(len(chap) / Config.CHAPTER_PER_PAGE)
    if len(chap) % Config.CHAPTER_PER_PAGE == 0:
        page_count -= 1
    if page is not None:
        page = int(page)
        if page > page_count:
            page = page_count
        lis = chap[page * Config.CHAPTER_PER_PAGE:(page + 1) * Config.CHAPTER_PER_PAGE]
        i = 0
    for c in lis:
        l.append({
            'index': page * Config.CHAPTER_PER_PAGE + i,
            'title': c.get('title')
        })
        i += 1

    if form.validate_on_submit():
        return render_template('chapter.html', data=l, title='章节列表', page_count=page_count, page=form.page.data,
                               source_id=source_id,
                               book_id=book_id, form=form)

    return render_template('chapter.html', data=l, title='章节列表', page_count=page_count, page=page, source_id=source_id,
                           book_id=book_id, form=form)


@bp.route('/read/', methods=['GET'])
@login_required
def read():
    index = int(request.args.get('index'))
    source_id = request.args.get('source_id')
    book_id = request.args.get('book_id')
    r = Record(user=current_user, book_id=book_id, chapter_index=index, source_id=source_id, time=datetime.utcnow())
    asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    tasks = list()
    res = dict()
    tasks.append(async_get_response(key='detail', url='http://api.zhuishushenqi.com/book/' + book_id, res=res))
    tasks.append(
        async_get_response(key='chapters', url='http://api.zhuishushenqi.com/toc/{0}?view=chapters'.format(source_id),
                           res=res))
    loop.run_until_complete(asyncio.wait(tasks))
    r.book_name = res['detail']['title']
    r.source_name = res['chapters']['name']
    page = int(index / Config.CHAPTER_PER_PAGE)
    chap = res['chapters'].get('chapters')
    title = chap[index]['title']
    url = chap[index]['link']
    r.chapter_name = chap[index]['title']
    # 为各个源添加特殊处理
    if res['chapters']['source'] == 'biquge':
        url = reg_biquge(res['chapters']['link'], url)
    # 设定redis key
    key = md5((source_id + str(index)).encode("utf8")).hexdigest()[:10]

    li = get_content_list(key=key, url=url)
    if index < len(chap) - 1:
        next_key = md5((source_id + str(index + 1)).encode("utf8")).hexdigest()[:10]
        next_url = chap[index + 1]['link']
        # 使用后台任务缓存下一章节
        try:
            current_app.task_queue.enqueue('app.tasks.cache', next_key, next_url)
        except current_app.redis.exceptions.RedisError:
            print('后台任务未开启！')
    font_size = '120%'
    if current_user.is_authenticated:
        font_size = current_user.font_size if current_user.font_size is not None else '120%'
        s = Subscribe.query.filter(Subscribe.book_id == book_id, Subscribe.user == current_user).first()
        if s:
            r.is_subscribe = True
            s.chapter = index
            s.chapter_name = title
            s.source_id = source_id
            s.time = datetime.utcnow()
        else:
            r.is_subscribe = False
    db.session.add(r)
    db.session.commit()

    return render_template('read.html', body=li, title=title, next=(index + 1) if len(chap) - index > 1 else None,
                           pre=(index - 1) if index > 0 else None, index=index,
                           book_id=book_id, page=page, source_id=source_id, font_size=font_size,
                           background_color='#b0c4de')


def reg_biquge(book_url, chapter_url):
    reg_normal = r'(http:\/\/www.biquge.la\/book\/[0-9]*\/[0-9]*.html)'
    reg_error = r'(http:\/\/www.biquge.la[0-9]*.html)'
    reg_chapter = r'([0-9]*.html)'
    reg = re.compile(reg_normal)
    lis = re.findall(reg, chapter_url)
    if lis:
        return chapter_url
    else:
        reg = re.compile(reg_error)
        lis = re.findall(reg, chapter_url)
        if lis:
            reg = re.compile(reg_chapter)
            lis = re.findall(reg, chapter_url)
            if lis:
                return book_url + lis[0]
    return chapter_url


def get_content_text(url):
    chapter_url = Config.CHAPTER_DETAIL.format(url.replace('/', '%2F').replace('?', '%3F'))
    data = get_response(chapter_url)
    if not data:
        txt = '检测到阅读接口发生故障，请刷新页面或稍后再试'
    else:
        if data['ok']:
            txt = data.get('chapter').get('cpContent')
        else:
            txt = '此来源暂不可用，请换源'
        if not txt:
            txt = data.get('chapter').get('body')
    return txt


def get_redis_string(key):
    if current_app.redis.exists(key):
        txt = current_app.redis.get(key).decode()
    else:
        return None
    return txt


def set_redis_string(key, txt):
    current_app.redis.set(key, str(txt), ex=86400)


def get_content_list(url, key=None):
    txt = None
    if key:
        txt = get_redis_string(key)
    if not key or txt is None:
        txt = get_content_text(url)
    lis = txt.split('\n')
    li = []
    for row in lis:
        if row != '' and row != '\t':
            li.append(row)
    return li


UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
LOCAL_FORMAT = '%Y-%m-%d %H:%M:%S'


def utc2local(utc_st):
    now_stamp = time()
    local_time = datetime.fromtimestamp(now_stamp)
    utc_time = datetime.utcfromtimestamp(now_stamp)
    offset = local_time - utc_time
    local_st = utc_st + offset
    return local_st


def local2utc(local_st):
    time_format = time.mktime(local_st.timetuple())
    utc_st = datetime.utcfromtimestamp(time_format)
    return utc_st


@bp.route('/book_detail', methods=['GET'])
@login_required
def book_detail():
    book_id = request.args.get('book_id')
    asyncio.set_event_loop(asyncio.new_event_loop())
    c = 0  # 标识当前阅读章节序号
    is_subscribe = False
    loop = asyncio.get_event_loop()
    tasks = list()
    res = dict()
    tasks.append(async_get_response(key='detail', url='http://api.zhuishushenqi.com/book/' + book_id, res=res))
    tasks.append(
        async_get_response(key='updated', url='http://api.zhuishushenqi.com/book?view=updated&id=' + book_id, res=res))
    if current_user.is_authenticated:
        s = current_user.subscribing.filter(Subscribe.book_id == book_id).first()
        if s:
            source_id = s.source_id
            c = int(s.chapter)
            is_subscribe = True
        else:
            source_id = get_source_id(book_id)
        tasks.append(async_get_response(
            key='chapters', url='http://api.zhuishushenqi.com/toc/{0}?view=chapters'.format(source_id), res=res))
    loop.run_until_complete(asyncio.wait(tasks))

    data = res.get('detail')
    t = datetime.strptime(res['updated'][0]['updated'], UTC_FORMAT)
    data['updated'] = t
    data['lastChapter'] = res['updated'][0]['lastChapter']
    lis = data.get('longIntro').split('\n')
    data['longIntro'] = lis
    chap = res['chapters']['chapters']
    last_index = None
    if chap[-1]['title'].split(' ')[-1] == data['lastChapter'].split(' ')[-1]:
        last_index = len(chap) - 1

    next_url = c + 1 if chap and len(chap) > c + 1 else None
    if c + 1 > len(chap):
        reading_chapter = chap[-1]['title']  # 防止换源之后章节数量越界
    else:
        reading_chapter = chap[c]['title']
    return render_template(
        'book_detail.html', data=data, lastIndex=last_index, reading=c, next=next_url, source_id=source_id,
        title=data.get('title'), readingChapter=reading_chapter, is_subscribe=is_subscribe)


@bp.route('/source/<book_id>', methods=['GET'])
@login_required
def source(book_id):
    page = request.args.get('page')
    # data = get_response('http://novel.juhe.im/book-sources?view=summary&book=' + book_id)
    data = get_response('http://api.zhuishushenqi.com/toc?view=summary&book=' + book_id)
    for s in data:
        UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
        t = datetime.strptime(s['updated'], UTC_FORMAT)
        s['updated'] = t
        # t = s['updated']
        # t = datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%fZ')
        # s['updated'] = utc2local(t).strftime('%Y-%m-%d %H:%M:%S')
    if not page:
        page = 0
    return render_template('source.html', data=data[1:], title='换源', page=page, book_id=book_id)


# 分类
@bp.route('/classify', methods=['GET'])
def classify():
    gender = request.args.get('gender')
    _type = request.args.get('type')
    major = request.args.get('major')
    start = request.args.get('start')
    # limit = request.args.get('limit')
    # page = request.args.get('page')
    # tag = request.args.get('tag')
    limit = str(Config.CHAPTER_PER_PAGE)
    # data = get_response(
    #     'https://novel.juhe.im/category-info?' + (('&major=' + major) if major else '') + (
    #         ('&gender=' + gender) if gender else '') + (('&type=' + _type) if _type else '') + (
    #         ('&start=' + start) if start else '') + (('&limit=' + limit) if limit else ''))
    data = get_response(
        'http://api.zhuishushenqi.com/book/by-categories?' + (('&major=' + major) if major else '') + (
            ('&gender=' + gender) if gender else '') + (('&type=' + _type) if _type else '') + (
            ('&start=' + start) if start else '') + (('&limit=' + limit) if limit else ''))
    data = data['books']
    next_page = True
    if len(data) < Config.CHAPTER_PER_PAGE:
        next_page = False
    return render_template('classify.html', data=data, title='探索', gender=gender, type=_type, major=major,
                           start=int(start),
                           limit=int(limit), next=next_page)


# 书单列表
@bp.route('/book_list_rank', methods=['GET'])
def book_list_rank():
    gender = request.args.get('gender')
    duration = request.args.get('duration')
    start = request.args.get('start')
    sort = request.args.get('sort')
    limit = '20'
    # tag = request.args.get('tag')
    # data = get_response('https://novel.juhe.im/booklists?' + (('&gender=' + gender) if gender else '') + (
    #     ('&start=' + start) if start else '') + (('&duration=' + duration) if duration else '') + (
    #                         ('&sort=' + sort) if sort else '') + (('&limit=' + limit) if limit else ''))
    data = get_response('http://api.zhuishushenqi.com/book-list?' + (('&gender=' + gender) if gender else '') + (
        ('&start=' + start) if start else '') + (('&duration=' + duration) if duration else '') + (
                            ('&sort=' + sort) if sort else '') + (('&limit=' + limit) if limit else ''))
    next_page = False
    if data['total'] > 0:
        next_page = True
    return render_template('book_list_rank.html', data=data, title='书单排行', gender=gender,
                           start=int(start), duration=duration, sort=sort, next_page=next_page, limit=20)


# 书单详情
@bp.route('/bool_list_detail<_id>', methods=['GET'])
@login_required
def book_list_detail(_id):
    # data = get_response('https://novel.juhe.im/booklists/' + _id)
    data = get_response('http://api.zhuishushenqi.com/book-list/' + _id)
    UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
    updated = datetime.strptime(data['bookList']['updated'], UTC_FORMAT)
    created = datetime.strptime(data['bookList']['created'], UTC_FORMAT)
    data['bookList']['updated'] = updated
    data['bookList']['created'] = created
    return render_template('book_list_detail.html', data=data, title=data['bookList']['title'])


# 排行榜
@bp.route('/rank/<_id>', methods=['GET'])
def rank(_id):
    # data = get_response('http://novel.juhe.im/rank/' + _id)
    data = get_response('http://api.zhuishushenqi.com/ranking/' + _id)
    if data:
        return render_template('rank.html', title='排行', data=data)


@bp.route('/download', methods=['GET'])
@login_required
def download():
    book_id = request.args.get('book_id')
    if not current_user.can_download:
        return render_template('permission_denied.html', title='权限不足', message='下载功能并非向所有人开放，请联系管理员索取权限')
    source_id = request.args.get('source_id')
    if not source_id:
        source_id = get_source_id(book_id)

    # data = get_response('http://novel.juhe.im/book-info/' + book_id)
    data = get_response('http://api.zhuishushenqi.com/book/' + book_id)
    book_name = data.get('title')

    d = Download.query.filter_by(book_id=book_id, source_id=source_id).first()

    # 检测资源锁
    if d:
        if d.lock:
            # 检测文件锁
            flash('文件正在生成，请稍后再试！')
            return redirect(url_for('main.book_detail', book_id=book_id))
        else:
            # 检测服务器是否已经下载了文件的最新版本
            # data = get_response('http://novel.juhe.im/book-sources?view=summary&book=' + source_id)
            data = get_response('http://api.zhuishushenqi.com/toc/{0}?view=chapters'.format(source_id))
            chapter_list = data.get('chapters')
            download_list = chapter_list[d.chapter + 1:]

            if len(download_list) == 0:
                # 如果不存在新章节，返回文件链接
                book_title = d.book_name
                fileName = md5((book_id + source_id).encode("utf8")).hexdigest()[:10] + '.txt'
                return render_template('view_documents.html', title=book_title + '--下载', url=text.url(fileName),
                                       book_title=book_title)

    # from app.tasks import download
    # download(source_id,book_id)

    # 进入后台任务处理流程
    # if current_user.get_task_in_progress('download'):
    #     flash('下载任务已经存在于您的任务列表当中！')
    # else:
    # 使用用户身份开启任务
    task = current_user.launch_task('download', book_name, source_id, book_id)
    db.session.commit()
    flash('下载任务已经提交，请稍后回来下载')
    return redirect(url_for('main.book_detail', book_id=book_id))


@bp.route('/background', methods=['GET'])
@login_required
def background():
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    return render_template('background.html', title='后台管理')


@bp.route('/user_list', methods=['GET'])
@login_required
def user_list():
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    users = User.query.all()
    lis = list()
    for u in users:
        lis.append((u.id, u.name, u.is_admin, u.last_seen if u.last_seen else None))

    return render_template('user_list.html', title='用户列表', lis=lis)


@bp.route('/user_detail/<id>', methods=['GET'])
@login_required
def user_detail(id):
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    u = User.query.get(id)
    dic = {
        'id': u.id,
        'name': u.name,
        'is_admin': u.is_admin,
        'can_download': u.can_download,
        'last_seen': u.last_seen if u.last_seen else None,
        'user_agent': u.user_agent,
        'user_ip': u.user_ip,
    }
    lis = list()
    for s in u.subscribing:
        lis.append({
            'book_id': s.book_id,
            'book_name': s.book_name,
            'source_id': s.source_id,
            'chapter': s.chapter,
            'chapter_name': s.chapter_name,
            'time': s.time if s.time else None
        })
    dic['subscribing'] = lis
    return render_template('user_detail.html', dic=dic, title='用户详情--%s' % u.name)


@bp.route('/change_download_permission/<id>', methods=['GET'])
@login_required
def change_download_permission(id):
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    u = User.query.get(id)
    if u.can_download:
        u.can_download = False
    else:
        u.can_download = True
    db.session.add(u)
    db.session.commit()
    flash('修改下载权限成功！')
    return redirect(url_for('main.user_detail', id=id))


@bp.route('/download_list', methods=['GET'])
@login_required
def download_list():
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    ds = Download.query.all()
    lis = list()
    path = os.path.join(Config.UPLOADS_DEFAULT_DEST, 'downloads')
    for d in ds:
        data = get_response('http://api.zhuishushenqi.com/toc/{0}?view=chapters'.format(d.source_id))
        source_name = data.get('name')
        if os.path.exists(os.path.join(path, d.txt_name)):
            txt_size = os.path.getsize(os.path.join(path, d.txt_name))
            txt_size = txt_size / float(1024 * 1024)
            txt_size = round(txt_size, 2)
        else:
            txt_size = '文件缺失'
        lis.append({
            'id': d.id,
            'user_id': d.user_id,
            'user_name': d.user.name,
            'book_name': d.book_name,
            'book_id': d.book_id,
            'chapter': d.chapter,
            'source_id': d.source_id,
            'source_name': source_name,
            'time': d.time if d.time else None,
            'txt_name': d.txt_name,
            'chapter_name': d.chapter_name,
            'txt_size': txt_size
        })
    return render_template('download_list.html', lis=lis, title='下载列表')


@bp.route('/delete_download_file/<id>', methods=['GET'])
@login_required
def delete_download_file(id):
    if not current_user.is_admin:
        return render_template('permission_denied.html', message=None, title='权限不足')
    d = Download.query.get(id)

    path = os.path.join(Config.UPLOADS_DEFAULT_DEST, 'downloads')
    if os.path.exists(os.path.join(path, d.txt_name)):
        os.remove(os.path.join(path, d.txt_name))
    db.session.delete(d)
    db.session.commit()
    flash('删除下载项目成功！')
    return redirect(url_for('main.download_list'))


@bp.route('/download_file/', methods=['GET'])
@login_required
def download_file():
    file_name = request.args.get('file_name')
    book_name = request.args.get('book_name')
    path = os.path.join(Config.UPLOADS_DEFAULT_DEST, 'downloads')
    if os.path.exists(os.path.join(path, file_name)):
        return render_template('view_documents.html', title='下载文件', url=text.url(file_name), book_title=book_name)


@bp.route('/get_task_progress', methods=['POST'])
@login_required
def get_task_progress():
    ids = json.loads(request.get_data())
    lis = []
    for task_id in ids:
        task = Task.query.filter_by(id=task_id).first()
        lis.append({
            'id': task.id,
            'progress': task.get_progress()
        })
    return jsonify(lis)


@bp.route('/read_setting/', methods=['GET', 'POST'])
@login_required
def read_setting():
    if request.method == 'GET':
        index = request.args.get('index')
        book_id = request.args.get('book_id=book_id')
        source_id = request.args.get('source_id')
        body = ['信用卡额度不是洪水猛兽，而是你进入更高一层的阶层的顺风车。',
                '96费改之后，银行已经是“睁只眼闭只眼”的状态，“充电五分钟，套现一百万”不仅仅是个段子。',
                '何不搭乘这趟快车，迅速提升自己的眼界和境界，让自己的阶层也能得到提升呢？',
                '须知，开十万的车和开五十万的车，你的交际圈的水平自然大有不同，别人看到你的第一印象，也是大有不同的。',
                '而至于短期内需要大笔资金而借钱难如登天的现状，相信每个读者都有切身体会。',
                '而高额信用卡+各种套现工具的组合，也是解决燃眉之急的成本最低的方式。',
                '假如你不是想要提升自己而是仅靠信用卡暂时获得虚荣或者其他物质方面的追求的读者，请你远离信用卡。',
                '那样会让你变成卡奴，滚雪球般的债务很快会将你拖入万劫不复的深渊',
                '而真正有本领怀才不遇却被五斗米折腰的有志青年，信用卡额度是你快速打通向上的通道的顺风车，。',
                '它给你带来的不仅仅是银行的羊毛这样的蝇头小利，',
                '还有提升自身的最长久的投资']
        next_url = url_for('main.read', index=index, book_id=book_id, source_id=source_id)
        return render_template('read_setting.html', title='阅读设置', body=body, next_url=next_url)
    if request.method == 'POST':
        data = json.loads(request.get_data())
        font_size = data.get('font_size')
        night_mode = data.get('night_mode')
        current_user.font_size = font_size
        current_user.night_mode = night_mode
        db.session.commit()
        return 1


@bp.route('/author/<author_name>', methods=['GET'])
@login_required
def author(author_name):
    data = get_response('http://api.zhuishushenqi.com/book/accurate-search?author=' + author_name)
    lis = list()
    for book in data['books']:
        lis.append({
            '_id': book['_id'],
            'title': book['title'],
            'cover': book['cover'],
            'retentionRatio': book['retentionRatio'],
            'latelyFollower': book['latelyFollower'],
            'author': author_name
        })
    return render_template('author.html', title=author_name, lis=lis)
