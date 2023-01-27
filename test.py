from selectorlib import Extractor
import requests, lxml
import time, random
import sys

extract_amazon_search = Extractor.from_yaml_file('amazon_search_results.yml')
extract_amazon_item_variables = Extractor.from_yaml_file('amazon_item_variables.yml')

extract_rakuten_search = Extractor.from_yaml_file('rakuten_search_results.yml')

class Auto_Class():
	def __init__(self):
		self.const_headers_rakuten = self.InitHeadersRakuten()
		self.const_headers_amazon = self.InitHeadersAmazon()

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

	def rakuten_get(self) :
		url = "https://search.rakuten.co.jp/search/mall/%E5%8E%9A%E5%B2%B8+%E5%A4%A7%E9%9B%AA+%E3%82%A6%E3%82%A4%E3%82%B9%E3%82%AD%E3%83%BC/?max=60000&min=10000"
		session = self.create_session(True)
		
		try:
			r = session.get(url, timeout=25)
			if r.status_code == 200:
				data = extract_rakuten_search.extract(r.text)
				print(len(data['products']))
				print(data['products'])
				for item in data['products']:
					print(self.getNumberPrice(item['price']))
					print(item['title'])
					print(item['price'])
				
		except:
			print('error!')


if __name__ == "__main__":
	app = Auto_Class()
	app.rakuten_get()
	# app.test()