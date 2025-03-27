import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="goldpirate",
    version="1.8.2",
    author="Moris Doratiotto",
    author_email="moris.doratiotto@gmail.com",
    description="A python module to download torrents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mortafix/GoldPirate",
    packages=setuptools.find_packages(),
    install_requires=[
        "halo >= 0.0.31",
        "requests >= 2.28.1",
        "beautifulsoup4 >= 4.11.1",
        "colorifix >= 2.0.4",
        "qbittorrent-api  >= 2022.8.38",
        "tabulate >= 0.8.10",
        "fake_useragent >= 1.4",
        "humanfriendly >= 10.0",
        "toml >= 0.10.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
    ],
    python_requires=">=3.8",
    keywords=["torrent", "download"],
    package_data={
        "goldpirate": [
            "config.toml",
            "torrents/corsaronero.py",
            "torrents/limetorrents.py",
            "torrents/torlock.py",
            "torrents/torrentdownload.py",
            "torrents/x1337.py",
            "torrents/rarbg.py",
            "torrents/thepiratebay.py",
        ]
    },
    entry_points={"console_scripts": ["goldpirate=goldpirate.goldpirate:main"]},
)
