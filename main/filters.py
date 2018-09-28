#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from datetime import datetime
from enum import Enum, unique

from utils import getCuttedStr

REC_LEAD = re.compile(r"\|lead\|(.*)\|leadend\|")
REC_MAIN = re.compile(r".*\|main\|(.*)\|mainend\|")
TITLE_IMG_IMG = re.compile(r".*(\|bgc\|.*\|bgcend\|)")
TITLE_IMG_BGC = re.compile(r".*\|bgc\|(.*)\|bgcend\|")
CATLOG_ICONTYPE = dict(
    original="原",
    transfer="转")
CATLOG_CSSTYPE = dict(
    original="l-cirlcle-icon-org",
    transfer="l-cirlcle-icon-trans")
CATLOG_TOOTIP = dict(
    original="原创",
    transfer="转帖")
SWITCH_i18n = dict(
    words_please=lambda x: "请",
    words_or=lambda x: "或者",
    words_forSendCmm=lambda x: "以便发表评论",
    blog_master=lambda x: "博主",
    blog_name_hide=lambda x: "当前位置",
    blog_send_count=lambda x: "博客数",
    blog_reply_count=lambda x: "回复数",
    default_meta_desctiption=lambda x: "本博客基于协程, 涉及python asyncio标准库、 aiohttp异步http框架等后端技术，前端使用Uikit3进行构建, 不断完善中",
    default_meta_keywords=lambda x: "l-blog,各人博客,web开发,python开发,python自学",
    default_title=lambda x: "L-blog 基于aiohttp和uikit搭建的各人博客",
    home_page=lambda x: "首页",
    author=lambda x: f"作者 {x}",
    archive_label=lambda x: "归档",
    archive_title=lambda x: "博客归档，网站所有博客概览",
    archive_discrib=lambda x: "博客归档，按年、月对博客进行分类、归档、排序",
    archive_keywords=lambda x: "博客归档",
    archive_menu_href=lambda x: "归档",
    about_label=lambda x: "关于",
    about_title=lambda x: "关于博客及作者介绍",
    about_discrib=lambda x: "本博客基于协程, 涉及python asyncio标准库、 aiohttp异步http框架等后端技术，前端使用Uikit3进行构建",
    about_keywords=lambda x: "关于网站,关于博客,关于作者,关于站长",
    about_menu_href=lambda x: "关于",
    timeline_title=lambda x: "博客建站历程, 时间轴",
    timeline_discrib=lambda x: "查看博客的建站历程, 时间轴",
    timeline_keywords=lambda x: "建站历程,时间轴,历史",
    timeline_label=lambda x: "时间轴",
    search_result_title=lambda x: "搜索结果",
    search_result_keywords=lambda x: "python,全文搜索,whoosh+jieba基本使用",
    search_result_discrib=lambda x: "本博客使用whoosh+jieba对博客的标题，内容进行分词存储，然后给每个分词建立索引。搜索时返回标题或者内容中包含目标关键字的博客。",
    search_result_label=lambda x: "当前搜索：",
    search_menu_href=lambda x: "博客搜索..",
    login_menu_href=lambda x: "登录",
    login_cencel=lambda x: "取消",
    login_ifforgetpwd=lambda x: "忘记密码?",
    login_approveusername=lambda x: "激活帐号",
    login_ph_username=lambda x: "邮箱/昵称",
    login_ph_pwd=lambda x: "密码",
    logo=lambda x: "",
    registe_menu_href=lambda x: "注册",
    right_slide_bar_logout=lambda x: "登出",
    created_at=lambda x: f" {x}",
    read_count=lambda x: f"阅读 {x}",
    read_count_t2=lambda x: f"阅读次数 {x}",
    comment_count=lambda x: f"评论 {x}",
    comment_count_t2=lambda x: f"评论次数 {x}",
    comment_count_right=lambda x: f"{x} 条评论",
    comment_need_log=lambda x, y, z: f"请先{y}或{z}，以便进行评论",
    reply=lambda x: "回复",
    user_reply_count=lambda x: "回复数",
    operate_reply=lambda x, y: "删除" if y == 0 else "恢复",
    send_reply=lambda x: "发表回复",
    cancel=lambda x: "取消",
    submit=lambda x: "发表",
    content=lambda x: "内容",
    tag=lambda x: "标签",
    catelog=lambda x: "分类",
    frientlyConn=lambda x: "友情链接",
    something=lambda x: "博客相关",
    watchfor_detail=lambda x: "查看详细信息",
    blogCountInTag=lambda x, y: f"标签 [{x}] 下有{y}篇blog",
    blogCountInCatelog=lambda x, y: f"分类 [{x}] 下有{y}篇blog",
    blog_url_left=lambda x: f"本文链接：{x}",
    blog_online_days=lambda x: "博客上线",
    filter_sum_count=lambda x: f"共 {x} 篇",
    footer_pages=lambda x: "页面",
    footer_contactme=lambda x: "联系方式",
    sort_time=lambda x: "时间排序",
    sort_hot=lambda x: "热度排序",
    e404_discrib=lambda x: "未能找到该页面",
    e500_discrib=lambda x: "服务端发生错误",
    welcome_toIndex=lambda x: "登录",
    project_git_address=lambda x: "https://github.com/larssonsun/l-blog")


@unique
class CommHideStatus(Enum):
    Normal = 0
    HideByAdmin = 1
    HideBySelf = 2
    HideBySystem = 3


def converWith3dot(content):
    return f"...{content}..."


def limitCmmLength(content, limitLen, hideType, therest=False):
    if hideType == CommHideStatus.Normal.value:
        return content[limitLen:] if therest else content[:limitLen]
    else:
        return "" if therest else content


def fmtGetHideInfo(content, hideType):
    if hideType == CommHideStatus.HideByAdmin.value:
        return "(此评论已由管理员删除)"
    elif hideType == CommHideStatus.HideBySelf.value:
        return "(此评论已由本人删除)"
    elif hideType == CommHideStatus.HideBySystem.value:
        return "(评论已提交，请等待管理员审核)"
    else:
        return content


def fmtGetHideClass(content):
    if content == CommHideStatus.Normal.value:
        return ""
    else:
        return "l-comment-body-banned"


def fmtCatelog(content, doType):
    if "iconType" == doType:
        return CATLOG_ICONTYPE.get(content)
    elif "tooltipType" == doType:
        return CATLOG_TOOTIP.get(content)
    elif "cssType" == doType:
        return CATLOG_CSSTYPE.get(content)


def fmtDatetimeFromFloat(flt, *, diff=False):
    if isinstance(flt, float):
        if diff:
            return f'created at {__getDateTimeDiff(datetime.fromtimestamp(flt))}'
        else:
            return datetime.fromtimestamp(flt).strftime("%Y-%m-%d %H:%M")


def fmtMonthDateFromFloat(flt):
    if isinstance(flt, float):
        return datetime.fromtimestamp(flt).strftime("%m-%d")


def fmtYearMonthDateFromFloat(flt):
    if isinstance(flt, float):
        return datetime.fromtimestamp(flt).strftime("%Y-%m-%d")


def fmtLabel(content, typeName, *parm):
    do = SWITCH_i18n.get(typeName)
    if not do:
        return content
    else:
        return do(content, *parm) if parm else do(content)


def fmtgetTitleImg(content, typeName):
    if 'img' == typeName:
        m = re.match(TITLE_IMG_IMG, content)
        if m:
            return content.replace(m.group(1), "")
        else:
            return content
    else:
        m = re.match(TITLE_IMG_BGC, content)
        if m:
            return m.group(1)
        else:
            return "#fff"


def __getDateTimeDiff(t):
    delta = (datetime.now() - t).total_seconds()
    if delta < 60:
        return '刚刚'
    if delta < 3600:
        return '%d分钟前' % (delta // 60)
    if delta < 86400:
        return '%d小时前' % (delta // 3600)
    if delta < 604800:
        return '%d天前' % (delta // 86400)
    else:
        return t.strftime("%Y-%m-%d %H:%M:%S")


def getArticalLead(content):
    m = re.match(REC_LEAD, content)
    if m:
        return m.group(1)
    else:
        return ""


def getArticalMain(content):
    m = re.match(REC_MAIN, content)
    if m:
        return m.group(1)
    else:
        return content


def getArticalFull(content, **kw):
    size = kw.get("size", 1)
    s = getCuttedStr(content, size)
    if s != content:
        return s + " ..."
    else:
        return s


def getCommentForComments(cfcsList, commentId):
    rtList = [cfc if cfc.get("parent_comment_id") ==
              commentId else None for cfc in cfcsList]
    return filter(lambda x: x, rtList)
