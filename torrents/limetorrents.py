from functools import reduce
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout


class LimeTorrents:
    def __init__(self):
        self.url = "https://limetorrents.info"
        self.search = "/search/all/##"
        self.delimiter = "-"
        self.sort = "/search/all/##/@@"
        self.sort_type = {
            "age": "date",
            "size": "size",
            "seed": "seeds",
            "leech": "leechs",
        }
        self.page = "/@@"

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
                        allow_redirects=True,
                        timeout=3,
                    ).text,
                    "html.parser",
                ).findAll("td")[12:]
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
            _, link_page = [t.get("href") for t in torrent[0].findAll("a")]
            info, size, seed, leech = [t.text for t in torrent[1:5]]
            last_check, category = info.split(" - in ")
            torrents.append(
                [
                    "LimeTorrents",
                    name,
                    link_page,
                    last_check,
                    category,
                    size,
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def get_magnet_link(self, torrent_page):
        soup = soup = bs(
            requests.get(
                "{}{}".format(self.url, torrent_page), allow_redirects=True
            ).text,
            "html.parser",
        )
        try:
            return [
                x.get("href")
                for x in soup.findAll("a", {"class": "csprite_dltorrent"})
                if search("magnet", x.get("href"))
            ][0]
        except IndexError:
            return None

    def get_torrent_page(self, torrent_page):
        return f"{self.url}{torrent_page}"
