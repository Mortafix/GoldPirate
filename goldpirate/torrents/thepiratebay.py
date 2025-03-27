from datetime import datetime
from re import search, sub

import requests
from humanfriendly import format_size
from requests.exceptions import ConnectTimeout, ReadTimeout


class ThePirateBay:
    def __init__(self, user_agent):
        self.url = "https://thepiratebay.org"
        self.api_url = "https://apibay.org"
        self.search = "/q.php?q=##"
        self.delimiter = "%20"
        self.page = "/description.php?id=@@"
        self.user_agent = {"User-Agent": user_agent}

    def _search_torrents(self, query, pages, sort=None):
        url_attach = sub("##", sub(r"\s", self.delimiter, query), self.search)
        return requests.get(f"{self.api_url}{url_attach}").json()

    def _parse_date(self, timestamp):
        if not timestamp or not timestamp.isdigit():
            return 0
        return format(datetime.fromtimestamp(int(timestamp)), "%d.%m.%Y")

    def _get_category(self, category_id):
        major_category_id = int(category_id[0])
        categories = {
            1: "Audio",
            2: "Video",
            3: "App",
            4: "Games",
            5: "Porn",
            6: "Other",
        }
        return categories.get(major_category_id, "Other")

    def build_list(self, query, pages, sort=None):
        try:
            search_list = self._search_torrents(query, pages, sort)
        except (ConnectTimeout, ReadTimeout):
            return []
        if search_list[0].get("name") == "No results returned":
            return []
        return [
            [
                "ThePirateBay",
                torrent.get("name"),
                f"{self.url}{sub('@@',torrent.get('id'),self.page)}",
                self._parse_date(torrent.get("added", 0)),
                self._get_category(torrent.get("category")),
                format_size(int(torrent.get("size"), 0)),
                int(torrent.get("seeders")),
                int(torrent.get("leechers")),
            ]
            for torrent in search_list
        ]

    def get_magnet_link(self, torrent_page):
        torrent_id = search(r"id\=(\d+)", torrent_page).group(1)
        info_url = f"{self.api_url}/t.php?id={torrent_id}"
        try:
            info_torrent = requests.get(info_url).json()
        except Exception:
            return None
        torrent_name = info_torrent.get("name").strip().replace(" ", ".")
        torrent_hash = info_torrent.get("info_hash")
        return f"magnet:?xt=urn:btih:{torrent_hash}&dn={torrent_name}"
