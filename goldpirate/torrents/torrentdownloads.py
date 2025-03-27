from re import search, sub

from bs4 import BeautifulSoup as bs
from requests import get
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

    def _get(self, url):
        return get(
            url, allow_redirects=True, headers=self.user_agent, timeout=3, verify=False
        )

    def _search_torrents(self, query, pages, sort=None):
        endpoint = sub("##", sub(r"\s", self.delimiter, query), self.search)
        search_texts = list()
        for i in range(pages):
            page_url = sub("@@", str(i + 1), self.page)
            soup = bs(self._get(f"{self.url}{endpoint}{page_url}").text, "html.parser")
            search_texts.extend(soup.findAll("div", {"class": "grey_bar3"})[6:-1])
        return search_texts

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
        try:
            soup = bs(self._get(torrent_page).text, "html.parser")
            return [
                a.get("href")
                for a in soup.findAll("a")
                if search("magnet", str(a.get("href")))
            ][0]
        except IndexError:
            return None
