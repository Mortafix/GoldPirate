from datetime import datetime, timedelta
from functools import reduce
from re import search, sub

import requests
from bs4 import BeautifulSoup as bs
from requests.exceptions import ConnectTimeout, ReadTimeout


class TorLock:
    def __init__(self, user_agent):
        self.url = "https://www.torlock.com"
        self.search = "/all/torrents/##"
        self.delimiter = "+"
        self.sort = "/all/torrents/##.html?sort=@@&order=desc"
        self.sort_type = {
            "age": "added",
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
                            self.url, url_attach, sub("@@", str(i + 1), self.page)
                        ),
                        headers=self.user_agent,
                        timeout=3,
                        verify=False,
                    ).text,
                    "html.parser",
                ).findAll("td")[27:]
                for i in range(pages)
            ],
            [],
        )

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except (ConnectTimeout, ReadTimeout):
            return []
        singles = [search_list[i * 7 : i * 7 + 7] for i in range(len(search_list) // 7)]
        torrents = list()
        for torrent in singles:
            name = torrent[0].text
            link_page = [a.get("href") for a in torrent[0].findAll("a")]
            if link_page:
                category = int(torrent[0].find("span").get("class")[0][2:])
                time, size, seed, leech = [t.text for t in torrent[1:5]]
                torrents.append(
                    [
                        "TorLock",
                        name,
                        f"{self.url}{link_page[0]}",
                        self._date_converter(time),
                        self._get_category(category),
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
            return datetime.strftime(datetime.now() - timedelta(1), "%d.%m.%Y")
        day, month, year = site_date.split("/")
        return "{:02d}.{:02d}.{}".format(int(month), int(day), int(year))

    def _get_category(self, category_id):
        categories = {
            1: "Movies",
            2: "Music",
            3: "Television",
            4: "Games",
            5: "Software",
            6: "Anime",
            7: "Adult",
            8: "E-Books",
            9: "Images",
            12: "Audio Books",
            0: "Other",
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
