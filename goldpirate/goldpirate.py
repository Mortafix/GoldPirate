from argparse import ArgumentParser
from fileinput import input as finput
from os import path
from subprocess import check_output

from colorifix.colorifix import erase, paint, ppaint
from fake_useragent import UserAgent
from goldpirate.torrents.corsaronero import CorsaroNero
from goldpirate.torrents.limetorrents import LimeTorrents
from goldpirate.torrents.rarbg import RarBG
from goldpirate.torrents.torlock import TorLock
from goldpirate.torrents.torrentdownloads import TorrentDownloads
from goldpirate.torrents.x1337 import X1337
from halo import Halo
from humanfriendly import parse_size
from qbittorrentapi import Client
from qbittorrentapi.exceptions import APIConnectionError
from requests import packages
from tabulate import tabulate
from toml import load
from urllib3.exceptions import InsecureRequestWarning

packages.urllib3.disable_warnings(category=InsecureRequestWarning)
fake_ua = UserAgent()

SITES = {
    "1337x": X1337(fake_ua.random),
    "LimeTorrents": LimeTorrents(fake_ua.random),
    "TorLock": TorLock(fake_ua.random),
    "TorrentDownloads": TorrentDownloads(fake_ua.random),
    "CorsaroNero": CorsaroNero(fake_ua.random),
    "RarBG": RarBG(fake_ua.random),
}
COLORS = {
    "1337x": 161,
    "LimeTorrents": 48,
    "TorLock": 123,
    "TorrentDownloads": 202,
    "CorsaroNero": 239,
    "RarBG": 33,
}


# ---- Configuration


def change_configuration(script_dir, down_path):
    cfg_path = input("Default download path: ").strip() or down_path
    while not path.exists(cfg_path) or cfg_path == "/tmp":
        erase()
        cfg_path = input(paint("[#red]Folder not exists.[/] Retry: ")) or down_path
    for line in finput(path.join(script_dir, "config.toml"), inplace=1):
        print(line.replace(down_path, cfg_path), end="")
    ppaint("[#green]Successful! New configuration saved correctly.")


# ---- Utils


def get_terminal_window_size():
    return int(check_output(["stty", "size"]).split()[1].decode())


def sanitize_str(string):
    return string.encode("ascii", "ignore").decode().strip()


# ---- Torrents


def print_torrents(torrents, window_size):
    max_name_size = window_size - 89 if window_size < 171 else -1
    table_torrents = [
        (
            i + 1,
            sanitize_str(name[:max_name_size]),
            category,
            f"[#yellow]{age}[/]",
            f"[#blue]{size}[/]",
            f"[#green]{seed}[/]",
            f"[#red]{leech}[/]",
            f"[#{COLORS.get(site)}]{site}[/]",
        )
        for i, (site, name, _, age, category, size, seed, leech) in enumerate(torrents)
    ]
    table_torrents = [
        [paint(("", "[@bold]")[i % 2] + f"{field}[/]") for field in line]
        for i, line in enumerate(table_torrents)
    ]
    table = tabulate(
        table_torrents,
        headers=["Torrent", "Category", "Age", "Size", "Seed", "Leech", "Site"],
        tablefmt="psql",
        showindex=0,
        colalign=("right", "left", "left", "left", "right", "right", "right", "left"),
    )
    print(table)


def sort_all(torrents, sort):
    sort_type = {"size": (parse_size, 5), "seed": (int, 6), "leech": (int, 7)}
    if not sort or sort not in sort_type:
        return torrents
    return sorted(
        torrents, key=lambda x: sort_type[sort][0](x[sort_type[sort][1]]), reverse=True
    )


def download_from_qbittorrent(magnet_link, down_path, config):
    qb = Client(
        config.get("address"),
        config.get("port") or None,
        config.get("username"),
        config.get("password"),
    )
    qb.auth_log_in()
    return qb.torrents_add(magnet_link, savepath=down_path)


def get_torrents(query, pages, sort=None):
    torrents = list()
    for name, site in SITES.items():
        with Halo(text=paint(f"Scanning [#blue]{name}[/]"), spinner="dots"):
            try:
                site_torrents = site.build_list(query, pages, sort)
                torrents.extend(site_torrents)
            except Exception:
                continue
    return torrents


# ---- Main


def main():
    SCRIPT_DIR = path.dirname(path.realpath(__file__))
    config = load(open(path.join(SCRIPT_DIR, "config.toml")))
    config_qbt = config.get("qbittorrent")
    config_search = config.get("search")
    # parser
    parser = ArgumentParser(
        prog="gold-pirate",
        description="Do you want to be a pirate? It's FREE.",
        usage="gold-pirate -q QUERY [-s SORT]",
        epilog='Example: gold-pirate -q "Harry Potter Stone" -s size',
    )
    parser.add_argument(
        "-q", type=str, help="query to search", metavar=("QUERY"), required=True
    )
    parser.add_argument(
        "-s", type=str, help="sort result [age,size,seed,leech]", metavar=("SORT")
    )
    parser.add_argument("-o", type=str, help="download folder")
    parser.add_argument("-c", action="store_true", help="change configuration")
    parser.add_argument(
        "-V",
        "--verbose",
        action="store_true",
        help="print torrent page and magnet link",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="script version",
        action="version",
        version="gold-pirate v1.7.3",
    )
    args = parser.parse_args()
    query = args.q
    sort = args.s if args.s else config_search.get("sort")
    config = args.c
    verbose = args.verbose
    down_path = args.o or config_qbt.get("download_folder")
    # search
    if down_path == "/tmp" or config:
        change_configuration(SCRIPT_DIR, down_path)
        return main()
    torrents = sort_all(get_torrents(query, config_search.get("pages"), sort), sort)
    limit = min(len(torrents), config_search.get("limit"))
    # download
    if limit > 0 and torrents:
        print_torrents(torrents[:limit], get_terminal_window_size())
        while True:
            torr_idx = input(paint("> Select a torrent [@bold][0:exit][/]: "))
            while not torr_idx.isdigit() or not int(torr_idx) in range(limit + 1):
                torr_idx = input(paint("> Select a torrent [@bold][0:exit][/]: "))
            torr_idx = int(torr_idx)
            if torr_idx == 0:
                exit(-1)
            torrent_page = torrents[torr_idx - 1][2]
            magnet = SITES[torrents[torr_idx - 1][0]].get_magnet_link(torrent_page)
            if magnet:
                try:
                    if verbose:
                        ppaint(f"\n[#gray]{torrent_page}[/]\n[@underline]{magnet}[/]\n")
                    download_from_qbittorrent(magnet, down_path, config_qbt)
                    ppaint("[#green]Torrent successfully sent to QBitTorrent![/]\n")
                except APIConnectionError:
                    ppaint("[#red]Unable to find QBitTorrent.[/]\n")
                except Exception:
                    ppaint("[#red]Something went wrong..[/]\n")
            else:
                ppaint("[#red]Magnet link not found.[/]\n")
    else:
        ppaint(f"[#red]No torrent found for [@underline @bold]{query}[/@].[/]")


if __name__ == "__main__":
    main()
