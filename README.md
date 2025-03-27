# Gold Pirate

Why join the Navy if you can be a Pirate?  
Python script to download torrent from the Internet.

## Installation
The package can be downloaded directly from [PyPi](https://pypi.org/project/goldpirate/).
```bash
pip install goldpirate
```

## Setup QBitTorrent
In order to download torrent, you need QBitTorrent.
1. Download and install [QBitTorrent](https://www.qbittorrent.org/download.php)
2. Go to **Settings** > **WEB UI**
	* Check **Web UI interface**
	* Set port to **8080**
	* Check **Bypass authentication for clients on localhost**

![alt text](https://github.com/mortafix/homebrew-goldpirate/blob/master/images/QBit-Settings.png?raw=true)  

## Example
You can see the help, `-h`, man to know all the possibile commands.
```bash
goldpirate -q "The Matrix"
goldpirate -q "Harry Potter" -s age
goldpirate -q "Back to the Future" -s size -e rarbg -o /home/me/movies --plain-text --verbose
```
![alt text](https://github.com/mortafix/homebrew-goldpirate/blob/master/images/Example.png?raw=true)  

## Supported Sites
1. [1337x](https://1337x.to/)
2. [LimeTorrents](https://limetorrents.info/)
3. [TorLock](https://torlock.com)
4. [TorrentDownloads](https://torrentdownloads.me)
5. [IlCorsaroNero](https://ilcorsaronero.link)
6. [RarBG](https://rargb.to)
7. [ThePirateBay](https://thepiratebay.org)