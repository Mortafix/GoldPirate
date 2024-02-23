from datetime import datetime
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout


class RarBG:
    def __init__(self, user_agent):
        self.url = "https://rargb.to"
        self.search = "?search=##"
        self.delimiter = "%20"
        self.sort = "?search=##&order=@@&by=DESC"
        self.sort_type = {
            "age": "data",
            "size": "size",
            "seed": "seeders",
            "leech": "leechers",
        }
        self.page = "/search/@@/"
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
                    f"{self.url}{sub('@@', str(i + 1), self.page)}{url_attach}",
                    headers=self.user_agent,
                    timeout=3,
                    verify=False,
                ).text,
                "html.parser",
            ).findAll("td")[45:-3]
            for i in range(pages)
        ]
        return sum(torrents_per_page, start=[])

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except ConnectTimeout:
            return []
        singles = [search_list[i : i + 8] for i in range(0, len(search_list), 8)]
        torrents = list()
        for torrent in singles:
            name = torrent[1].text.strip().split("\n")[0]
            link_page = torrent[1].find("a").get("href")
            category = torrent[2].text.split("/")[0]
            time, size, seed, leech = [t.text for t in torrent[3:7]]
            torrents.append(
                [
                    "RarBG",
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
        if m := search(r"(\d{4})-(\d{2})-(\d{2})", site_date):
            year, month, day = m.groups()
            return datetime(int(year), int(month), int(day)).strftime("%d.%m.%Y")
        return ""

    def get_magnet_link(self, torrent_page):
        soup = bs(
            requests.get(torrent_page, allow_redirects=True, verify=False).text,
            "html.parser",
        )
        try:
            return [
                a.get("href")
                for a in soup.findAll("a")
                if search("magnet", a.get("href") or "")
            ][0]
        except IndexError:
            return None
