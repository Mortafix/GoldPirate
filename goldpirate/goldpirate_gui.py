import pandas as pd
import streamlit as st
from fake_useragent import UserAgent
from humanfriendly import parse_size
from qbittorrentapi import Client
from qbittorrentapi.exceptions import APIConnectionError, LoginFailed
from requests import packages
from torrents.corsaronero import CorsaroNero
from torrents.limetorrents import LimeTorrents
from torrents.rarbg import RarBG
from torrents.thepiratebay import ThePirateBay
from torrents.torlock import TorLock
from torrents.torrentdownloads import TorrentDownloads
from torrents.x1337 import X1337
from urllib3.exceptions import InsecureRequestWarning

packages.urllib3.disable_warnings(category=InsecureRequestWarning)
st.set_page_config(page_title="GoldPirate", page_icon="☠️", layout="wide")
fake_ua = UserAgent()
qbt = Client(
    st.secrets.qbittorrent.url,
    st.secrets.qbittorrent.port,
    st.secrets.qbittorrent.username,
    st.secrets.qbittorrent.password,
)
SITES = {
    "1337x": X1337(fake_ua.random),
    "LimeTorrents": LimeTorrents(fake_ua.random),
    "TorLock": TorLock(fake_ua.random),
    "TorrentDownloads": TorrentDownloads(fake_ua.random),
    "CorsaroNero": CorsaroNero(fake_ua.random),
    "RarBG": RarBG(fake_ua.random),
    "ThePirateBay": ThePirateBay(fake_ua.random),
}


def sort_all(torrents, sort):
    sort_type = {"size": (parse_size, 5), "seed": (int, 6), "leech": (int, 7)}
    if sort not in sort_type:
        return torrents
    return sorted(
        torrents, key=lambda x: sort_type[sort][0](x[sort_type[sort][1]]), reverse=True
    )


@st.cache_data(show_spinner=False)
def scraping(_site, name, query, pages, sort):
    return _site.build_list(query, pages, sort)


def main():
    st.title("_Gold Pirate_ ☠️")
    # query
    query_form = st.form("query-form")
    query = query_form.text_input("Query", placeholder="search your query here")
    left_col, right_col = query_form.columns(2)
    pages_labels = {1: "Fast", 2: "Normal", 3: "Deep"}
    pages = left_col.select_slider(
        "Search type", pages_labels, 2, format_func=lambda x: pages_labels.get(x)
    )
    sort = right_col.selectbox(
        "Sort", ["seed", "age", "size", "leech"], format_func=lambda x: x.title()
    )
    if query_form.form_submit_button("Search 🕵🏻‍♂️", use_container_width=True):
        if not query:
            return query_form.warning("**Query** can't be empty!", icon="⚠️")
        st.cache_data.clear()
    if not query:
        return

    # searching
    torrents_list = list()
    with st.status(f"**Searching** torrents for `{query}`", expanded=True) as status:
        for i, (name, site) in enumerate(SITES.items()):
            try:
                st.write(f"**{name}** | Searching..")
                torrents = scraping(site, name, query, pages, sort)
                torrents_list.extend(torrents)
                st.write(f"**{name}** | Found **{len(torrents)}** torrent(s)!")
            except Exception:
                st.write("**{name}** | Error..")
                continue
        if not torrents_list:
            return status.update(
                label="Search complete with **NO** results..",
                state="complete",
                expanded=False,
            )
        status.update(
            label=f"Search complete, found **{len(torrents_list)}** torrent(s)!",
            state="complete",
            expanded=False,
        )

    # table
    torrents_sorted = sort_all(torrents_list, sort)
    columns = [
        "Site",
        "Torrent",
        "Torrent Page",
        "Age",
        "Category",
        "Size",
        "Seed",
        "Leech",
    ]
    torrents_df = pd.DataFrame(torrents_sorted, columns=columns)
    torrents_df["Download?"] = False
    data = st.data_editor(
        torrents_df,
        column_config={
            "Torrent Page": st.column_config.LinkColumn(
                display_text="Open page", width="small"
            ),
        },
        disabled=columns,
        use_container_width=True,
        hide_index=True,
    )
    if st.button("Download ⬇️", use_container_width=True):
        if (torrents_to_download := data.loc[data["Download?"]]).empty:
            return
        st.session_state["torrents"] = {
            i: (torrent["Site"], torrent["Torrent"].strip(), torrent["Torrent Page"])
            for i, torrent in torrents_to_download.iterrows()
        }
    if not st.session_state.get("torrents"):
        return

    # check QBitTorrent
    try:
        qbt.auth_log_in()
    except LoginFailed:
        return st.error("Invalid **username** and/or **password**!", icon="❌")
    except APIConnectionError:
        url = f"{qbt.host}:{qbt.port}"
        return st.warning(f"No **QBitTorrent** instance found at _{url}_", icon="⚠️")

    # download
    st.subheader("_Downloads_", divider="gray")
    for i, (site, torrent, page) in st.session_state.torrents.copy().items():
        container = st.empty()
        download_form = container.form(f"download-qbit-{i}")
        download_form.info(torrent, icon="📎")
        left_col, right_col = download_form.columns((2, 1))
        torrent_name = left_col.text_input("Name", placeholder="Torrent rename")
        folders = {path: name for name, path in st.secrets.paths.items()}
        file_folder = right_col.selectbox(
            "Folder", folders, format_func=lambda x: folders.get(x)
        )
        if download_form.form_submit_button("Download 🔗", use_container_width=True):
            if not file_folder:
                download_form.warning("Select a **folder**", icon="⚠️")
                continue
            try:
                magnet = SITES.get(site).get_magnet_link(page)
                qbt.torrents_add(magnet, rename=torrent_name, save_path=file_folder)
                st.session_state.torrents.pop(i)
                container.empty()
                st.toast("✅ Sent to _QBitTorrent_ **succesfully**!")
            except Exception:
                st.toast("❌ _Ops!_ Something went **wrong**..")
                continue


if __name__ == "__main__":
    main()
