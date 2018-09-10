#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import namedtuple
from markdown import Markdown
from markdown.extensions.toc import TocExtension
import re

rtData = namedtuple("rtData", ["error_code", "error_msg", "data"])

emialRc = re.compile(r'^[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$') 
pwdRc  = re.compile(r'^[0-9a-zA-Z\_]{6,18}$')
userNameRc  = re.compile(r'^[0-9a-zA-Z]{6,12}$')

def addDictProp(dct, newProp, prpoVal):
    dct[newProp] = prpoVal

def mdToHtml(mdStr):
    md = Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.toc'
    ])
    #TocExtension实例用替代'markdown.extensions.toc'时
    #slugify 参数可以接受一个函数作为参数，这个函数将被用于处理标题的锚点值。Markdown 内置的处理方法不能处理中文标题
    html = md.convert(mdStr)
    toc = md.toc
    return html, toc
