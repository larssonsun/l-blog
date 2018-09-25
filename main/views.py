#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import datetime
import hashlib
import json
import re
import uuid
from collections import namedtuple
from datetime import datetime
from functools import wraps

import aiohttp_jinja2
from aiohttp import web
from aiohttp_session import get_session

from models.db import (exeNonQuery, exeScalar, delete_cache, get_cache,
                       get_cache_ttl, select, set_cache)
from utils import (WhooshSchema, addDictProp, certivateMailHtml,
                   duplicateSqlRc, emailRc, getWhooshSearch, hash_md5,
                   mdToHtml, pwdRc, rtData, setAvatar, setWhooshSearch,
                   stmp_send_thread, userNameRc)


async def hello(request):
    return web.Response(body=b'<h1>Hello fucky! shity!</h1>', content_type="text/html", charset="utf-8")


def basePageInfo(func):
    """This function applies only to class views."""
    @wraps(func)
    async def wrapper(cls, *args, **kw):
        # do not know how to replace after 3 sentence with one
        curr = re.sub("hot", "", cls.request.path)
        curr = re.sub("time", "", curr)
        curr = re.sub("/*", "", curr)
        if len(curr) == 0:
            curr = "index"
        elif curr in ("archive", "about"):
            pass
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
                user = await select("""
                select a.`id`, a.`name`, a.`email`, count(b.id) as 'cmm_ct', a.`admin`from `users` a 
                left join `comments` b on a.`id` = b.`user_id` and b.`hide_status`= 0
                where a.`id`= %s
                group by a.`id`, a.`name`, a.`email`
                """, uid)
                if not user or len(user) != 1:
                    if cls.request.app.get("l_data"):
                        cls.request.app.pop("l_data")
                else:
                    ava = setAvatar(user[0].get("email"))
                    user[0]["avatar"] = ava.get("avatarAdmin") if user[0].get(
                        "name") == "larsson" else ava.get("avatarNormal")
                    cls.request.app.l_data = user[0]
                return await func(cls, *args, **kw)
            else:
                cls.request.app.l_data = None
                pth = cls.request.path
                if a:
                    if pth in ("/blogdetail/addComment", "/blogdetail/delComment"):
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


async def sendCerMain(*, cerUrl, userId, uname, mailAddr):
    #send certificate mail to registed email address
    rtd = None
    mailCerExpert = 70
    mailCerPerSec = 2
    approveExpert = 320
    smc = await get_cache("sendMail_minute")
    smc = 0 if not smc else smc
    if smc < mailCerPerSec:
        approvedKey = hash_md5(str(uuid.uuid4()))
        await set_cache(approvedKey, userId, ttl=approveExpert)
        await set_cache("sendMail_minute", smc + 1, ttl=mailCerExpert)
        stmp_send_thread(mailAddr, "l-blog 邮箱验证", certivateMailHtml.format(
            targetUserName=uname,
            describ="欢迎注册，您现在可以通过点击下方的按钮完成邮箱验证。",
            certificateButtonTxt="验证邮箱",
            certificateHref=f"{ cerUrl }{ approvedKey }/"
        ))
        rtd = rtData(
            error_code=-1, error_msg=f"一封邮件已发送至您的邮箱,\r\n请于{ int(approveExpert / 60) }分钟内完成验证。", data=dict(waits=mailCerExpert))
    else:
        ttl = await get_cache_ttl("sendMail_minute")
        rtd = rtData(error_code=10008,
                     error_msg=f"验证邮件发送受限，请于 {ttl}秒后再试", data=dict(waits=ttl))
    return rtd


async def setRightSideInclude(tagId=None, catelogid=None):
    #tags
    tags = await select("select `id`, `tag_name`, `blog_count` as `bct` from `tags` where `blog_count` > 0 order by `id`")
    [addDictProp(tg, "current", tg.get("id") == tagId) for tg in tags]

    #catelogs
    catelogs = await select("select `id`, `catelog_name`, `blog_count` as `bct` from `catelog` where `blog_count` > 0 order by `id`")
    [addDictProp(cate, "current", cate.get("id") == catelogid)
        for cate in catelogs]

    #friendly conns
    friCnns = await select("select `name`, `url` from `friendlyconn`")

    return tags, catelogs, friCnns


class Logout(web.View):
    async def get(self):
        self.request.app.l_data = None
        session = await get_session(self.request)
        if session:
            session.clear()
        location = self.request.app.router["Index"].url_for()
        return web.HTTPFound(location=location)


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


class Approve(web.View):
    async def post(self):
        postData = await self.request.post()
        loginName = postData.get("username")
        rtd = rtData(error_code=-1, error_msg="", data=None)
        if not emailRc.match(loginName) and not userNameRc.match(loginName):
            rtd = rtData(error_code=40001,
                         error_msg="请输入正确格式的email或昵称", data=None)
        else:
            user = await select("select `id`, `name`, `email`, `approved` from `users` where `name`=%s or `email`=%s limit 0, 1", loginName, loginName)
            if not user or len(user) != 1:
                rtd = rtData(error_code=40002,
                             error_msg="未注册该邮箱或昵称", data=None)
            else:
                user = user[0]
                if b"\x01" == user.get('approved'):
                    rtd = rtData(error_code=40003,
                                 error_msg="目标账号已经激活，无需重复操作", data=None)
                else:
                    rtd = await sendCerMain(
                        cerUrl=f"{self.request.scheme}:/{self.request.host}{self.request.app.router['registe'].url_for()}",
                        userId=user.get("id"),
                        uname=user.get("name"),
                        mailAddr=user.get("email"))

        return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class Registe(web.View):
    async def get(self):
        # #f"{ self.request.url }/registe/{approvedKey}"
        keyCur = True
        approvedKey = self.request.match_info["approvedKey"]

        if not approvedKey:
            keyCur = False

        userId = await get_cache(approvedKey)
        if not userId:
            keyCur = False

        if keyCur:
            i = await exeNonQuery("update `users` set `approved`=1 where `id`=%s", userId)
            if i == 1:
                session = await get_session(self.request)
                if session:
                    session.pop("uid")
                session = await get_session(self.request)
                session['uid'] = userId
                await expert_cache(approvedKey)
                welcomeVm = dict(title="欢迎!", discrib="您已经完成注册。")
                return aiohttp_jinja2.render_template("welcome.html", self.request, welcomeVm)
            else:
                raise web.HTTPForbidden(text="帐号激活失败。")
        else:
            raise web.HTTPForbidden(text="您无法进行未授权的邮箱验证。")

    async def post(self):
        postData = await self.request.post()
        email = postData.get("email")
        uname = postData.get("username")
        pwd = postData.get("pwd")
        repwd = postData.get("repwd")
        userId = str(uuid.uuid4())

        rtd = rtData(
            error_code=-1, error_msg="", data=None)
        if not emailRc.match(email):
            rtd = rtData(error_code=10001, error_msg="邮箱格式不正确", data=None)
        elif not userNameRc.match(uname):
            rtd = rtData(error_code=10004,
                         error_msg="昵称必须是6到18位的字母或数字", data=None)
        elif not pwd == repwd:
            rtd = rtData(error_code=10003, error_msg="两次密码输入不一致", data=None)
        elif not pwdRc.match(pwd) or not pwdRc.match(repwd):
            rtd = rtData(error_code=10002,
                         error_msg="密码必须是6到18位的字母数字或下划线", data=None)

        if rtd.error_code == -1:
            try:
                i = await exeNonQuery("INSERT INTO users (`id`, `email`, `passwd`, `admin`, \
                `name`, `image`, `created_at`, `approved`) VALUES (%s, %s, %s, 0, LOWER(%s), '', %s, 0);",
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

        if rtd.error_code == -1:
            rtd = await sendCerMain(cerUrl=self.request.url, userId=userId, uname=uname, mailAddr=email)
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
                a.`browse_count` as `readCount`, a.`source_from`, a.`name_en`, a.`title_image`, c.`catelog_name`
            from `blogs` a
            inner join `catelog` c on c.`id` = a.`catelog`
            left join `comments` b on a.`id` = b.`blog_id` and LENGTH(b.`parent_comment_id`)=0
            where a.`id` is not null
            and { "`tags` like (%s)" if tag else "0=%s" }
            and { "`catelog` = (%s)" if catelog else "0=%s" }
            group by a.`id`
            order by {"a.`created_at` desc" if not sortType or sortType == "time" else "a.`browse_count` desc" }
            """, f'%{tagId}%' if tag else int("0"), catelogid if catelog else int("0"))

        #right side include
        tags, catelogs, friCnns = await setRightSideInclude(tagId, catelogid)

        return aiohttp_jinja2.render_template("index.html", self.request, locals())

    async def delete(self):
        return "wow webapi!"


class BlogDetail(web.View):

    def setAvatarIntoCmm(self, comms):
        ava = setAvatar(None)

        [addDictProp(cmm, "avatar",
                     ava.get("avatarNormal").format(hashlib.md5(cmm.get("email").encode("utf-8").lower()).hexdigest()) if cmm.get("user_name") != "larsson"
                     else ava.get("avatarAdmin"))
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

            #article read count
            currentbrowse_count = 0
            session = await get_session(self.request)
            uid = session.get("uid")
            if blog.get("user_id") != uid:
                readBeginTime = session.get(blog.get("id"))
                if not readBeginTime or datetime.now().timestamp() - readBeginTime > 40 * 60:
                    i = await exeNonQuery("update `blogs` set `browse_count` = `browse_count` + 1 where `id` = %s", blog.get("id"))
                    if 1 == i:
                        session[blog.get("id")] = datetime.now().timestamp()

            #get newest browse_count
            currentbrowse_count = await exeScalar("select `browse_count` from `blogs` where `id` = %s", blog.get("id"))
            blog["browse_count"] = int(currentbrowse_count)

            #comments
            comments = await select("""
                select a.*, b.email, b.`admin` from `comments` a 
                inner join `users` b on a.`user_id` = b.`id`
                where a.`blog_id` = %s and length(a.`parent_comment_id`)=0 order by `created_at` desc
                """, blog.get("id"))
            commentCount = len(comments)
            cmmNo = (f'{str(x)} 楼' for x in range(commentCount, 0, -1))
            commentContentMaxLeng = 170
            #comm addon set
            self.setAvatarIntoCmm(comments)
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
                self.setAvatarIntoCmm(cfcsList)
                self.setAdminTag(cfcsList)

        #current url
        blogurl = self.request.url

        return aiohttp_jinja2.render_template("blogdetail.html", self.request, locals())


class AddComment(web.View):

    def validateComit(self, user_name, blog_user_name, toCommUserName, content):
        cttLimit = 800
        rtd = None

        if not toCommUserName:
            if user_name == blog_user_name:
                rtd = rtData(error_code=60003,
                             error_msg="不能回复自己的文章", data=None)

        if user_name == toCommUserName:
            rtd = rtData(error_code=60002, error_msg="不能回复自己的评论", data=None)

        if len(content) > cttLimit:
            rtd = rtData(error_code=60004,
                         error_msg=f"请精简您的发言，控制在{ cttLimit }字以内", data=None)

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

            rtd = self.validateComit(
                user_name, blog_user_name, toCommUserName, content)
            if not rtd:
                cmmId = str(uuid.uuid1())
                created_at = datetime.now().timestamp()
                ic = await exeNonQuery("insert into comments values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                                       cmmId, blog_id, user_id, user_name, "", content, created_at, "" if parent_comment_id is None else parent_comment_id,
                                       toCommUserName if isLv2Cm == "1" else "", 3)  # auto hide comment

                if(ic == 1):
                    rtd = rtData(error_code=-1, error_msg="发布成功", data=None)
                else:
                    rtd = rtData(error_code=60001,
                                 error_msg="未能成功提交评论", data=None)

            return web.json_response(data=dict(rtd._asdict()), dumps=json.dumps)


class DelComment(web.View):

    @login_required(True)
    async def post(self):
        data = await self.request.post()
        l_data = self.request.app.l_data
        if data and l_data:
            operUserId = l_data.get("id")
            cmmId = data.get("id")
            hideStatus = data.get("hide_status")
            curUserId = await exeScalar("select `user_id` from `comments` where `id` = %s limit 0, 1", cmmId)
            isAdmin = await exeScalar("select `admin` from `users` where `id` = %s limit 0, 1", operUserId)

            newStatus = None
            if curUserId == operUserId and isAdmin != "1":
                if hideStatus not in ("0", "2"):
                    rtd = rtData(error_code=50002,
                                 error_msg="您不能进行此操作", data=None)
                else:
                    newStatus = "0" if hideStatus == "2" else "2"

            elif isAdmin == "1":
                # set to display when status is "1" only
                newStatus = "0" if hideStatus == "1" else "1"

            else:
                rtd = rtData(error_code=50003,
                             error_msg="您不能操作其他人的评论", data=None)

            if newStatus:
                ic = await exeNonQuery("update `comments` set `hide_status`=%s where `id` = %s", newStatus, cmmId)
                if(ic == 1):
                    rtd = rtData(error_code=-1, error_msg="操作成功", data=None)
                else:
                    rtd = rtData(error_code=50001,
                                 error_msg="操作失败", data=None)

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

        #right side include
        tags, catelogs, friCnns = await setRightSideInclude()

        return aiohttp_jinja2.render_template("archive.html", self.request, locals())


class About(web.View):
    @login_required()
    @basePageInfo
    async def get(self):
        vm = {}

        #right side include
        tags, catelogs, friCnns = await setRightSideInclude()

        return aiohttp_jinja2.render_template("about.html", self.request, 
            {"vm": vm, "tags": tags, "catelogs": catelogs, "friCnns": friCnns})


class FullSiteSearch(web.View):

    @login_required(True)
    @basePageInfo
    async def post(self):
        vm = {}
        vm["results"] = []
        data = await self.request.post()
        partten = data.get("search")
        if partten and len(partten) > 20:
            partten = partten[:20]
        vm["keywords"] = partten
        results = getWhooshSearch(
            partten, "blog", ["title", "content"], ["title", "content"])
        vm["bct"] = 0
        if results:
            vm["bct"] = len(results)
            for hit in results:
               vm["results"].append(hit)

        #right side include
        tags, catelogs, friCnns = await setRightSideInclude()

        return aiohttp_jinja2.render_template("searchResult.html", self.request, locals())
