#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import datetime
import hashlib
import json
import re
import urllib
import uuid
from collections import namedtuple
from datetime import datetime
from functools import wraps

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from application.utils import (addDictProp, duplicateSqlRc, emialRc, hash_md5,
                               mdToHtml, pwdRc, rtData, stmp_send_thread,
                               userNameRc)
from models.db import exeNonQuery, exeScalar, get_cache, select, set_cache, get_cache_ttl


async def hello(request):
    return web.Response(body=b'<h1>Hello fucky! shity!</h1>', content_type="text/html", charset="utf-8")


def basePageInfo(func):
    """This function applies only to class views."""
    @wraps(func)
    async def wrapper(cls, *args, **kw):
        # do not know how to replace last 3 sentence with one
        curr = re.sub("hot", "", cls.request.path)
        curr = re.sub("time", "", curr)
        curr = re.sub("/*", "", curr)
        if len(curr) == 0:
            curr = "index"
        elif curr == "archive":
            curr = "archive"
        else:
            curr = None
        cls.request.app.site_status = dict(currMenuItem=curr)
        return await func(cls, *args, **kw)

    return wrapper


def login_required(*a):
    """This function applies only to class views."""
    def decorater(func):
        @wraps(func)
        async def inner(cls, *args, **kw):
            session = await get_session(cls.request)
            uid = session.get("uid")
            if uid:
                user = await select('select id, name, email from users where id = %s', uid)
                if not user or len(user) != 1:
                    if cls.request.app.get("l_data"):
                        cls.request.app.pop("l_data")
                else:
                    cls.request.app.l_data = user[0]
                return await func(cls, *args, **kw)
            else:
                cls.request.app.l_data = None
                pth = cls.request.path
                if a:
                    if pth in "/blogdetail/addComment":
                        rtd = rtData(error_code=30001,
                                     error_msg="请先登录", data=None)
                        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)
                    else:
                        return web.Response(status=302, headers={'location': '/login'})
                else:
                    return await func(cls, *args, **kw)
        return inner
    return decorater


async def getTags(*blogTags):
    if blogTags and len(blogTags) == 1:
        blogTags = blogTags[0].split(",")
        ps = []
        [ps.append("%s") for tag in blogTags]
        ps = ",".join(ps)
        tags = await select(f"""
        select `id`, `tag_name`, blog_count as `bct` from `tags` where `id` in ({ps}) order by `id`
        """, *blogTags)
    else:
        #tag
        tags = await select("select `id`, `tag_name`, blog_count as `bct` from `tags` where `blog_count` > 0 order by `id`")

    return tags


class Logout(web.View):
    async def get(self):
        self.request.app.l_data = None
        session = await get_session(self.request)
        if session:
            session.clear()
        headers = self.request.headers
        host = headers.get("host")
        referer = headers.get("Referer")
        if referer:
            referPath = referer.split(host)[-1]
        else:
            referPath = "/"
        return web.Response(status=302, headers={"location": referPath})


class Login(web.View):
    async def post(self):
        postData = await self.request.post()
        loginName = postData.get("username")
        pwd = postData.get("pwd")
        hashedPwd = hash_md5(pwd)
        userDct = await select("select `id`, `email`, `passwd`, `approved`, `name` from `users` \
            where `email` = %s or `name` = %s", loginName, loginName)
        if not userDct or len(userDct) != 1:
            rtd = rtData(error_code=20003, error_msg="该用户不存在", data=None)
            return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)
        userDct = userDct[0]

        if hashedPwd != userDct.get('passwd'):
            rtd = rtData(error_code=20004, error_msg="密码错误", data=None)
            return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)

        if b"\x01" != userDct.get('approved'):
            rtd = rtData(error_code=20005, error_msg="帐号尚未激活", data=None)
            return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)

        session = await get_session(self.request)
        session['uid'] = userDct.get('id')
        rtd = rtData(error_code=-1, error_msg="登录成功", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class Registe(web.View):
    async def get(self):
        
        # #f"{ self.request.url }/registe/{approvedKey}"
        approvedKey = self.request.match_info["approvedKey"]
        userId = await get_cache(approvedKey)
        print(userId)

        # session = await get_session(self.request)
        # if session:
        #     session.pop("uid")

        # session = await get_session(self.request)
        # session['uid'] = userId

        return web.Response(body=(f'<h1>{userId}</h1>').encode("utf-8"), content_type="text/html", charset="utf-8")

    async def post(self):
        postData = await self.request.post()
        email = postData.get("email")
        uname = postData.get("username")
        pwd = postData.get("pwd")
        repwd = postData.get("repwd")
        userId = str(uuid.uuid4())

        rtd = rtData(
            error_code=-1, error_msg="确认邮件已发送至您的注册邮箱,\r\n请于5分钟内根据其中提示完成注册。", data=None)
        if not emialRc.match(email):
            rtd = rtData(error_code=10001, error_msg="邮箱格式不正确", data=None)
        elif not userNameRc.match(uname):
            rtd = rtData(error_code=10004,
                         error_msg="昵称必须是6到12位的字母或数字", data=None)
        elif not pwd == repwd:
            rtd = rtData(error_code=10003, error_msg="两次密码输入不一致", data=None)
        elif not pwdRc.match(pwd) or not pwdRc.match(repwd):
            rtd = rtData(error_code=10002,
                         error_msg="密码必须是6到18位的字母数字或下划线", data=None)

        if rtd.error_code == -1:
            try:
                i = await exeNonQuery("INSERT INTO users (`id`, `email`, `passwd`, `admin`, \
                `name`, `image`, `created_at`, `approved`) VALUES (%s, %s, %s, 0, %s, '', %s, 0);",
                                      userId, email, hash_md5(pwd), uname, datetime.now().timestamp())
                if 1 != i:
                    rtd = rtData(error_code=10009,
                                 error_msg="意外地未能成功注册", data=None)
            except Exception as ex:
                try:
                    if duplicateSqlRc.match(ex.args[1]):
                        rtd = rtData(error_code=10006,
                                     error_msg="昵称或邮箱已经被使用", data=None)
                except:
                    rtd = rtData(error_code=10007,
                                 error_msg="注册过程中发生错误", data=None)

            #send certificate mail to target mailbox
            smc = await get_cache("sendMail_minute")
            smc = 0 if not smc else smc
            if smc < 2:
                approvedKey = hash_md5(str(uuid.uuid4()))
                await set_cache(approvedKey, userId, ttl=320)
                await set_cache("sendMail_minute", smc + 1, ttl=90)
                stmp_send_thread(email, "l-blog注册验证",
                        f"<div><a href='{ self.request.url }{ approvedKey }/'>请按此进行验证</a><div>")

                # print(f"{ self.request.url }{ approvedKey }/")
            else:
                ttl = await get_cache_ttl("sendMail_minute")
                rtd = rtData(error_code=10008,
                                     error_msg=f"验证邮件发送受限，请于 {ttl}秒后再试", data=None)
        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class Index(web.View):

    @login_required()
    @basePageInfo
    async def get(self):

        #for tag filter
        tagId = self.request.match_info.get("tagId")
        tag = None
        if tagId:
            tag = await select("select `tag_name` as `tagName`, `tag_discrib` as `tagDiscrib`, `blog_count` as `bct`  \
                from `tags` where `id` = %s limit 1 offset 0", tagId)
            tag = tag[0]
            sortFurtUrl = ""

        #for catelog filter
        catelogid = self.request.match_info.get("cateId")
        catelog = None
        if catelogid:
            catelog = await select("select `catelog_name` as catelogName, `catelog_discrib` as `catelogDiscib`, `blog_count` as `bct` \
                 from `catelog` where `id` = %s limit 1 offset 0", catelogid)
            catelog = catelog[0]

        #fot sort
        sortType = self.request.match_info.get("type")

        #blog
        articals = await select(f"""
            select a.`id`, a.`user_name`, a.`name`, a.`summary`, a.`created_at`, count(b.`id`) as `commentCount`,
                a.`browse_count` as `readCount`, a.`source_from`, a.`name_en`
            from `blogs` a
            left join `comments` b on a.`id` = b.`blog_id` and LENGTH(b.`parent_comment_id`)=0
            where a.`id` is not null
            and { "`tags` like (%s)" if tag else "0=%s" }
            and { "`catelog` = (%s)" if catelog else "0=%s" }
            group by a.`id`
            order by {"a.`created_at` desc" if not sortType or sortType == "time" else "a.`browse_count` desc" }
            """, f'%{tagId}%' if tag else int("0"), catelogid if catelog else int("0"))

        #tags
        tags = await select("select `id`, `tag_name`, `blog_count` as `bct` from `tags` where `blog_count` > 0 order by `id`")
        [addDictProp(tg, "current", tg.get("id") == tagId) for tg in tags]

        #catelogs
        catelogs = await select("select `id`, `catelog_name`, `blog_count` as `bct` from `catelog` where `blog_count` > 0 order by `id`")
        [addDictProp(cate, "current", cate.get("id") == catelogid)
         for cate in catelogs]

        return aiohttp_jinja2.render_template("index.html", self.request, locals())

    async def delete(self):
        return "wow webapi!"


class BlogDetail(web.View):

    def setAvatar(self, comms):
        avatarAdmin = "../static/images/avatardemo.png"
        size = 40
        gravatar_url = "http://www.gravatar.com/avatar/{0}?"
        gravatar_url += urllib.parse.urlencode({'d': "mm", 's': str(size)})

        [addDictProp(cmm, "avatar",
                     gravatar_url.format(hashlib.md5(cmm.get("email").encode("utf-8").lower()).hexdigest()) if cmm.get("user_name") != "larsson"
                     else avatarAdmin)
            for cmm in comms]

    def setAdminTag(self, comms):
        [addDictProp(cmm, "admintag", None if cmm.get(
            "admin") == 0 else 1) for cmm in comms]

    async def setPrevNextBlog(self, currentBlog):
        index = currentBlog.get("index")
        names = await select(
            "select `name`, `name_en`, `index` from `blogs` where `index` in (%s, %s)  limit 2 offset 0", *(index-1, index+1))
        if names and len(names) >= 1:
            currentBlog["Prev" if int(names[0].get(
                "index")) < index else "Next"] = names[0].get("name_en")
            currentBlog["PrevName" if int(names[0].get(
                "index")) < index else "NextName"] = names[0].get("name")
            if len(names) == 2:
                currentBlog["Prev" if int(names[1].get(
                    "index")) < index else "Next"] = names[1].get("name_en")
                currentBlog["PrevName" if int(names[1].get(
                    "index")) < index else "NextName"] = names[1].get("name")

    async def get_blog_cache(self, k):
        blog = await get_cache(k)
        if blog:
            return blog
        else:
            return await self.set_blog_cache(k)

    async def set_blog_cache(self, k):
        blog = await select("select a.*, b.id as 'catelog_id', b.catelog_name from `blogs` a inner join `catelog` b on a.catelog=b.id where `name_en` = %s limit 1 offset 0", k)
        if len(blog) == 1:
            blog = blog[0]
            blogId = blog.get("id")
            blog["markDownedContent"], blog["toc"] = mdToHtml(
                blog.get("content"))

            #browse count
            session = await get_session(self.request)
            uid = session.get("uid")
            if uid and blog.get("user_id") != uid:
                readBeginTime = session.get(blogId)
                if readBeginTime:
                    if datetime.now().timestamp() - readBeginTime > 20 * 60:
                        i = await exeNonQuery("update `blogs` set `browse_count` = `browse_count` + 1 where `id` = %s", blogId)
                        if 1 == i:
                            session[blogId] = datetime.now().timestamp()
                else:
                    session[blogId] = datetime.now().timestamp()

            #blog tags str
            blog["tagsStr"] = blog.get("tags")

            #blog tags
            blog["tags"] = await getTags(blog.get("tags"))

            #blog prev and next
            await self.setPrevNextBlog(blog)

            #set cache
            await set_cache(k, blog)

        return blog

    @login_required()
    @basePageInfo
    async def get(self):
        name_en = self.request.match_info["id"]

        #blog
        blog = await self.get_blog_cache(name_en)
        if blog:

            #comments
            comments = await select("""
                select a.*, b.email, b.`admin` from `comments` a 
                inner join `users` b on a.`user_id` = b.`id`
                where a.`blog_id` = %s and length(a.`parent_comment_id`)=0 order by `created_at` desc
                """, blog.get("id"))
            commentCount = len(comments)
            cmmNo = (f'{str(x)} 楼' for x in range(commentCount, 0, -1))
            #comm avatar
            self.setAvatar(comments)
            self.setAdminTag(comments)
            #comments for comments
            if commentCount > 0:
                cmmIdList = [cmm.get("id") for cmm in comments]
                inStr = ",".join(["%s" for i in range(0, commentCount)])
                cfcsList = await select(f"""
                select a.*, b.`email`, b.`admin` from `comments` a
                inner join `users` b on a.`user_id` = b.`id`
                where a.`parent_comment_id` in ({inStr}) order by a.`parent_comment_id`, a.`created_at` asc
                """,  *cmmIdList)
                #comm for comm avatar
                self.setAvatar(cfcsList)
                self.setAdminTag(cfcsList)

        #current url
        blogurl = self.request.url

        return aiohttp_jinja2.render_template("blogdetail.html", self.request, locals())


class AddComment(web.View):

    def validateComit(self, user_name, blog_user_name, toCommUserName):
        rtd = None
        if not toCommUserName:
            if user_name == blog_user_name:
                rtd = rtData(error_code=10003,
                             error_msg="不能回复自己的文章", data=None)
        elif user_name == toCommUserName:
            rtd = rtData(error_code=10002, error_msg="不能回复自己的评论", data=None)
        return rtd

    @login_required(True)
    async def post(self):
        data = await self.request.post()
        l_data = self.request.app.l_data
        if data:
            user_id = l_data.get("id")
            user_name = l_data.get("name")

            blog_user_name = data.get("blog_username")
            blog_id = data.get("blog_Id")
            content = data.get("content")

            parent_comment_id = data.get("parent_comment_id")
            toCommUserName = data.get("to_comm_username")
            isLv2Cm = data.get("isLv2Cm")

            rtd = self.validateComit(user_name, blog_user_name, toCommUserName)
            if not rtd:
                cmmId = str(uuid.uuid1())
                created_at = datetime.now().timestamp()
                ic = await exeNonQuery("insert into comments values (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                       cmmId, blog_id, user_id, user_name, "", content, created_at, "" if parent_comment_id is None else parent_comment_id,
                                       toCommUserName if isLv2Cm == "1" else "")

                if(ic == 1):
                    rtd = rtData(error_code=-1, error_msg="发布成功", data=None)
                else:
                    rtd = rtData(error_code=10001,
                                 error_msg="未能成功提交评论", data=None)

            return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class Archive(web.View):
    @login_required()
    @basePageInfo
    async def get(self):
        archiveVM = {}

        def getYM(f): return datetime.fromtimestamp(f).year

        def ifY(y, x): return y == x["year"]

        #archives
        archivesInY = []
        archives = await select("select `name`, `name_en`, `created_at` from `blogs` order by `created_at` desc")
        if archives:
            [addDictProp(achiv, "year", getYM(achiv.get("created_at")))
             for achiv in archives]
            cy = (y for y in range(datetime.now().year, 2016, -1))
            for y in cy:
                lstInY = [achiv if ifY(
                    y, achiv) else None for achiv in archives]
                if lstInY[0]:
                    archivesInY.append(dict(year=y, data=lstInY))

        archiveVM["archives"] = archivesInY
        archiveVM["bct"] = len(archives)

        #tags
        tags = await select("select `id`, `tag_name`, `blog_count` as `bct` from `tags` where `blog_count` > 0 order by `id`")

        #catelogs
        catelogs = await select("select `id`, `catelog_name`, `blog_count` as `bct` from `catelog` where `blog_count` > 0 order by `id`")

        return aiohttp_jinja2.render_template("archive.html", self.request, locals())
