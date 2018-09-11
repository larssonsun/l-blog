#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#导入项目顶层路径方便导入模块
# import os
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# os.sys.path.append(BASE_DIR)
#或自定义一个pth文件放入site.getsitepackages()的第一个路径下。如果是x86则直接将路径加入\Lib\site-packages\pywin32.py中

import asyncio
import logging
from email.mime.text import MIMEText

import aiomysql
import aioredis
from aiocache import RedisCache
from aiocache.serializers import PickleSerializer
from aiosmtplib import SMTP

from config.settings import (CACHES_CONTENT, CACHES_SESSION, DATABASES,
                             MAIL_SMTPCLIENT)
from models.larsson_db_mysql_aio import MyPyAioMysql

# logging.basicConfig(level=logging.INFO)


def log(sql, args=()):
    logging.info('SQL: %s' % sql, *args)


async def create_pool(loop, **kw):
    logging.info('create database connection pool...')  # 定义mysql全局连接池
    global __mpams
    __mpams = MyPyAioMysql(host=DATABASES["host"], port=DATABASES["port"], user=DATABASES["user"],
                           pwd=DATABASES["password"], db=DATABASES["db"], dictionary=True, loop=loop)
    await __mpams.create_pool()
    return __mpams.pool


async def select(sql, *args):
    log(sql, args)
    return await __mpams.exeQuery(sql, *args)


async def exeScalar(sql, *args):
    log(sql, args)
    return await __mpams.exeScalar(sql, *args)


async def exeNonQuery(sql, *args):
    log(sql, args)
    return await __mpams.exeNonQuery(sql, *args)


async def create_redis_pool(loop):
    logging.info('create redis connection pool...')  # 定义redis全局连接池
    _redis_pool = await aioredis.create_pool(address=CACHES_SESSION['address'], db=CACHES_SESSION['db'], password=CACHES_SESSION['password'],
                                             minsize=CACHES_SESSION['minsize'], maxsize=CACHES_SESSION['maxsize'], loop=loop)
    return _redis_pool


async def create_cache(loop):
    logging.info('create cache ...')  # 定义cache
    global _cache
    _cache = RedisCache(serializer=PickleSerializer(), endpoint=CACHES_CONTENT['address'], port=CACHES_CONTENT["port"],
                        db=CACHES_CONTENT['db'], password=CACHES_CONTENT['password'], pool_min_size=CACHES_CONTENT['minsize'],
                        pool_max_size=CACHES_CONTENT['maxsize'], loop=loop, namespace="blog_cache")
    return _cache


async def get_cache(k):
    return await _cache.get(k)


async def set_cache(k, v):
    return await _cache.set(k, v)


async def create_smtp(loop):
    logging.info('create smtp connection ...')  # 定义smtp
    global _smptClient
    _smptClient = SMTP(
        hostname=MAIL_SMTPCLIENT['host'], port=MAIL_SMTPCLIENT['port'], use_tls=True, loop=loop)
    return _smptClient

# await stmp_send("l@scetia.com", "邮箱确认", f"<div><a href='{request.url}'>{request.url}<div>")
async def stmp_send(toAddr, subject, html):
    await _smptClient.connect()
    await _smptClient.login(MAIL_SMTPCLIENT['fromAddr'], MAIL_SMTPCLIENT['fromPwd'])
    message = MIMEText(html, "HTML", "utf-8")
    message['From'] = MAIL_SMTPCLIENT['fromAddr']
    message['To'] = toAddr
    message['Subject'] = subject
    await _smptClient.send_message(message)
    await _smptClient.quit()
