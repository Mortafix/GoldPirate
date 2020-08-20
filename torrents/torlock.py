import requests
from bs4 import BeautifulSoup as bs
from re import search,sub
from time import sleep
from datetime import timedelta,datetime
from functools import reduce

class TorLock:
	def __init__(self):
		self.url = 'https://torlock.unblockit.win'
		self.search = '/all/torrents/##'
		self.delimiter = '+'
		self.sort = '/all/torrents/##.html?sort=@@&order=desc'
		self.sort_type = {'age':'added','size':'size','seed':'seeds','leech':'peers'}
		self.page = '/@@.html'
		self.user_agent = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}

	def _search_torrents(self,query,sort=None):
		url_attach = sub('@@',self.sort_type[sort],sub('##',sub(r'\s',self.delimiter,query),self.sort)) if sort and sort in self.sort_type else sub('##',sub(r'\s',self.delimiter,query),self.search)
		return reduce(lambda x,y:x+y,[bs(requests.get('{}{}{}'.format(self.url,url_attach,sub('@@',str(i),self.page)),headers=self.user_agent).text, 'html.parser').findAll('td')[27:] for i in range(2)],[])


	def build_list(self,query,sort=None):
		search_list = self._search_torrents(query,sort)
		singles = [search_list[i*6:i*6+6] for i in range(len(search_list)//6)]
		torrents = list()
		for torrent in singles:
			name = torrent[0].text
			link_page = [a.get('href') for a in torrent[0].findAll('a')][0]
			category = int(torrent[0].find('span').get('class')[0][2:])
			time,size,seed,leech = [t.text for t in torrent[1:5]]
			torrents.append(['TorLock',name,link_page,self._date_converter(time),self._get_category(category),sub(r'\d+$','',size),int(sub(',','',seed)),int(sub(',','',leech))])
		return torrents

	def _date_converter(self,site_date):
		if site_date == 'Today': return datetime.now().strftime('%d.%m.%Y')
		if site_date == 'Yesterday': return datetime.strftime(datetime.now() - timedelta(1), '%d.%m.%Y')
		day,month,year = site_date.split('/')
		return '{:02d}.{:02d}.{}'.format(int(month),int(day),int(year))

	def _get_category(self,cateogry_id):
		categories = {1:'Movies',2:'Music',3:'Television',4:'Games',5:'Software',6:'Anime',7:'Adult',8:'E-Books',9:'Images',12:'Audio Books',0:'Other'}
		return categories[cateogry_id] if cateogry_id in categories else 'Other' 

	def get_magnet_link(self,torrent_page):
		soup = soup = bs(requests.get('{}{}'.format(self.url,torrent_page),allow_redirects=True).text,'html.parser')
		try: return [a.get('href') for a in soup.findAll('a') if search('magnet',str(a.get('href')))][0]
		except IndexError: return None

if __name__ == '__main__':
	tr = TorLock()
	torrents = tr.build_list('Harry potter calice')
	print(torrents)