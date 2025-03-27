from argparse import ArgumentParser
from fileinput import input as finput
from os import path
from re import sub
from subprocess import check_output

from colorifix.colorifix import erase, paint, ppaint
from fake_useragent import UserAgent
from goldpirate.torrents.corsaronero import CorsaroNero
from goldpirate.torrents.limetorrents import LimeTorrents
from goldpirate.torrents.rarbg import RarBG
from goldpirate.torrents.thepiratebay import ThePirateBay
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
    # "1337x": X1337(fake_ua.random),
    "LimeTorrents": LimeTorrents(fake_ua.random),
    "TorLock": TorLock(fake_ua.random),
    "TorrentDownloads": TorrentDownloads(fake_ua.random),
    "CorsaroNero": CorsaroNero(fake_ua.random),
    "RarBG": RarBG(fake_ua.random),
    "ThePirateBay": ThePirateBay(fake_ua.random),
}
COLORS = {
    "1337x": 161,
    "LimeTorrents": 48,
    "TorLock": 123,
    "TorrentDownloads": 202,
    "CorsaroNero": 239,
    "RarBG": 33,
    "ThePirateBay": 180,
}


def paint_or_not(text, colored, _print=True):
    if colored:
        return ppaint(text) if _print else paint(text)
    plain_text = sub(r"\[(#|\/|@).*?\]", "", text)
    return print(plain_text) if _print else plain_text


# ---- Configuration


def change_configuration(script_dir, down_path, colored):
    cfg_path = input("Default download path: ").strip() or down_path
    while not cfg_path or not path.exists(cfg_path) or cfg_path == "/tmp":
        erase()
        text = "[#red]Folder not exists.[/] Retry: "
        cfg_path = input(paint_or_not(text, colored, False)) or down_path
    for line in finput(path.join(script_dir, "config.toml"), inplace=1):
        print(line.replace(down_path, cfg_path), end="")
    text = "[#green]Successful! New configuration saved correctly."
    paint_or_not(text, colored)


# ---- Utils


def get_terminal_window_size():
    return int(check_output(["stty", "size"]).split()[1].decode())


def sanitize_str(string):
    return string.encode("ascii", "ignore").decode().strip()


# ---- Torrents


def print_torrents(torrents, window_size, colored):
    max_name_size = window_size - 89 if window_size < 171 else -1
    if not colored:
        print()
        for i, (site, name, _, _, _, size, _, _) in enumerate(torrents, 1):
            print(f"{i} [{site}] {name[:max_name_size + 30].strip()} ({size})")
        return print()
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


def get_torrents(engine, query, pages, sort=None, colored=False):
    torrents = list()
    for name, site in SITES.items():
        if engine != "all" and engine != name.lower():
            continue
        if not colored:
            print(f"Scanning {name}..")
            try:
                site_torrents = site.build_list(query, pages, sort)
                torrents.extend(site_torrents)
            except Exception:
                continue
            continue
        with Halo(text=paint(f"Scanning [#blue]{name}[/]"), spinner="dots"):
            try:
                site_torrents = site.build_list(query, pages, sort)
                torrents.extend(site_torrents)
            except Exception:
                continue
    if not colored:
        print()
    return torrents


# ---- Main


def args_parser():
    parser = ArgumentParser(
        prog="gold-pirate",
        description="Do you want to be a pirate? It's FREE.",
        usage="gold-pirate -q QUERY [-s SORT] [-e ENGINE] [-o OUTPUT]",
        epilog='Example: gold-pirate -q "Harry Potter" -s size -V',
    )
    parser.add_argument(
        "-q", type=str, help="query to search", metavar=("QUERY"), required=True
    )
    parser.add_argument(
        "-s", type=str, help="sort result [age,size,seed,leech]", metavar=("SORT")
    )
    parser.add_argument("-e", type=str, help="search engine (site)", metavar=("ENGINE"))
    parser.add_argument("-o", type=str, help="download folder", metavar=("OUTPUT"))
    parser.add_argument(
        "-p", "--plain-text", action="store_true", help="plain text output"
    )
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
        version="gold-pirate v1.8.2",
    )
    return parser.parse_args()


def main():
    SCRIPT_DIR = path.dirname(path.realpath(__file__))
    config = load(open(path.join(SCRIPT_DIR, "config.toml")))
    config_qbt = config.get("qbittorrent")
    config_search = config.get("search")
    # args
    args = args_parser()
    query = args.q
    sort = args.s if args.s else config_search.get("sort")
    verbose = args.verbose
    colored = not args.plain_text
    engine = args.e or config_search.get("engine")
    down_path = args.o or config_qbt.get("download_folder")
    # engine
    if engine != "all" and engine not in [site.lower() for site in SITES]:
        text = f"[#red]Search engine '{engine}' not found!"
        paint_or_not(text, colored)
        sites = ", ".join(f"[@underline]{site.lower()}[/@]" for site in SITES)
        text = f"[#red]Must be one in {sites} or [@underline]all"
        return paint_or_not(text, colored)
    # search
    if down_path == "/tmp":
        change_configuration(SCRIPT_DIR, down_path, colored)
        return main()
    torrents = sort_all(
        get_torrents(engine, query, config_search.get("pages"), sort, colored), sort
    )
    limit = min(len(torrents), config_search.get("limit"))
    # download
    if limit > 0 and torrents:
        print_torrents(torrents[:limit], get_terminal_window_size(), colored)
        while True:
            text = "> Select a torrent [@bold][0:exit][/]: "
            torr_idx = input(paint_or_not(text, colored, False))
            while not torr_idx.isdigit() or not int(torr_idx) in range(limit + 1):
                torr_idx = input(paint_or_not(text, colored, False))
            torr_idx = int(torr_idx)
            if torr_idx == 0:
                exit(-1)
            torrent_page = torrents[torr_idx - 1][2]
            magnet = SITES[torrents[torr_idx - 1][0]].get_magnet_link(torrent_page)
            if magnet:
                try:
                    if verbose:
                        text = f"[#gray]{torrent_page}[/]\n\n[@underline]{magnet}[/]\n"
                        paint_or_not(text, colored)
                    download_from_qbittorrent(magnet, down_path, config_qbt)
                    text = "[#green]Torrent successfully sent to QBitTorrent![/]\n"
                    paint_or_not(text, colored)
                except APIConnectionError:
                    text = "[#red]Unable to find QBitTorrent.[/]\n"
                    paint_or_not(text, colored)
                except Exception:
                    text = "[#red]Something went wrong..[/]\n"
                    paint_or_not(text, colored)
            else:
                text = "[#red]Magnet link not found.[/]\n"
                paint_or_not(text, colored)
    else:
        text = f"[#red]No torrent found for [@underline @bold]{query}[/@].[/]"
        paint_or_not(text, colored)


if __name__ == "__main__":
    main()
