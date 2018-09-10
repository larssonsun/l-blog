#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from aiohttp import web
import aiohttp_jinja2
import jinja2, uuid, hashlib
from aiohttp_session import setup
from aiohttp_session.redis_storage import RedisStorage
from application.views import hello, Login, Index, BlogDetail, AddComment, Logout, Registe, Archive
from application import filters
from config.settings import TEMPLATE_DIR, STATIC_DIR

def setupRoutes(app):
    app.router.add_view("/hello", hello, name="Hello")
    app.router.add_view("/", Index, name="Index")
    app.router.add_view("/" + "{type:[hot|time]+}/", Index, name="index_sort")
    app.router.add_view("/archive/", Archive, name="archive")
    app.router.add_view("/tag/" + "{tagId:[0-9a-zA-Z\_]+}/", Index, name="tag")
    app.router.add_view("/tag/" + "{tagId:[0-9a-zA-Z\_]+}/" + "{type:[hot|time]+}/", Index, name="index_tag_sort")
    app.router.add_view("/catelog/" + "{cateId:[0-9a-zA-Z\_]+}/", Index, name="catelog")
    app.router.add_view("/catelog/" + "{cateId:[0-9a-zA-Z\_]+}/" + "{type:[hot|time]+}/", Index, name="index_catelog_sort")
    app.router.add_view("/blogdetail/" + "{id:[0-9a-zA-Z\-]+}/", BlogDetail, name="BlogDetail")
    app.router.add_view("/blogdetail/addComment", AddComment, name="add-comment")
    app.router.add_view("/login/", Login, name="Login")
    app.router.add_view("/logout/", Logout, name="logout")
    app.router.add_view("/registe/", Registe, name="registe")
    
    

def setupStaticRoutes(app):
    app.router.add_static('/static/', path=STATIC_DIR, append_version=True, name='static')

def setupTemplateRoutes(app):
    aiohttp_jinja2.setup(app, 
    filters={
        "fmtLabel" : filters.fmtLabel,
        "fmtCatelog" : filters.fmtCatelog,
        "fmtDatetimeFromFloat" : filters.fmtDatetimeFromFloat,
        "fmtMonthDateFromFloat" : filters.fmtMonthDateFromFloat,
        "getCommentForComments" : filters.getCommentForComments,
        "getArticalLead" : filters.getArticalLead,
        "getArticalMain" : filters.getArticalMain,
        "getArticalFull" : filters.getArticalFull},
    loader=jinja2.FileSystemLoader(TEMPLATE_DIR))

def setupSession(app, redis_pool):
    storage = RedisStorage(redis_pool=redis_pool, cookie_name='sessionid', key_factory=lambda: hash_sha256(uuid.uuid4().hex))
    setup(app, storage)

def hash_sha256(password):
    """sha256加密"""
    h = hashlib.sha256('henrik'.encode('utf-8'))
    h.update(password.encode('utf-8'))
    return h.hexdigest()