from datetime import datetime
from functools import reduce
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout


class X1337:
    def __init__(self):
        self.url = "https://1377x.to"
        self.search = "/search/##"
        self.delimiter = "+"
        self.sort = "/sort-search/##/@@/desc"
        self.sort_type = {
            "age": "time",
            "size": "size",
            "seeders": "leechers",
            "leech": "leechers",
        }
        self.page = "/@@/"
        self.user_agent = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36"
        }

    def _search_torrents(self, query, pages, sort=None):
        url_attach = (
            sub(
                "@@",
                self.sort_type[sort],
                sub("##", sub(r"\s", self.delimiter, query), self.sort),
            )
            if sort and sort in self.sort_type
            else sub("##", sub(r"\s", self.delimiter, query), self.search)
        )
        return reduce(
            lambda x, y: x + y,
            [
                bs(
                    requests.get(
                        "{}{}{}".format(
                            self.url, url_attach, sub("@@", str(i + 1), self.page)
                        ),
                        headers=self.user_agent,
                        timeout=3,
                    ).text,
                    "html.parser",
                ).findAll("td")
                for i in range(pages)
            ],
            [],
        )

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
                    link_page,
                    self._date_converter(time),
                    category.title(),
                    sub(r"\d+$", "", size),
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def _date_converter(self, site_date):
        if search(r"\d\d:\d\d", site_date):
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
        return (
            "{:02d}.{:02d}.20{}".format(
                int(sub(r"\D+", "", day)), months[month], year[1:]
            )
            if not search("(am|pm)", site_date)
            else "{}.{}.2020".format(months[day], int(sub(r"\D+", "", year)))
        )

    def get_magnet_link(self, torrent_page):
        soup = soup = bs(
            requests.get(
                "{}{}".format(self.url, torrent_page), allow_redirects=True
            ).text,
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

    def get_torrent_page(self, torrent_page):
        return f"{self.url}{torrent_page}"
