from re import search, sub

from bs4 import BeautifulSoup as bs
from requests import get
from requests.exceptions import ConnectTimeout, ReadTimeout


class LimeTorrents:
    def __init__(self, user_agent):
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
        self.user_agent = {"User-Agent": user_agent}

    def _get(self, url):
        return get(
            url, allow_redirects=True, headers=self.user_agent, timeout=3, verify=False
        )

    def _search_torrents(self, query, pages, sort=None):
        endpoint = (
            sub(
                "@@",
                self.sort_type[sort],
                sub("##", sub(r"\s", self.delimiter, query), self.sort),
            )
            if sort and sort in self.sort_type
            else sub("##", sub(r"\s", self.delimiter, query), self.search)
        )
        search_texts = list()
        for i in range(pages):
            page_url = sub("@@", str(i), self.page)
            soup = bs(self._get(f"{self.url}{endpoint}{page_url}").text, "html.parser")
            search_texts.extend(soup.findAll("td")[12:])
        return search_texts

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except (ConnectTimeout, ReadTimeout):
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
                    f"{self.url}{link_page}",
                    last_check,
                    category,
                    size,
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def get_magnet_link(self, torrent_page):
        try:
            soup = bs(self._get(torrent_page).text, "html.parser")
            return [
                x.get("href")
                for x in soup.findAll("a", {"class": "csprite_dltorrent"})
                if search("magnet", x.get("href"))
            ][0]
        except IndexError:
            return None
