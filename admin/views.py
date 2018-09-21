#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from functools import wraps

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from utils import setWhooshSearch, WhooshSchema
from models.db import select

class ResetBlogIndex(web.View):
    dctTuple = (dict(
        id="aiohttp-publish-with-nginx-supervisor",
        title=u"aiohttp 部署 Nginx + supervisord",
        content=u"将aiohttp服务器组运行在nginx之后有好多好处。首先，nginx是个很好的前端服务器。它可以预防很多攻击如格式错误的http协议的攻击。第二，部署nginx后可以同时运行多个aiohttp实例，这样可以有效利用CPU。最后，nginx提供的静态文件服务器要比aiohttp内置的静态文件支持快",
        summary="将aiohttp服务器组运行在nginx之后有好多好处。首先，nginx是个很好的前端服务器。它可以预防很多攻击如格式错误的http协议的攻击。第二，部署nginx后可以同时运行多个aiohttp实"
    ),
        dict(
        id="python-slice",
        title=u"Python 切片",
        content=u"取一个list或tuple的部分元素是非常常见的操作。这里介绍一下python的高级特性之aiohttp一切",
        summary="取一个list或tuple的部分元素是非常常见的操作。"
    ))

    def setBlogSearch(self):
        setWhooshSearch("blog", WhooshSchema.Blogs, self.dctTuple)

    # @login_required(True)
    async def post(self):
        self.setBlogSearch()
