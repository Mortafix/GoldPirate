#!/usr/bin/env python3
# Author: Moris Doratiotto

import os
import subprocess
import json
import fileinput
from functools import reduce
from requests.exceptions import ConnectionError
from re import search,sub
import argparse
from tabulate import tabulate
from qbittorrent import Client
from qbittorrent.client import LoginRequired
from torrents.limetorrents import LimeTorrents
from torrents.x1337 import X1337
from torrents.torlock import TorLock

SITES = {'1337x':X1337(),'LimeTorrents':LimeTorrents(),'TorLock':TorLock()}
class Colors: 
	BOLD='\x1b[1m'
	GREEN,LGREEN = '\x1b[1m\x1b[32m','\x1b[0m\x1b[32m'
	RED,LRED = '\x1b[1m\x1b[31m','\x1b[0m\x1b[31m'
	BLUE,LBLUE = '\x1b[1m\x1b[34m','\x1b[0m\x1b[34m'
	YELLOW,LYELLOW =  '\x1b[1m\x1b[33m','\x1b[0m\x1b[33m'
	SITES = {'1337x':'\x1b[38;5;161m','LimeTorrents':'\x1b[38;5;48m','TorLock':'\x1b[38;5;123m'}
	ENDC = '\033[0m'

def read_config(cfg_path):
	with open(os.path.join(cfg_path,'config.json'), 'r') as cfg:
		cfg_json = json.loads(''.join([l for l in [sub('\t|\n','',l) for l in cfg.readlines()] if l and l[0] != '/']))
	return cfg_json['download-folder'],cfg_json['defualt-sort']

def change_configuration(cfg_path):
	path = input('Download path [{}]: '.format(DOWN_PATH)).strip()
	path = path if path else DOWN_PATH
	while not os.path.exists(path) or path == '/tmp':
		path = input('Folder not exists. Retry: ')
		path = path if path else DOWN_PATH
	if path != DOWN_PATH:
		for line in fileinput.input(os.path.join(SCRIPT_DIR,'config.json'), inplace = 1): 
			print(line.replace(DOWN_PATH,path),end='')
		print('Successful! New configuration saved correctly.')

def print_torrents(torrents_list,size):
	max_name_size = size-89 if size < 171 else -1
	headers = ['Torrent','Category','Age','Seed','Leech','Size','Site']
	table = [(	i+1 if i%2 == 0 else '{}{}{}'.format(Colors.BOLD,i+1,Colors.ENDC),
				n[:max_name_size].encode('ascii', 'ignore').decode() if i%2 == 0 else '{}{}{}'.format(Colors.BOLD,n[:max_name_size].encode('ascii', 'ignore').decode(),Colors.ENDC),
				c if i%2 == 0 else '{}{}{}'.format(Colors.BOLD,c,Colors.ENDC),
				'{}{}{}'.format(Colors.LYELLOW,a,Colors.ENDC) if i%2 == 0 else '{}{}{}'.format(Colors.YELLOW,a,Colors.ENDC),
				'{}{}{}'.format(Colors.LGREEN,s,Colors.ENDC) if i%2 == 0 else '{}{}{}'.format(Colors.GREEN,s,Colors.ENDC),
				'{}{}{}'.format(Colors.LRED,l,Colors.ENDC) if i%2 == 0 else '{}{}{}'.format(Colors.RED,l,Colors.ENDC),
				'{}{}{}'.format(Colors.LBLUE,sub(r'(\.\d)\d',r'\1',si),Colors.ENDC) if i%2 == 0 else '{}{}{}'.format(Colors.BLUE,sub(r'(\.\d)\d',r'\1',si),Colors.ENDC),
				'{}{}{}'.format(Colors.SITES[site],site,Colors.ENDC)) for i,(site,n,_,a,c,si,s,l) in enumerate(torrents_list)]
	print(tabulate(table,headers=headers,tablefmt='psql',showindex=0,colalign=('right','left','left','left','right','right','right','left')))

def get_terminal_window_size():
	return int(subprocess.check_output(['stty', 'size']).split()[1].decode())

def size_to_int(size):
	if (s := search(r'([\d\.]+)\sTB',size)): return float(s.group(1)) * 1000 * 1000 * 1000 * 1024
	if (s := search(r'([\d\.]+)\sGB',size)): return float(s.group(1)) * 1000 * 1000 * 1024
	if (s := search(r'([\d\.]+)\sMB',size)): return float(s.group(1)) * 1000 * 1024
	if (s := search(r'([\d\.]+)\sKB',size)): return float(s.group(1)) * 1024
	if (s := search(r'([\d\.]+)\sbytes',size)): return float(s.group(1))

def sort_all(torrents,sort):
	sort_type = {'size':(size_to_int,5),'seed':(int,6),'leech':(int,7)}
	if not sort or sort not in sort_type: return torrents
	return sorted(torrents,key=lambda x:sort_type[sort][0](x[sort_type[sort][1]]),reverse=True)

def download_from_qbittorrent(magnet_link):
	qb = Client("http://127.0.0.1:8080/")
	qb.login()
	qb.download_from_link(magnet_link,savepath=DOWN_PATH)

def get_torrents(query,sort=None):
	return reduce(lambda x,y: x+y,[obj.build_list(query,sort) for name,obj in SITES.items()],[])

if __name__ == '__main__':
	SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
	DOWN_PATH,DEFAULT_SORT = read_config(SCRIPT_DIR)
	# parser 
	parser = argparse.ArgumentParser(prog='gold-pirate',description='Do you want to be a pirate? It\'s FREE.',usage='gold-pirate -q QUERY [-s SORT]',epilog='Example: gold-pirate -q "Harry Potter Stone" -s size')
	parser.add_argument('-q',type=str,help='query to search',metavar=('QUERY'))
	parser.add_argument('-s',type=str,help='sort result [age,size,seed,leech]',metavar=('SORT'))
	parser.add_argument('-c',action='store_true',help='change configuration')
	parser.add_argument('-v','--version',help='script version',action='version',version='gold-pirate v1.0.0')
	args = parser.parse_args()
	query = args.q
	sort = args.s if args.s else DEFAULT_SORT
	config = args.c
	# search
	if DOWN_PATH == '/tmp' or config: change_configuration(SCRIPT_DIR); exit(-1)
	if not query: print('usage: gold-pirate -q QUERY [-s SORT]'); exit(-1)
	wind_size = get_terminal_window_size()
	torrents = sort_all(get_torrents(query,sort),sort)
	limit = len(torrents) if len(torrents) < 50 else 50
	# download
	if limit > 0 and torrents:
		print_torrents(torrents[:limit],wind_size)
		while True:
			while (inp := int(input(f'Select a torrent to download [0:exit]: '))) not in range(limit+1): pass
			if inp == 0: exit(-1)
			link_torrent = torrents[inp-1][2]
			magnet = SITES[torrents[inp-1][0]].get_magnet_link(link_torrent)
			if magnet:
				try: 
					download_from_qbittorrent(magnet)
					print('Torrent successfully sent to QBitTorrent!'); print()
				except ConnectionError: print('Open QBitTorrent. If it\'s already open, check the configuration.')
			else: print('Magnet link not found..')
	else: print('No torrent found for \'{}\'.'.format(query))
