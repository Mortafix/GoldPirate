from datetime import datetime, timedelta
from re import search, sub

from bs4 import BeautifulSoup as bs
from requests import get
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

    def _get(self, url):
        return get(
            url, allow_redirects=True, headers=self.user_agent, timeout=3, verify=False
        )

    def _search_torrents(self, query, pages, sort=None):
        query_delim = sub(r"\s", self.delimiter, query)
        endpoint = (
            sub("@@", self.sort_type[sort], sub("##", query_delim, self.sort))
            if sort in self.sort_type
            else sub("##", query_delim, self.search)
        )
        search_texts = list()
        for i in range(pages):
            page_url = sub("@@", str(i + 1), self.page)
            soup = bs(self._get(f"{self.url}{endpoint}{page_url}").text, "html.parser")
            search_texts.extend(soup.findAll("td")[66:])
        return search_texts

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
        try:
            soup = bs(self._get(torrent_page).text, "html.parser")
            return [
                a.get("href")
                for a in soup.findAll("a")
                if search("magnet", a.get("href"))
            ][0]
        except IndexError:
            return None
