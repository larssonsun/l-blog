#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#导入项目顶层路径方便导入模块
# import os
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# os.sys.path.append(BASE_DIR)
#或自定义一个pth文件放入site.getsitepackages()的第一个路径下。如果是x86则直接将路径加入\Lib\site-packages\pywin32.py中
# import site;site.getsitepackages()
import asyncio
import logging

import aiomysql
import aioredis
from aiocache import RedisCache
from aiocache.serializers import PickleSerializer

from project.app.config.settings import CACHES_CONTENT, CACHES_SESSION, DATABASES
from project.app.models.larsson_db_mysql_aio import MyPyAioMysql

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


async def set_cache(k, v, ttl=None):
    return await _cache.set(k, v, ttl=ttl)


async def delete_cache(k):
    return await _cache.delete(k)


async def get_cache_ttl(k):
    return await _cache.raw("ttl", f"blog_cache:{k}".encode("utf-8"))
