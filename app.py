#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import uvloop
import argparse
import asyncio
import logging

from aiohttp import web

from application.middlewares import setup_middlewares
from application.routes import (setupRoutes, setupSession, setupStaticRoutes,
                                setupTemplateRoutes)
from models.db import create_cache, create_pool, create_redis_pool

logging.basicConfig(level=logging.INFO)


async def init(loop):
    mysql_pool = await create_pool(loop)
    redis_pool = await create_redis_pool(loop)
    cache = await create_cache(loop)

    async def dispose_mysql_pool():
        mysql_pool.close()
        await mysql_pool.wait_closed()

    async def dispose_redis_pool():
        redis_pool.close()
        await redis_pool.wait_closed()

    async def dispose_cache():
        await cache.close()

    async def dispose_sth(app):
        await dispose_mysql_pool()
        await dispose_redis_pool()
        await dispose_cache()

    app = web.Application(logger=logging.Logger)
    setupSession(app, redis_pool)
    setupRoutes(app)
    setup_middlewares(app)
    setupStaticRoutes(app)
    setupTemplateRoutes(app)
    app.on_cleanup.append(dispose_sth)
    return app


def main():
    parser = argparse.ArgumentParser(description="l-blog server start")
    parser.add_argument('--host', type=str,
                        default='localhost', help='this is a host')
    parser.add_argument('--port', type=str, default='9000',
                        help='this is a port')
    args = parser.parse_args()
    # # uvloop 是 asyncio 默认事件循环的一个代替品，实现的功能完整，且即插即用。uvloop 是用 Cython 写的，建于 libuv 之上。
    # # uvloop 可以使 asyncio 更快。事实上，它至少比 nodejs、gevent 和其他 Python 异步框架要快 两倍 。基于 uvloop 的 asyncio 的速度几乎接近了 Go 程序的速度。
    # # 该模块不支持windows....wocao.... 
    # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    web.run_app(init(loop), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
