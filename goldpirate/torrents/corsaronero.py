from re import search, sub

from bs4 import BeautifulSoup as bs
from requests import get
from requests.exceptions import ConnectTimeout, ReadTimeout


class CorsaroNero:
    def __init__(self, user_agent):
        self.url = "https://ilcorsaronero.link"
        self.search = "/search?q=##"
        self.delimiter = "+"
        self.sort = "/search?q=##&sort=@@&order=desc"
        self.sort_type = {
            "age": "timestamp",
            "size": "size",
            "seed": "seeders",
            "leech": "leechers",
        }
        self.page = "&page=@@"
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
        titles_list = list()
        search_texts = list()
        for i in range(pages):
            page_url = sub("@@", str(i), self.page)
            soup = bs(self._get(f"{self.url}{endpoint}{page_url}").text, "html.parser")
            search_texts.extend(soup.findAll("td"))
            titles_list.extend(soup.findAll("th"))
        return search_texts, titles_list[7:]

    def build_list(self, query, pages, sort=None):
        try:
            search_list, title_list = self._search_torrents(query, pages, sort)
        except (ConnectTimeout, ReadTimeout):
            return []
        search_list = [x for x in search_list if x.text and not x.get("colspan")]
        singles = [search_list[i * 6 : i * 6 + 6] for i in range(len(search_list) // 6)]
        torrents = list()
        for torrent, title in zip(singles, title_list):
            category = torrent[0].text
            torrent_page = title.find("a").get("href")
            seed, leech, size, time = [
                "0" if x == "n/a" else x for x in [t.text for t in torrent[1:5]]
            ]
            torrents.append(
                [
                    "CorsaroNero",
                    title.text,
                    f"{self.url}{torrent_page}",
                    time.strip().split(" ")[0],
                    category.strip(),
                    sub(r"\d+$", "", size.strip()),
                    int(sub(",", "", seed)),
                    int(sub(",", "", leech)),
                ]
            )
        return torrents

    def get_magnet_link(self, torrent_page):
        try:
            soup = bs(self._get(torrent_page).text, "html.parser")
            return [
                a.get("href")
                for a in soup.findAll("a")
                if search("magnet", str(a.get("href")))
            ][0]
        except IndexError:
            return None
