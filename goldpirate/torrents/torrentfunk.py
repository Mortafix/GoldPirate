from datetime import datetime, timedelta
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout


class TorrentFunk:
    def __init__(self, user_agent):
        self.url = "https://torrentfunk.com"
        self.search = "/all/torrents/##.html"
        self.delimiter = "-"
        self.sort = "/all/torrents/##.html?sort=@@&o=desc"
        self.sort_type = {
            "age": "added",
            "size": "size",
            "seed": "seeds",
            "leech": "peers",
        }
        self.page = "&page=@@"
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
            ).findAll("td")[66:]
            for i in range(pages)
        ]
        return sum(torrents_per_page, start=[])

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except ConnectTimeout:
            return []
        singles = [search_list[i : i + 7] for i in range(0, len(search_list), 7)]
        torrents = list()
        for torrent in singles:
            name = torrent[0].text
            link_page = torrent[0].find("a").get("href")
            time, size, seed, leech = [t.text for t in torrent[1:5]]
            torrents.append(
                [
                    "TorrentFunk",
                    name,
                    f"{self.url}{link_page}",
                    self._date_converter(time),
                    "",
                    sub(r"\d+$", "", size),
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def _date_converter(self, site_date):
        if site_date == "Today":
            return datetime.now().strftime("%d.%m.%Y")
        if site_date == "Yesterday":
            return (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")
        day, month, year = site_date.split()
        months = {
            "Jan": 1,
            "Feb": 2,
            "Mar": 3,
            "Apr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Aug": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dec": 12,
        }
        month = months.get(month, 1)
        return datetime(2000 + int(year), month, int(day)).strftime("%d.%m.%Y")

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
