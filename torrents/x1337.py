import requests
from bs4 import BeautifulSoup as bs
from re import search,sub
from time import sleep
from functools import reduce

class X1337:
	def __init__(self):
		self.url = 'https://1337x.unblockit.win'
		self.search = '/search/##'
		self.delimiter = '+'
		self.sort = '/sort-search/##/@@/desc'
		self.sort_type = {'age':'time','size':'size','seeders':'leechers','leech':'leechers'}
		self.page = '/@@/'
		self.user_agent = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}

	def _search_torrents(self,query,sort=None):
		url_attach = sub('@@',self.sort_type[sort],sub('##',sub(r'\s',self.delimiter,query),self.sort)) if sort and sort in self.sort_type else sub('##',sub(r'\s',self.delimiter,query),self.search)
		return reduce(lambda x,y:x+y,[bs(requests.get('{}{}{}'.format(self.url,url_attach,sub('@@',str(i+1),self.page)),headers=self.user_agent).text, 'html.parser').findAll('td') for i in range(2)],[])

	def build_list(self,query,sort=None):
		search_list = self._search_torrents(query,sort)
		singles = [search_list[i*6:i*6+6] for i in range(len(search_list)//6)]
		torrents = list()
		for torrent in singles:
			name = torrent[0].text
			category,link_page = [a.get('href') for a in torrent[0].findAll('a')]
			category = int(search(r'(\d+)/0',category).group(1))
			seed,leech,time,size = [t.text for t in torrent[1:5]]
			torrents.append(['1337x',name,link_page,self._date_converter(time),self._get_category(category),sub(r'\d+$','',size),int(sub(',','',seed)),int(sub(',','',leech))])
		return torrents

	def _date_converter(self,site_date):
		month,day,year = site_date.split()
		months = {'Jan.':1,'Feb.':2,'Mar.':3,'Apr.':4,'May.':5,'Jun.':6,'Jul.':7,'Aug.':8,'Sep.':9,'Oct.':10,'Nov.':11,'Dec.':12}
		return '{:02d}.{:02d}.20{}'.format(int(sub(r'\D+','',day)),months[month],year[1:]) if not search('(am|pm)',site_date) else '{}.{}.2020'.format(months[day],int(sub(r'\D+','',year)))

	def _get_category(self,cateogry_id):
		categories = {1: 'DVD', 2: 'Divx/Xvid', 3: 'SVCD/VCD', 4: 'Dubs/Dual Audio', 5: 'DVD', 6: 'Divx/Xvid', 7: 'SVCD/VCD', 9: 'Documentary', 10: 'PC Game', 11: 'PS2', 12: 'PSP', 13: 'Xbox', 14: 'Xbox360', 15: 'PS1', 16: 'Dreamcast', 18: 'PC Software', 19: 'Mac', 20: 'Linux', 22: 'MP3', 23: 'Lossless', 24: 'DVD', 25: 'Video', 26: 'Radio', 28: 'Anime', 33: 'Emulation', 34: 'Tutorials', 35: 'Sounds', 36: 'E-Books', 37: 'Images', 38: 'Mobile Phone', 39: 'Comics', 41: 'HD', 42: 'HD', 43: 'PS3', 44: 'Wii', 45: 'DS', 46: 'GameCube', 47: 'Nulled Script', 48: 'Video', 49: 'Picture', 50: 'Magazine', 51: 'Hentai', 52: 'Audiobook', 53: 'Album', 54: 'h.264/x264', 55: 'Mp4', 56: 'Android', 57: 'iOS', 58: 'Box Set', 59: 'Discography', 60: 'Single', 66: '3D', 67: 'Games', 68: 'Concerts', 69: 'AAC', 70: 'HEVC/x265', 71: 'HEVC/x265', 72: '3DS', 73: 'Bollywood', 74: 'Cartoon', 75: 'SD', 76: 'UHD', 77: 'PS4', 78: 'Dual Audio', 79: 'Dubbed', 80: 'Subbed', 81: 'Raw', 82: 'Switch'}
		return categories[cateogry_id] if cateogry_id in categories else 'Other'

	def get_magnet_link(self,torrent_page):
		soup = soup = bs(requests.get('{}{}'.format(self.url,torrent_page),allow_redirects=True).text,'html.parser')
		try: return [a.get('href') for a in soup.findAll('a') if search('magnet',a.get('href'))][0]
		except IndexError: return None