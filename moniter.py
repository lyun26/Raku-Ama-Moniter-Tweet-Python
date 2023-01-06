from selectorlib import Extractor
import requests, lxml
from bs4 import BeautifulSoup, SoupStrainer
import threading
import time, random
import velocity

import tweepy

import mysql.connector
import json
from datetime import datetime

from playwright.sync_api import sync_playwright 

import sys
import locale

from amazon_paapi import AmazonApi
from amazon_paapi import get_asin

from twitter_text import parse_tweet

extract_amazon_search = Extractor.from_yaml_file('amazon_search_results.yml')
extract_amazon_item_variables = Extractor.from_yaml_file('amazon_item_variables.yml')

extract_rakuten_search = Extractor.from_yaml_file('rakuten_search_results.yml')


is_debug = False

class Auto_Class():
	def __init__(self):
		self.database_busy = False
		self.const_headers_rakuten = self.InitHeadersRakuten()
		self.const_headers_amazon = self.InitHeadersAmazon()
		
		
		self.tweetLastTime = [0, 0, 0, 0, 0]
		self.tweetCount = [0, 0, 0, 0, 0]
		

		self.setMysql()

		# Load Setting
		
		self.mySetting = {}
		self.mySetting['detail'] = {}
		self.getSetting()

		self.initTweetRecord()

		self.amazon_thread_ids = []
		self.rakuten_thread_ids = []

		self.initTweetSaves()
		self.initErrorSaves()


		

		

	def setMysql(self):
		self.mydb = mysql.connector.connect(
			host="localhost",
			port='3306',
			user="root",
			password="Com_123456",
			# password="",
			database="twitter_amazon",
			auth_plugin='mysql_native_password',
			# autocommit=True
		)

		self.mycursor = self.mydb.cursor()

	def test(self):
		content_format = "asdfdasfdas\n{}\nfdsafsa"
		content_target = "dfasfd"
		content = self.change_tweet_len(content_format, content_target)
		print(content)
		pass
	
	
	def getRakutenAffiliateUrl(self, url_str, product_id, image_url=''):
		if url_str:
			if product_id:
				arr = url_str.split('item.rakuten.co.jp/')
				if len(arr)==2:
					arr = arr[1].split('/')
					if len(arr)>1:
						try:
							shop_code = arr[0]
							request_url = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706?format=json&itemCode=%s:%s&affiliateId=%s&applicationId=%s'%(shop_code, product_id, self.mySetting['detail']['rk_affiliate_id'], self.mySetting['detail']['rk_application_id'])
							session = requests.Session()
							headers = self.GetHeadersRakutenAPI()
							session.headers.update(headers)	
							r = session.get(request_url, timeout=25)
							json_data = json.loads(r.text)
							return json_data['Items'][0]['Item']['affiliateUrl']
						except:
							pass
		if image_url:
			arr = image_url.split('tshop.r10s.jp/')
			if len(arr)>1:
				arr = arr[1].split("/")
				if len(arr)>1:
					shop_code = arr[0]
					if product_id:
						try:
							request_url = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706?format=json&itemCode=%s:%s&affiliateId=%s&applicationId=%s'%(shop_code, product_id, self.mySetting['detail']['rk_affiliate_id'], self.mySetting['detail']['rk_application_id'])
							session = requests.Session()
							headers = self.GetHeadersRakutenAPI()
							session.headers.update(headers)	
							r = session.get(request_url, timeout=25)
							json_data = json.loads(r.text)
							return json_data['Items'][0]['Item']['affiliateUrl']
						except:
							pass

		return url_str

	def proxyUpdateDate(self):
		arr_i = []
		for j in range(len(self.mySetting['proxy'])):
			min_count = 10000000
			min_i = -1
			for i in range(len(self.mySetting['proxy'])):
				if not (i in arr_i):
					if min_count>self.mySetting['proxy'][i]['count']:
						min_count = self.mySetting['proxy'][i]['count']
						min_i = i

			if min_i>=0:
				arr_i.append(min_i)
				self.mySetting['proxy'][min_i]['count'] = j

		for i in range(len(self.mySetting['proxy'])):
			if not (i in arr_i):
				self.mySetting['proxy'][i]['count'] = len(self.mySetting['proxy'])


		for i in range(len(self.mySetting['proxy'])):
			self.mySetting['proxy'][i]['status'] = 1
			self.proxy_set_database(self.mySetting['proxy'][i]['id'], self.mySetting['proxy'][i]['status'], self.mySetting['proxy'][i]['count'], self.mySetting['proxy'][i]['in_use'])
			self.mySetting['proxy'][i]['need_save'] = 0
			time.sleep(0.05)

	def run(self):
		count_proxy_all = 0
		count_proxy_all_limit = 20

		count_rakuten_save = 0
		count_rakuten_save_limit = 11

		count_amazon_save = 0
		count_amazon_save_limit = 13

		self.rakuten_thread_ids = []
		self.amazon_thread_ids = []
		self.amazon_thread_asin_api = False
		self.amazon_access_count_asin_api = 0
		while 1:
			try:
				for i in range(len(self.mySetting['rakuten'])):
					if not (i in self.rakuten_thread_ids):
						self.rakuten_thread_ids.append(i)
						token_thread = threading.Thread(target=self.rakuten_get, args=(i,))
						token_thread.start()
						continue

				if count_rakuten_save>=count_rakuten_save_limit:
					for i in range(len(self.mySetting['rakuten'])):
						self.rakuten_set_database(self.mySetting['rakuten'][i]['id'], json.dumps(self.mySetting['rakuten'][i]['data']), self.mySetting['rakuten'][i]['status'])
						time.sleep(0.1)
					count_rakuten_save = 0
				else:
					count_rakuten_save = count_rakuten_save + 1



				
				for i in range(len(self.mySetting['amazon'])):
					if self.mySetting['detail']['asin_api'] == 1 and self.mySetting['amazon'][i]['type']==1:
						if self.amazon_thread_asin_api==False:
							self.amazon_thread_asin_api=True
							token_thread = threading.Thread(target=self.amazon_get_item_asin_api)
							token_thread.start()
							continue
					else:
						if not (i in self.amazon_thread_ids):
							self.amazon_thread_ids.append(i)
							token_thread = threading.Thread(target=self.amazon_get_item, args=(i,))
							token_thread.start()
							continue

				if count_amazon_save>=count_amazon_save_limit:
					for i in range(len(self.mySetting['amazon'])):
						data_item = self.mySetting['amazon'][i]['data']					
						if data_item or data_item=={}:
							self.amazon_set_database(self.mySetting['amazon'][i]['id'], json.dumps(data_item), self.mySetting['amazon'][i]['status'])
						time.sleep(0.1)
					count_amazon_save = 0
				else:
					count_amazon_save = count_amazon_save + 1




				self.calProxyInUse()
				if self.mySetting['detail']['today_str'] == datetime.now().strftime('%Y-%m-%d'):
					if count_proxy_all>=count_proxy_all_limit:
						for i in range(len(self.mySetting['proxy'])):
							self.proxy_set_database(self.mySetting['proxy'][i]['id'], self.mySetting['proxy'][i]['status'], self.mySetting['proxy'][i]['count'], self.mySetting['proxy'][i]['in_use'])
							time.sleep(0.1)
						count_proxy_all = 0
					else:
						count_proxy_all = count_proxy_all + 1
				else:
					self.amazon_access_count_asin_api = 0
					self.mySetting['detail']['today_str'] = datetime.now().strftime('%Y-%m-%d')  # when the date changed
					self.proxyUpdateDate()
					self.clearTweetRecord()

				self.saveMainSetting('today_str', self.mySetting['detail']['today_str'])



				is_updated_database = self.getUpdatedDatabase()
				if is_updated_database==1:
					self.database_busy = True
					while 1:
						if len(self.rakuten_thread_ids)==0 and len(self.amazon_thread_ids)==0 and self.amazon_thread_asin_api==False:
							break
						time.sleep(1)


					try:
						self.getSetting()
						self.setUpdatedDatabase()
					except:
						pass
					self.database_busy = False


				self.saveTweetSaves()
				self.saveErrorSaves()

					
				time.sleep(5)

			except:
				print(datetime.now(), "Mysql error!")
				self.setMysql()
				time.sleep(5)

	def isWorkingTime(self):
		try:
			time_start = app.convert2Time(app.mySetting['detail']['time_start'])
			time_end = app.convert2Time(app.mySetting['detail']['time_end'])
			if time_start:
				if time_end:
					time_current = datetime.now()
					if time_start<=time_current and time_current<=time_end:
						return True
					else: 
						return False
		except:
			pass
		return True


	def convert2Time(self, str):
		try:
			arr = str.split(":")
			if len(arr)==2:
				res = datetime.now().replace(hour=int(arr[0]), minute=int(arr[1]))
				return res
			else:
				return False
		except:
			return False

	def setUpdatedDatabase(self):
		sql = "UPDATE settings SET value='0' Where name='updated_database'"
		self.mycursor.execute(sql)
		self.mydb.commit()
		

	def getUpdatedDatabase(self) :
		res = 0
		try:
			sql = "SELECT value FROM settings Where name='updated_database'"
			self.mycursor.execute(sql)
			myresult = self.mycursor.fetchall()
			for x in myresult:
				res = int(x[0])
		except:
			print(datetime.now(), "getUpdatedDatabase error!")
			res = -1
		return res

	def getSetting(self) :
		self.getMainSetting()
		self.getAmazonSetting()
		self.getRakutenSetting()
		self.getProxyServer()


	def getMainSetting(self):
		self.mySetting['twitter'] = [{},{},{},{},{}]

		# start_time = time.perf_counter()
		twitter_title_names = ['consumer_api_key', 'consumer_api_secret', 'access_token', 'access_token_secret']
		detail_title_names = ["interval_amazon_seconds", "interval_amazon_asin_seconds", "interval_rakuten_seconds", "twit_max_inaday", "interval_same_twit_seconds", "interval_min_twit_seconds", "moniter_amazon_on", "moniter_rakuten_on", "proxy_access_count", "proxy_max_in_use"]

		detail_title_strs = ["time_start", "time_end", "amz_associate_id", "amz_access_key", "amz_secret_key", "rk_application_id", "rk_affiliate_id", "today_str"]

		sql = "SELECT name, value FROM settings"
		self.mycursor.execute(sql)
		myresult = self.mycursor.fetchall()
		for x in myresult:
			name = x[0]
			value = x[1]
			for item in twitter_title_names:
				item_name = item
				for i in range(5):
					if (i!=0):
						item_name = item + str(i-1)
						
					if name==item_name:
						self.mySetting['twitter'][i][item] = value
						break

			for title in detail_title_names:
				if name==title:
					self.mySetting['detail'][title] = int(value)

			for title in detail_title_strs:
				if name==title:
					self.mySetting['detail'][title] = value


		self.mySetting['detail']['asin_api'] = 1

		# print(self.mySetting['detail'])	
		# print("Time taken of click TopTab Element: ", time.perf_counter() - start_time, "seconds")
	def saveMainSetting(self, name, value):
		try:
			if value:
				sql = "UPDATE settings SET value=%s, updated_at=%s Where name=%s"
				values = (value, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), name)
				self.mycursor.execute(sql, values)
				self.mydb.commit()
		except:
			print(datetime.now(), ": saveMainSetting Error!")


	def getAmazonSetting(self):
		self.mySetting['amazon'] = []
		# start_time = time.perf_counter()
		sql = "SELECT id, twitter_account_id, type, price_low, price_high, url, comment_pre, comment_medium, memo, count_product, update_product, twit_on, data FROM amazons ORDER BY id ASC"
		self.mycursor.execute(sql)
		myresult = self.mycursor.fetchall()
		for x in myresult:
			item = {"id": x[0],"twitter_account_id": x[1], "type": x[2], "price_low": x[3], "price_high": x[4], "url": x[5], "comment_pre": x[6], "comment_medium": x[7], "memo": x[8], "count_product": x[9], "update_product": x[10], "twit_on": x[11], 'data': x[12]}
			
			if not item['comment_pre']:
				item['comment_pre'] = ""

			if not item['comment_medium']:
				item['comment_medium'] = ""

			if (item['type']==1) :
				asin = item['url']
				item['url_real'] = "https://www.amazon.co.jp/dp/" + asin
				item['url_variables'] = "https://www.amazon.co.jp/gp/product/ajax/ref=dp_aod_NEW_mbc?asin=%s&m=&qid=&smid=&sourcecustomerorglistid=&sourcecustomerorglistitemid=&sr=&pc=dp&experienceId=aodAjaxMain"%( asin)

			# if item['data']:
			# 	item['data'] = json.loads(item['data'])
			item['data'] = {}
			item['session'] = {}
			item['proxies'] = 0
			item['status'] = 0

			item['need_save'] = 0
			
			self.mySetting['amazon'].append(item)
		# print("Time taken of click TopTab Element: ", time.perf_counter() - start_time, "seconds")

	def getRakutenSetting(self):
		self.mySetting['rakuten'] = []
		
		# start_time = time.perf_counter()
		
		sql = "SELECT id, twitter_account_id, url_reset, url_reset_no, comment_pre, comment_medium, memo, count_product, update_product, twit_on, data FROM rakutens ORDER BY id ASC"
		self.mycursor.execute(sql)
		myresult = self.mycursor.fetchall()
		for x in myresult:
			item = {'id': x[0],'twitter_account_id': x[1], 'url_reset': x[2], 'url_reset_no': x[3], 'comment_pre': x[4], 'comment_medium': x[5], 'memo': x[6], 'count_product': x[7], 'update_product': x[8], 'twit_on': x[9], 'data': x[10]}
			
			if not item['comment_pre']:
				item['comment_pre'] = ""
			
			if not item['comment_medium']:
				item['comment_medium'] = ""
			
			# if item['data']:
			# 	item['data'] = json.loads(item['data'])
			
			item['data'] = {}
			item['status'] = 0
			item['need_save'] = 0

			self.mySetting['rakuten'].append(item)
		
		# print("Time taken of click TopTab Element: ", time.perf_counter() - start_time, "seconds")

	def getProxyServer(self):
		self.mySetting['proxy'] = []
		sql = "SELECT id, port, protocol, ip, status, count FROM proxy_servers ORDER BY id ASC"
		self.mycursor.execute(sql)
		myresult = self.mycursor.fetchall()
		for x in myresult:
			count_val = 0
			if x[5]:
				count_val = x[5]
			item = {'id':x[0], 'port':x[1], 'protocol':x[2], 'ip':x[3], 'status': x[4], 'count': count_val, 'need_save':0}
			item['in_use'] = 0
			self.mySetting['proxy'].append(item)

		# item = {'id':0, 'port': '', 'protocol': '', 'ip': ''}
		# self.mySetting['proxy'].append(item)
		# print(self.mySetting)
			

	def InitHeadersAmazon(self):
		headers = []

		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
		}
		headers.append(item)


		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
		}
		headers.append(item)


		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
		}
		headers.append(item)


		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
		}
		headers.append(item)


		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			# 'host': 'www.amazon.co.jp',
			'accept-language': 'en-US,en;q=0.5',
		}
		headers.append(item)

		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 OPR/90.0.4480.80',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			# 'Origin': 'https://www.amazon.co.jp/',
			'accept-language': 'en-US,en;q=0.5',
		}
		headers.append(item)

		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			# 'Origin': 'https://www.amazon.co.jp/',
			'accept-language': 'en-US,en;q=0.5',
		}
		headers.append(item)

		item = {
			'dnt': '1',
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
			'sec-fetch-site': 'same-origin',
			'sec-fetch-mode': 'navigate',
			'sec-fetch-user': '?1',
			'sec-fetch-dest': 'document',
			'referer': 'https://www.amazon.co.jp/',
			# 'Origin': 'https://www.amazon.co.jp/',
			'accept-language': 'en-US,en;q=0.5',
		}
		headers.append(item)

		return headers

	def GetHeadersRakutenAPI(self):
		headers = []
		item={
			'sec-ch-ua' : '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
			'sec-ch-ua-mobile' : '?0',
			'sec-ch-ua-platform' : '"Windows"',
			'sec-fetch-dest' : 'document',
			'sec-fetch-mode' : 'navigate',
			'sec-fetch-site' : 'none',
			'sec-fetch-user' : '?1',
			'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
			'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'Accept-Encoding':'gzip, deflate, br',
			'Accept-Language':'en-US,en;q=0.8',
			'cache-control':'max-age=0',
			'Upgrade-Insecure-Requests':'1',
			'Host': 'app.rakuten.co.jp'
		}
		headers.append(item)
		return item

	def InitHeadersRakuten(self) :
		headers = []

		item={
			'sec-ch-ua' : '"Chromium";v="74", "Google Chrome";v="74", "Not;A=Brand";v="99"',
			'sec-ch-ua-mobile' : '?0',
			'sec-ch-ua-platform' : '"Windows"',
			'sec-fetch-dest' : 'document',
			'sec-fetch-mode' : 'navigate',
			'sec-fetch-site' : 'none',
			'sec-fetch-user' : '?1',
			'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
			'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'Accept-Encoding':'gzip, deflate, br',
			'Accept-Language':'en-US,en;q=0.8',
			'cache-control':'max-age=0',
			'Upgrade-Insecure-Requests':'1'
		}
		headers.append(item)

		item={
			'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
			'Accept':'text/html, application/xhtml+xml, image/jxr, */*',
			'Accept-Encoding':'gzip, deflate',
			'Accept-Language':'en-US, en; q=0.8, ko; q=0.7, zh-Hans-CN; q=0.5, zh-Hans; q=0.3, ja; q=0.2',
			'Host':'search.rakuten.co.jp',
		}
		headers.append(item)

		item={
			'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'accept-encoding':'gzip, deflate, br',
			'accept-language':'en-US,en;q=0.9',
			'cache-control':'max-age=0',
			'sec-ch-ua':'" Not A;Brand";v="99", "Chromium";v="104", "Opera";v="90"',
			'sec-ch-ua-mobile':'?0',
			'sec-ch-ua-platform':'"Windows"',
			'sec-fetch-dest':'document',
			'sec-fetch-mode':'navigate',
			'sec-fetch-site':'none',
			'sec-fetch-user':'?1',
			'upgrade-insecure-requests':'1',
			'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 OPR/90.0.4480.80',
		}	
		headers.append(item)

		item={
			'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'accept-encoding':'gzip, deflate, br',
			'accept-language':'en-US,en;q=0.9',
			'cache-control':'max-age=0',
			'sec-ch-ua':'"Microsoft Edge";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
			'sec-ch-ua-mobile':'?0',
			'sec-ch-ua-platform':'"Windows"',
			'sec-fetch-dest':'document',
			'sec-fetch-mode':'navigate',
			'sec-fetch-site':'none',
			'sec-fetch-user':'?1',
			'upgrade-insecure-requests':'1',
			'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.27',
		}
		headers.append(item)

		item={
			'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
			'accept-encoding':'gzip, deflate, br',
			'accept-language':'en-US,en;q=0.9',
			'host' : 'search.rakuten.co.jp',
			'sec-fetch-dest':'document',
			'sec-fetch-mode':'navigate',
			'sec-fetch-site':'none',
			'sec-fetch-user':'?1',
			'upgrade-insecure-requests':'1',
			'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) Gecko/20100101 Firefox/104.0',
		}	
		headers.append(item)

		return headers

	def create_session(self, is_rakuten = True, referer=''):
		if is_rakuten:
			headers = random.choice(self.const_headers_rakuten)	
		else:			
			headers = random.choice(self.const_headers_amazon)	
			if referer:
				headers['referer'] = referer

		session = requests.Session()
		session.headers.update(headers)	
		return session

	def init_session_post(self):
		post_headers={
					'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0',
					'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
					'Accept-Language':'en-US,en;q=0.5',
					'Accept-Encoding':'gzip, deflate',
					'Connection':'keep-alive',
					'Upgrade-Insecure-Requests':'1'
					}
		self.session.headers.update(post_headers)

	def calProxyInUse(self):
		for item in self.mySetting['proxy']:
			item['in_use'] = 0
			for amazon in self.mySetting['amazon']:
				if amazon['proxies']:
					if item['ip'] == amazon['proxies']['object']['ip']:
						item['in_use'] = item['in_use'] + 1

	def getProxyVal(self):
		proxy = {}
		min_val = 10000000
		for item in self.mySetting['proxy']:
			if item['status'] != 0:
				if item['count']<min_val and item['in_use']<self.mySetting['detail']['proxy_max_in_use']:
					min_val = item['count']
					proxy = item

		if not proxy:
			min_val = 10000000
			for item in self.mySetting['proxy']:
				if item['count']<min_val and item['in_use']<self.mySetting['detail']['proxy_max_in_use']:
					min_val = item['count']
					proxy = item

		if not proxy:
			proxy = random.choice(self.mySetting['proxy'])

		proxy['in_use'] = proxy['in_use'] + 1
		proxies = {"object": proxy, "value":{
					'http': 'http://%s:%s'%(proxy['ip'], proxy['port']),
					'https': 'http://%s:%s'%(proxy['ip'], proxy['port']),
				}};
		return proxies;

	def getProxyRandom(self):
		proxy = random.choice(self.mySetting['proxy'])
		if proxy['id'] == 0:
			return "server"
		proxies = {"object": proxy, "value":{
					'http': 'http://%s:%s'%(proxy['ip'], proxy['port']),
					'https': 'http://%s:%s'%(proxy['ip'], proxy['port']),
				}};
		return proxies;


	def rakuten_get(self, id=1) :
		thread_id = id
		while 1:
			if self.database_busy:
				break
			rakuten = self.mySetting['rakuten'][thread_id];
			if rakuten:
				status = 0
				if self.mySetting['detail']['moniter_rakuten_on']==1:
					if self.isWorkingTime():
						if rakuten['twit_on'] == 1:
							url = rakuten['url_reset_no']
							session = self.create_session(True)
							
							proxies = self.getProxyRandom()
							if proxies!="server":
								session.proxies.setdefault('http', 'http://127.0.0.1:9009')
								session.proxies.update(proxies['value'])
							
							try:
								r = session.get(url, timeout=25)
								if r.status_code == 200:
									data = extract_rakuten_search.extract(r.text)
									self.rakuten_compare(rakuten, data)
									status = 1
							except:
								new_item = {"type": "Proxy Failed", "description": "Rakuten:" + str(rakuten['id']) + " Proxy IP:" + proxies['object']['ip'],  "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
								self.queueErrorSave(new_item)
								print(datetime.now(), "proxy :", proxies['object']['ip'])
								print("")

				
				rakuten['status'] = status

			sleep_time = 6
			if self.mySetting['detail']:
				if self.mySetting['detail']['interval_rakuten_seconds']:
					sleep_time = int(self.mySetting['detail']['interval_rakuten_seconds'])
			time.sleep(sleep_time)
			
		if thread_id in self.rakuten_thread_ids:
			self.rakuten_thread_ids.remove(thread_id)

	def rakuten_compare(self, rakuten, data):
		if not data['products']:
			data['products'] = []

		new_data = {}
		new_data['url'] = rakuten['url_reset_no']
		new_data['products'] = []

		old_data = rakuten['data']
		if(old_data):
			if data['products']:
				for item in data['products']:
					is_new = True
					for old_item in old_data['products']:
						if item['title']==old_item:
							is_new = False
							break
					if is_new:
						url = item['url']
						if not url:
							url = item['url_second']
						product_id = item['product_id']
						image_url = item['image']
						affiliate_url = self.getRakutenAffiliateUrl(url, product_id, image_url)

						comment_pre = "ウイスキー速報！！"
						if rakuten['comment_pre']:
							comment_pre = rakuten['comment_pre']

						comment_medium = "が出現中！！"
						if rakuten['comment_medium']:
							comment_medium = rakuten['comment_medium']

						# content = comment_pre + "\n" + item['title'] + "\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + str(self.getNumberPrice(item['price'])) + "円" + "\n" + affiliate_url
						
						content_format = comment_pre + "\n{}\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + str(self.getNumberPrice(item['price'])) + "円" + "\n" + affiliate_url
						content_target = item['title']
						content = self.change_tweet_len(content_format, content_target)
						if (content):
							res = self.send_tweet(rakuten, item['title'], content, rakuten['id'], 'rakuten')
							if res:
								new_data['products'].append(item['title'])
						else:
							print("rakuten_compare tweet error! ")

					else:
						new_data['products'].append(item['title'])
			
		else:
			if data['products']:
				for item in data['products']:
					new_data['products'].append(item['title'])
		# if self.isChangeProducts(rakuten['data'], new_data):
		# 	rakuten['need_save'] = 1
		rakuten['data'] = new_data
		return True


	def amazon_get_item(self, id=1) :
		access_count = 0
		thread_id = id
		failed_count = 0
		while(1) :
			if self.database_busy:
				break

			amazon = self.mySetting['amazon'][thread_id];
			if amazon:
				status = 0
				if self.mySetting['detail']['moniter_amazon_on']==1:
					if self.isWorkingTime():
						if amazon['twit_on'] == 1:
							search_type = amazon['type']
							if search_type==1:
								url = amazon['url_variables']
								referer = amazon['url_real']
							else:
								url = amazon['url']
								referer = url

							amazon['session'] = self.create_session(False, referer)
							
							if not amazon['proxies'] or access_count>self.mySetting['detail']['proxy_access_count']:
								amazon['proxies'] = self.getProxyVal()
								access_count = 0
								failed_count = 0

							if failed_count>=4:
								amazon['proxies']['object']['status'] = 0
								amazon['proxies'] = self.getProxyVal()
								access_count = 0
								failed_count = 0
							
							# if amazon['proxies']!="server":
							amazon['session'].proxies.setdefault('http', 'http://127.0.0.1:9009')
							amazon['session'].proxies.update(amazon['proxies']['value'])
							
							
							try:
								r = amazon['session'].get(url, timeout=25)
								if r.status_code == 200:
									if search_type==0:
										data = extract_amazon_search.extract(r.text)
									else:
										data = extract_amazon_item_variables.extract(r.text)

									self.amazon_compare(amazon, data)
									amazon['proxies']['object']['status'] = 1
									status = 1
								else:
									failed_count = failed_count + 1
									new_item = {"type": "Proxy Failed", "description": "Amazon:" + str(amazon['id']) + " Proxy IP:" + amazon['proxies']['object']['ip'],  "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
									self.queueErrorSave(new_item)

							except:
								failed_count = failed_count + 1
								print(datetime.now(),": amazon scraping error!")

							access_count = access_count + 1
							amazon['proxies']['object']['count'] = amazon['proxies']['object']['count'] + 1
							amazon['proxies']['object']['need_save'] = 1
					
							# try:
							# 	fos_url = "https://www.amazon.co.jp/autocomplete/fos"
							# 	amazon['session'].headers.update({'referer': referer})
							# 	p = amazon['session'].get(fos_url, timeout=25)

							# 	suggestion_url = "https://www.amazon.co.jp/api/2017/suggestions"
							# 	amazon['session'].headers.update({'referer': referer})
							# 	h = amazon['session'].head(suggestion_url, timeout=25)
							# except:
							# 	pass

				
				amazon['status'] = status
				

			sleep_time = 60
			if self.mySetting['detail']:
				if self.mySetting['detail']['interval_amazon_seconds']:
					sleep_time = int(self.mySetting['detail']['interval_amazon_seconds'])
			if sleep_time<15:
				sleep_time = 15
			time.sleep(sleep_time)

		if thread_id in self.amazon_thread_ids:
			self.amazon_thread_ids.remove(thread_id)

	def amazon_get_item_asin_api(self) :
		self.amazon_thread_asin_api = True
		asins_all = []
		number_of_asin = 0
		while(1) :
			if self.database_busy:
				break

			for item in asins_all:
				item['exist'] == False
			
			for amazon in self.mySetting['amazon']:
				if amazon['type']==1 and amazon['twit_on'] == 1:
					# temp_asins_all.append(amazon['url'])
					has_exist = False
					for item in asins_all:
						if item['asin'] == amazon['url']:
							item['exist'] == True
							has_exist = True
							break
					if has_exist==False:						
						asins_all.append({"asin":amazon['url'], "exist": True, "access_count": 0})

			asins = []
			len_asins = len(asins_all)
			count_val = 0
			temp = 0
			for i in range(len_asins):
				temp = i + number_of_asin
				if temp>=len_asins:
					temp = temp - len_asins
				if asins_all[temp]['exist']:
					count_val = count_val + 1
					asins.append(asins_all[temp]['asin'])
					if count_val>=10:
						break
			number_of_asin = temp + 1

			data = []
			if asins:
				if self.mySetting['detail']['amz_associate_id']:
					if self.mySetting['detail']['moniter_amazon_on']==1:
						if self.isWorkingTime():
							try:
								self.amazonApiObj = AmazonApi(self.mySetting['detail']['amz_access_key'], self.mySetting['detail']['amz_secret_key'], self.mySetting['detail']['amz_associate_id'], 'JP')
								data = self.amazonApiObj.get_items(asins)
							except:
								new_item = {"type": "AmazonApi Failed", "description": "Access Key: " + self.mySetting['detail']['amz_access_key'],  "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
								self.queueErrorSave(new_item)
								print(datetime.now(), ": amazon api error !")
								data = []
							self.amazon_access_count_asin_api = self.amazon_access_count_asin_api + 1

			if data:
				for amazon in self.mySetting['amazon']:
					if amazon['type']==1:
						status = amazon['status']
						if amazon['twit_on'] == 1:
							amazon_asin = amazon['url']
							for item in data:
								if item.asin==amazon_asin:
									data_item = {'asin': item.asin, 'lowest_price': 0, 'title': ""}
									try:
										data_item['title'] = item.item_info.title.display_value
										data_item['lowest_price'] = item.offers.summaries[0].lowest_price.amount
									except:
										# print(datetime.now(), ": amazon_get_item_asin_api fetching values error!")
										pass
									self.amazon_compare_asin_api(amazon, data_item)
									amazon['data'] = data_item
									status = 1
									break
						
						amazon['status'] = status
						
			else:
				for amazon in self.mySetting['amazon']:
					if amazon['type']==1:
						if amazon['twit_on'] == 1:
							amazon_asin = amazon['url']
							for item in asins:
								if amazon_asin==item:
									amazon['status'] = 0
									break

			
			sleep_time = 60
			if self.mySetting['detail']:
				if self.mySetting['detail']['interval_amazon_asin_seconds']:
					sleep_time = int(self.mySetting['detail']['interval_amazon_asin_seconds'])

			if sleep_time<15:
				sleep_time = 15
			time.sleep(sleep_time)
	
		self.amazon_thread_asin_api = False

	def proxy_set_database(self, id_val, status, count, in_use):
		# try:
		if not status:
			status = 0
		if not in_use:
			in_use = 0
		if not count:
			count = 0
		# print(status, ":", count, ":",  id_val)
		sql = "UPDATE proxy_servers SET status=%s, count=%s, in_use=%s, updated_at=%s Where id=%s"
		values = (status, count, in_use, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id_val)
		self.mycursor.execute(sql, values)
		self.mydb.commit()

	def amazon_set_database(self, id, data, status):
		try:
			sql = "UPDATE amazons SET data=%s, status=%s, updated_at=%s Where id=%s"
			values = (data, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id)
			self.mycursor.execute(sql, values)
			self.mydb.commit()
		except:
			print(datetime.now(), ": amazon_set_database error!")

	def rakuten_set_database(self, id, data, status):
		try:
			sql = "UPDATE rakutens SET data=%s, status=%s, updated_at=%s Where id=%s" 
			values = (data, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id)
			self.mycursor.execute(sql, values)
			self.mydb.commit()
		except:
			print(datetime.now(), ": rakuten_set_database error!")
			pass

	def isChangeProducts(self, old_data, new_data):
		if not old_data:
			return True

		if len(old_data['products'])!=len(new_data['products']):
			return True
		res = False
		for i in range(len(old_data['products'])):
			if old_data['products'][i]!=new_data['products'][i]:
				res = True
				break
		return res

	def amazon_compare(self, amazon, data) :
		if not data['products']:
			data['products'] = []

		old_data = amazon['data']
		if amazon['type']==0:
			new_data = {}
			new_data['url'] = amazon['url']
			new_data['products'] = []
			if(old_data):
				for item in data['products']:
					is_new = True
					for old_item in old_data['products']:
						if item['asin']==old_item:
							is_new = False
							break
					if is_new:
						url = "https://www.amazon.co.jp/dp/" + item['asin']

						comment_pre = "ウイスキー速報！！"
						if amazon['comment_pre']:
							comment_pre = amazon['comment_pre']

						comment_medium = "が出現中！！"
						if amazon['comment_medium']:
							comment_medium = amazon['comment_medium']

						price_str = ""
						temp = self.getNumberPrice(item['price'])
						if temp:
							price_str = str(temp) + "円"

						# content = comment_pre + "\n" + item['title'] + "\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + price_str + "\n" + self.amazonAffiliateUrl(url)

						content_format = comment_pre + "\n{}\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + price_str + "\n" + self.amazonAffiliateUrl(url)
						content_target = item['title']
						content = self.change_tweet_len(content_format, content_target)
						if (content):
							res = self.send_tweet(amazon, item['asin'], content, amazon['id'], 'amazon')
							if res:
								new_data['products'].append(item['asin'])
						else:
							print("amazon_compare tweet error! ")
						
							
					else:
						new_data['products'].append(item['asin'])
			else:
				if data['products']:
					for item in data['products']:
						new_data['products'].append(item['asin'])

			amazon['data'] = new_data
		else:
			new_data = {}
			new_data['url'] = amazon['url']
			new_data['lowest_price'] = 0
			
			price_list = []
			try:
				price_list.append(self.getNumberPrice(data['price']))
			except:
				pass

			for item in data['products']:
				try:
					price_list.append(self.getNumberPrice(item['price']))
				except:
					pass

			min_price = 0
			for price in price_list:
				if min_price==0:
					min_price = price
				else:
					if min_price>price:
						min_price = price

			new_data['lowest_price'] = min_price


			if amazon['price_low']:
				if amazon['price_high']:
					if amazon['price_high']>=min_price and min_price>=amazon['price_low'] and min_price>0:
						comment_pre = "ウイスキー速報！！"
						if amazon['comment_pre']:
							comment_pre = amazon['comment_pre']

						comment_medium = "が出現中！！"
						if amazon['comment_medium']:
							comment_medium = amazon['comment_medium']

						# content = comment_pre + "\n" + data['name'] + "\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + str(min_price) + "円" + "\n" + self.amazonAffiliateUrl(amazon['url_real'])

						content_format = comment_pre + "\n{}\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + str(min_price) + "円" + "\n" + self.amazonAffiliateUrl(amazon['url_real'])
						content_target = data['name']
						content = self.change_tweet_len(content_format, content_target)

						must_do = False
						if amazon['data']:
							if amazon['data']['lowest_price'] > min_price:
								must_do = True
							if amazon['data']['lowest_price'] <=0:
								must_do = True

						if (content):
							res = self.send_tweet(amazon, amazon['url'], content, amazon['id'], 'amazon', must_do)
						else:
							print("amazon_compare tweet 1 error! ")

						
			amazon['data'] = new_data
		return True	
		

	def amazon_compare_asin_api(self, amazon, data) :
		try:
			price = data['lowest_price']
			if amazon['price_low']:
				if amazon['price_high']:
					if amazon['price_high']>=price and price>=amazon['price_low'] and price>0:
						comment_pre = "ウイスキー速報！！"
						if amazon['comment_pre']:
							comment_pre = amazon['comment_pre']

						comment_medium = "が出現中！！"
						if amazon['comment_medium']:
							comment_medium = amazon['comment_medium']

						content_format = comment_pre + "\n{}\n" + comment_medium + "\n" +datetime.now().strftime('%H:%M')+ " 在庫観測 " + str(price) + "円" + "\n" + self.amazonAffiliateUrl(amazon['url_real'])
						content_target = data['title']
						content = self.change_tweet_len(content_format, content_target)

						must_do = False
						if amazon['data']:
							if amazon['data']['lowest_price'] > price:
								must_do = True
							if amazon['data']['lowest_price'] <= 0:
								must_do = True

						if (content):
							res = self.send_tweet(amazon, amazon['url'], content, amazon['id'], 'amazon', must_do)
						else:
							print("amazon_compare_asin_api tweet 1 error! ")
						
		except:
			print(datetime.now(), ": amazon_compare_asin_api error!")
			pass
		return True	

	def amazonAffiliateUrl(self, url):
		return url + "?tag="+ self.mySetting['detail']['amz_associate_id'] +"&linkCode=ogi&th=1&psc=1"

	def getNumberPrice(self, str) :
		if str:
			str = str.replace(",", "")
		if str:
			str = str.replace(" ", "")
		if str:
			str = str.replace("￥", "")
		if str:
			str = str.replace("円", "")
		if str:
			if str!="":
				return int(str)
		return 0

	def initErrorSaves(self):
		self.errorSave = []
		self.errorSaveCount = 200
		for i in range(self.errorSaveCount):
			item = {"type": 0, "description":"",  "created_at": "", "need_save": 0}
			self.errorSave.append(item)

	def queueErrorSave(self, new_item):
		for item in self.errorSave:
			if item['need_save']==0:
				item['need_save'] = 1
				item['type'] = new_item['type']
				item['description'] = new_item['description']
				item['created_at'] = new_item['created_at']
				break

	def saveErrorSaves(self):
		for item in self.errorSave:
			if item['need_save']==1:
				try:
					sql = "INSERT INTO logs (type, description, created_at) VALUE (%s, %s, %s)"
					values = (item['type'], item['description'], item['created_at'])
					self.mycursor.execute(sql, values)
					self.mydb.commit()
					item['need_save'] = 0
					time.sleep(0.05)
				except:
					print(datetime.now(), ": saveErrorSaves Error!")

	def initTweetSaves(self):
		self.tweetSave = []
		self.tweetSaveCount = 100
		for i in range(self.tweetSaveCount):
			item = {"foreignId":0, "mall":"amazon", "identifier": "", "content": "", "twitter_account_id":0,  "created_at": "", "need_save": 0}
			self.tweetSave.append(item)
	
	def queueTweetSaves(self, new_item):
		for item in self.tweetSave:
			if item['need_save']==0:
				item['need_save'] = 1
				item['foreignId'] = new_item['foreignId']
				item['mall'] = new_item['mall']
				item['identifier'] = new_item['identifier']
				item['content'] = new_item['content']
				item['twitter_account_id'] = new_item['twitter_account_id']
				item['created_at'] = new_item['created_at']
				break

	def saveTweetSaves(self):
		for item in self.tweetSave:
			if item['need_save']==1:
				try:
					sql = "INSERT INTO tweets (twitter_account_id, foreignId, mall, url, content, created_at) VALUE (%s, %s, %s, %s, %s, %s)"
					values = (item['twitter_account_id'], item['foreignId'], item['mall'], item['identifier'], item['content'], item['created_at'])
					self.mycursor.execute(sql, values)
					self.mydb.commit()
					item['need_save'] = 0
					time.sleep(0.05)
				except:
					print(datetime.now(), ": saveTweetSaves error!")
					self.setMysql()
				

	def initTweetRecord(self):
		self.tweetRecord = []
		self.tweetRecordCount = 0
		for i in range(20000):
			item = {"identifier": "", "twitter_account_id":0, "mall":"amazon", "time": datetime.now()}
			self.tweetRecord.append(item)
		self.loadTweetRecord()

	def loadTweetRecord(self):
		try:
			sql = "SELECT id, mall, url, twitter_account_id, created_at FROM tweets WHERE created_at>='%s 00:00:00' ORDER BY id ASC"%(datetime.now().strftime('%Y-%m-%d'))
			self.mycursor.execute(sql)
			myresult = self.mycursor.fetchall()
			for x in myresult:
				item = {'id': x[0],'mall': x[1], 'identifier': x[2], 'twitter_account_id': x[3], 'created_at': x[4]}
				self.addTweetRecord(item['identifier'], item['twitter_account_id'], item['mall'], item['created_at'])
				diff_time = item['created_at'] - datetime.now()
				diff_time = diff_time.total_seconds()
		except:
			print(datetime.now(), ": loadTweetRecord error!")
			pass

	def clearTweetRecord(self):
		self.tweetCount[0] = 0
		self.tweetCount[1] = 0
		self.tweetCount[2] = 0
		self.tweetCount[3] = 0
		self.tweetCount[4] = 0

	def checkTweetRecord(self, identifier, twitter_account_id, mall, oneInADay=False):
		has_record = False
		interval_same_twit_seconds = self.mySetting['detail']['interval_same_twit_seconds']
		for i in range(self.tweetRecordCount):
			item = self.tweetRecord[i]
			if item['identifier']==identifier and item['mall']==mall and item['twitter_account_id']==twitter_account_id:
				if oneInADay==True:
					org_time = datetime.now().replace(hour=0, minute=0)
					if item['time']>=org_time:
						has_record = True
						break
				else:
					diff_time = datetime.now() - item['time']
					diff_time = diff_time.total_seconds()
					if interval_same_twit_seconds>diff_time:
						has_record = True
						break
		
		return has_record

	def addTweetRecord(self, identifier, twitter_account_id, mall, time=''):
		if self.tweetRecordCount<20000:
			set_record = False
			for i in range(self.tweetRecordCount):
				try:
					diff_time = datetime.now() - self.tweetRecord[i]['time']
					diff_time = diff_time.total_seconds()
					if diff_time>200000:
						set_record = True
						self.tweetRecord[i]['identifier'] = identifier
						self.tweetRecord[i]['twitter_account_id'] = twitter_account_id
						self.tweetRecord[i]['mall'] = mall
						if time:
							self.tweetRecord[i]['time'] = time
						else:
							self.tweetRecord[i]['time'] = datetime.now()
						break
				except:
					print(datetime.now(), ": addTweetRecord error!")
					# for j in range(self.tweetRecordCount):
					# 	print(self.tweetRecord[j])

			if set_record==False:
				i = self.tweetRecordCount
				self.tweetRecord[i]['identifier'] = identifier
				self.tweetRecord[i]['twitter_account_id'] = twitter_account_id
				self.tweetRecord[i]['mall'] = mall
				if time:
					self.tweetRecord[i]['time'] = time
				else:
					self.tweetRecord[i]['time'] = datetime.now()
				self.tweetRecordCount = self.tweetRecordCount + 1

	def test_tweet(self, content):
		twitter_account_id = 0
		auth = tweepy.OAuthHandler(self.mySetting['twitter'][twitter_account_id]['consumer_api_key'], self.mySetting['twitter'][twitter_account_id]['consumer_api_secret'])
		auth.set_access_token(self.mySetting['twitter'][twitter_account_id]['access_token'], self.mySetting['twitter'][twitter_account_id]['access_token_secret'])
		api = tweepy.API(auth)
		api.update_status(content)

	def change_tweet_len(self, tweet_format, target):
		target = target[:280] 
		for i in range(len(target)):
			if i == 0:
				tweet_txt = tweet_format.format(target)
			else:
				tweet_txt = tweet_format.format(target[:-i] + "…")
			if parse_tweet(tweet_txt).valid:
				return tweet_txt
		print(tweet_format)
		print(target)
		print(parse_tweet(tweet_format(target)))
		return 0



	def send_tweet(self, obj,  identifier, content, id, mall="amazon", must_do=False):
		twitter_account_id = obj['twitter_account_id']
		can_tweet = True
		
		if must_do==False:
			if self.mySetting['detail']['twit_max_inaday'] :
				if self.tweetCount[twitter_account_id]>= int(self.mySetting['detail']['twit_max_inaday']):
					can_tweet = False

			oneInADay = False
			if mall=="amazon":
				if obj['type']==1:
					oneInADay = True
			
			if self.checkTweetRecord(identifier, twitter_account_id, mall, oneInADay):
				can_tweet = False


			if not can_tweet:
				return True

		# Tweet min interval time 
		# if self.tweetLastTime[twitter_account_id]:
		# 	diff_time = datetime.now()-self.tweetLastTime[twitter_account_id]
		# 	diff_time = diff_time.total_seconds()
		# 	if self.mySetting['detail']['interval_min_twit_seconds'] :
		# 		if diff_time< int(self.mySetting['detail']['interval_min_twit_seconds']):
		# 			diff_time = int(int(self.mySetting['detail']['interval_min_twit_seconds'])-diff_time)
		# 			time.sleep(diff_time)


		
		is_success = False
		try:
			auth = tweepy.OAuthHandler(self.mySetting['twitter'][twitter_account_id]['consumer_api_key'], self.mySetting['twitter'][twitter_account_id]['consumer_api_secret'])
			auth.set_access_token(self.mySetting['twitter'][twitter_account_id]['access_token'], self.mySetting['twitter'][twitter_account_id]['access_token_secret'])
			api = tweepy.API(auth)
			api.update_status(content)	
			is_success = True
		except:
			print(content)
			time.sleep(3)
			print(datetime.now(), "Twitter api ", twitter_account_id, "error!")

		if is_success==False:
			try:
				auth = tweepy.OAuthHandler(self.mySetting['twitter'][twitter_account_id]['consumer_api_key'], self.mySetting['twitter'][twitter_account_id]['consumer_api_secret'])
				auth.set_access_token(self.mySetting['twitter'][twitter_account_id]['access_token'], self.mySetting['twitter'][twitter_account_id]['access_token_secret'])
				api = tweepy.API(auth)
				api.update_status(content)	
				is_success = True
			except:
				new_item = {"type": "Tweet Failed", "description": "Twitter API Account: " + str(twitter_account_id),  "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
				self.queueErrorSave(new_item)
				# print(datetime.now(), "Twitter api second try ", twitter_account_id, "error!")
				token_thread = threading.Thread(target=self.test_tweet, args=(content,))
				token_thread.start()
				return False
			

		new_item = {"foreignId":id, "mall":mall, "identifier": identifier, "content": content, "twitter_account_id":twitter_account_id,  "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "need_save": 1}
		self.queueTweetSaves(new_item)

		self.addTweetRecord(identifier, twitter_account_id, mall)

		self.tweetCount[twitter_account_id] = self.tweetCount[twitter_account_id] + 1
		self.tweetLastTime[twitter_account_id] = datetime.now()


		return True	







	def getShortUrl(self, url) :
		headers = {
			'upgrade-insecure-requests': '1',
			'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
			'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
			'referer': 'http://118.27.30.32/login',
		}
		try:
			session = requests.Session()
			session.headers.update(headers)
			r = session.get("http://118.27.30.32/short_url?url="+url)
			return json.loads(r.text)['url']
		except:
			print("Error in getting short url!")
			return False

if __name__ == "__main__":
	velocity.cache('search.rakuten.co.jp')
	app = Auto_Class()
	app.run()
	# app.test()
	
	
