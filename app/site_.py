#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
from aiohttp import web
from project.app.config.settings import FEED_DIR, SITEMAP_DIR, ROBOTS_DIR

class Feeds_Atom(web.View):
    async def get(self):
        return web.FileResponse(f"{FEED_DIR}/atom.xml")

class Feeds_Rss(web.View):
    async def get(self):
        return web.FileResponse(f"{FEED_DIR}/rss.xml")

class Sitemap(web.View):
    async def get(self):
        return web.FileResponse(f"{SITEMAP_DIR}/sitemap.xml")

class Robots(web.View):
    async def get(self):
        return web.FileResponse(f"{ROBOTS_DIR}/robots.txt")
