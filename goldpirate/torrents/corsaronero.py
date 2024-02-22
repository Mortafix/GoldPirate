from functools import reduce
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout, ReadTimeout


class CorsaroNero:
    def __init__(self, user_agent):
        self.url = "https://ilcorsaronero.link"
        self.search = "/advsearch.php?search=##"
        self.delimiter = "+"
        self.sort = "/advsearch.php?search=##&&order=@@&by=DESC"
        self.sort_type = {
            "age": "data",
            "size": "size",
            "seed": "seeds",
            "leech": "peers",
        }
        self.page = "&page=@@"
        self.user_agent = {"User-Agent": user_agent}

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
                            self.url, url_attach, sub("@@", str(i), self.page)
                        ),
                        headers=self.user_agent,
                        timeout=3,
                        verify=False,
                    ).text,
                    "html.parser",
                ).findAll("td")[18:-3]
                for i in range(pages)
            ],
            [],
        )

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except (ConnectTimeout, ReadTimeout):
            return []
        search_list = [x for x in search_list if x.text and not x.get("colspan")]
        singles = [search_list[i * 6 : i * 6 + 6] for i in range(len(search_list) // 6)]
        torrents = list()
        for torrent in singles:
            category = torrent[0].text
            name = torrent[1].find("a").text
            link_page = sub(
                self.url, "", [a.get("href") for a in torrent[1].findAll("a")][0]
            )
            size = torrent[2].text
            time, seed, leech = [
                "0" if x == "n/a" else x for x in [t.text for t in torrent[3:]]
            ]
            torrents.append(
                [
                    "CorsaroNero",
                    name,
                    f"{self.url}{link_page}",
                    sub(r"(\d\d)$", r"20\1", time),
                    category,
                    sub(r"\d+$", "", size),
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def get_magnet_link(self, torrent_page):
        soup = bs(
            requests.get(torrent_page, allow_redirects=True, verify=False).text,
            "html.parser",
        )
        try:
            return [
                a.get("href")
                for a in soup.findAll("a")
                if search("magnet", str(a.get("href")))
            ][0]
        except IndexError:
            return None
