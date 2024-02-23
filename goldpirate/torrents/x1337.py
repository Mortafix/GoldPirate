from datetime import datetime
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout


class X1337:
    def __init__(self, user_agent):
        self.url = "https://1377x.to"
        self.search = "/search/##"
        self.delimiter = "+"
        self.sort = "/sort-search/##/@@/desc"
        self.sort_type = {
            "age": "time",
            "size": "size",
            "seed": "seeders",
            "leech": "leechers",
        }
        self.page = "/@@/"
        self.user_agent = {"User-Agent": user_agent}

    def _search_torrents(self, query, pages, sort=None):
        query_delim = sub(r"\s", self.delimiter, query)
        url_attach = (
            sub("@@", self.sort_type[sort], sub("##", query_delim, self.sort))
            if sort in self.sort_type
            else sub("##", query_delim, self.search)
        )
        torrents_per_page = [
            bs(
                requests.get(
                    f"{self.url}{url_attach}{sub('@@', str(i + 1), self.page)}",
                    headers=self.user_agent,
                    timeout=3,
                    verify=False,
                ).text,
                "html.parser",
            ).findAll("td")
            for i in range(pages)
        ]
        return sum(torrents_per_page, start=[])

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except ConnectTimeout:
            return []
        singles = [search_list[i * 6 : i * 6 + 6] for i in range(len(search_list) // 6)]
        torrents = list()
        for torrent in singles:
            name = torrent[0].text
            category, link_page = [a.get("href") for a in torrent[0].findAll("a")]
            category = search(r"sub\/(\w+)\/", category).group(1)
            seed, leech, time, size = [t.text for t in torrent[1:5]]
            torrents.append(
                [
                    "1337x",
                    name,
                    f"{self.url}{link_page}",
                    self._date_converter(time),
                    category.title(),
                    sub(r"\d+$", "", size),
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def _date_converter(self, site_date):
        if search(r"(am|pm)", site_date):
            return datetime.now().strftime("%d.%m.%Y")
        month, day, year = site_date.split()
        months = {
            "Jan.": 1,
            "Feb.": 2,
            "Mar.": 3,
            "Apr.": 4,
            "May.": 5,
            "Jun.": 6,
            "Jul.": 7,
            "Aug.": 8,
            "Sep.": 9,
            "Oct.": 10,
            "Nov.": 11,
            "Dec.": 12,
        }
        day = int(sub(r"\D+", "", day))
        month = months.get(month, 1)
        return datetime(2000 + int(year[1:]), month, day).strftime("%d.%m.%Y")

    def get_magnet_link(self, torrent_page):
        soup = bs(
            requests.get(torrent_page, allow_redirects=True, verify=False).text,
            "html.parser",
        )
        try:
            return [
                a.get("href")
                for a in soup.findAll("a")
                if search("magnet", a.get("href"))
            ][0]
        except IndexError:
            return None
