from functools import reduce
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout, ReadTimeout


class TorrentDownloads:
    def __init__(self, user_agent):
        self.url = "https://www.torrentdownloads.me"
        self.search = "/search/?search=##"
        self.delimiter = "+"
        self.sort = None
        self.sort_type = None
        self.page = "&page=@@"
        self.user_agent = {"User-Agent": user_agent}

    def _search_torrents(self, query, pages, sort=None):
        url_attach = sub("##", sub(r"\s", self.delimiter, query), self.search)
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
                        verify=False,
                    ).text,
                    "html.parser",
                ).findAll("div", {"class": "grey_bar3"})[6:-1]
                for i in range(pages)
            ],
            [],
        )

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except (ConnectTimeout, ReadTimeout):
            return []
        torrents = list()
        for torrent in search_list:
            if not search("No torrents", torrent.text):
                name = torrent.find("p").text
                link_page = [a.get("href") for a in torrent.find("p").findAll("a")][0]
                category = int(
                    search(
                        r"menu_icon(\d+)", torrent.find("p").find("img").get("src")
                    ).group(1)
                )
                leech, seed, size = [
                    s.text
                    for s in torrent.findAll("span")
                    if s.text and not search("mail", s.text)
                ]
                torrents.append(
                    [
                        "TorrentDownloads",
                        name,
                        f"{self.url}{link_page}",
                        "",
                        self._get_category(category),
                        sub(r"\xa0", " ", size),
                        int(sub(",", "", seed)),
                        int(sub(",", "", leech)),
                    ]
                )
        return torrents

    def _get_category(self, category_id):
        categories = {
            4: "Movies",
            5: "Music",
            8: "Television",
            3: "Games",
            7: "Software",
            1: "Anime",
            2: "E-Books",
            9: "Other",
        }
        return categories[category_id] if category_id in categories else "Other"

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
