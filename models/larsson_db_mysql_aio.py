#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aiomysql

class MyPyAioMysql(object):
	"""包装一下常用的持久化方法"""
	def __init__(self, *, host, port, user, pwd, db, loop, **kw):
		if not loop:
			raise "eventloop是必须的"
		if not isinstance(port, int):
			raise "port必须是数字"

		super(MyPyAioMysql, self).__init__()
		self.__host = host
		self.__port = port
		self.__user = user
		self.__pwd = pwd
		self.__db = db
		self.__loop = loop
		self.__charset = kw.get('charset', 'utf8')
		self.__autocommit = kw.get('autocommit', False),
		self.__maxsize = kw.get('maxsize', 10)
		self.__minsize = kw.get('minsize', 1)
		self.__dictionary = kw.get('dictionary', False)
		self.__pool = kw.get('pool', None)

	@property
	def pool(self):
		return self.__pool

	async def create_pool(self):
		global _mysql_pool
		self.__pool = await aiomysql.create_pool(host=self.__host, port=self.__port, user=self.__user, password=self.__pwd, 
			db=self.__db, loop=self.__loop, charset=self.__charset, autocommit=self.__autocommit, maxsize=self.__maxsize, 
			minsize=self.__minsize)

	async def exeScalar(self, sqlstr, *sqlparm):
		if not isinstance(sqlstr, str):
			raise "参数sqlstr仅支持单一sql语句"
		conn = None
		cur = None
		async with self.__pool.acquire() as conn:
			async with conn.cursor() as cur:
				try:
					await cur.execute(sqlstr, sqlparm)
					row = await cur.fetchall()
					await cur.close()
					return None if not row or len(row)<=0 else str(row[0][0])
				except Exception as e:
					raise e

	async def exeQuery(self, sqlStrs, *sqlparm):
		if not isinstance(sqlStrs, str) and not isinstance(sqlStrs, list):
			raise "参数sqlStrs仅支持字符串（单一sql）或者list（多sql语句）"
		conn = None
		cur = None
		rows = []
		async with self.__pool.acquire() as conn:
			async with conn.cursor(aiomysql.DictCursor if self.__dictionary else None) as cur:
				try:
					if isinstance(sqlStrs, list):
						for x in sqlStrs:
							if isinstance(x, str):
								await cur.execute(x)
							else:
								newX = None
								if len(x) > 2:
									newX = tuple([y for y in x[1:]])
								elif len(x) == 2:
									newX = (x[1],) if not isinstance(x[1], tuple) else x[1]
								await cur.execute(x[0], newX)
							tpl = await cur.fetchall()
							rows.append(list(tpl))
					elif isinstance(sqlStrs, str):
						await cur.execute(sqlStrs, sqlparm)
						rows = await cur.fetchall()
						rows = list(rows)
					await cur.close()
					return rows
				except Exception as e:
					raise e

	async def exeNonQuery(self, sqlStrs, *sqlparm):
		if not isinstance(sqlStrs, str) and not isinstance(sqlStrs, list):
			raise "参数sqlStrs仅支持字符串（单一sql）或者list（多sql语句）"
		conn = None
		cur = None
		rown = 0
		async with self.__pool.acquire() as conn:
			await conn.autocommit(self.__autocommit)# maybe some bugs here
			async with conn.cursor() as cur:
				try:
					if isinstance(sqlStrs, list):
						for x in sqlStrs:
							if isinstance(x, str):
								await cur.execute(x)
							else:
								newX = None
								if len(x) > 2:
									newX = tuple([y for y in x[1:]])
								elif len(x) == 2:
									newX = (x[1],) if not isinstance(x[1], tuple) else x[1]
								await cur.execute(x[0], newX)
							rown += cur.rowcount
					elif isinstance(sqlStrs, str):
						await cur.execute(sqlStrs, sqlparm)
						rown += cur.rowcount
						
					await cur.close()
					await conn.commit()
					return rown
				except Exception as e:
					if conn:
						await conn.rollback()
					raise e