#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from aiohttp import web
from config.settings import FEED_DIR

class Feeds_Atom(web.View):
    async def get(self):
        return web.FileResponse(f"{FEED_DIR}/atom.xml")

class Feeds_Rss(web.View):
    async def get(self):
        return web.FileResponse(f"{FEED_DIR}/rss.xml")
