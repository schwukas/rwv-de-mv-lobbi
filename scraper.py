#!/usr/bin/env python3

import requests
import re
import scraperwiki
import ftfy

from bs4 import BeautifulSoup as bs


os.environ["SCRAPERWIKI_DATABASE_NAME"] = "sqlite:///data.sqlite"

# The internet archive has data without broken encoding. Use this for years
# 2001-2013 (inclusive)
ARCHIVE_URL = "https://web.archive.org/web/20150117032248/http://www.lobbi-mv.de:80/chronik/"
BASE_URL = "https://www.lobbi-mv.de/chronik-rechter-gewalt/"
BROKEN_YEARS = range(2002, 2014)  # excluding 2014


def _make_soup(url, encoding):
    """Return a beautiful soup object generated from the given url.
    """
    r = requests.get(BASE_URL)
    r.encoding = encoding
    page = r.text
    page = ftfy.fix_text(page)
    return bs(page, "lxml")


soup = _make_soup(BASE_URL, "utf-8")

# Get all currently available years.
years = list()
for ul in soup.find_all("ul", class_="tabNavigation"):
    for year in ul.find_all("li"):
        years.append(int(year.get_text()))


for year in years:
    if year in BROKEN_YEARS:
        soup = _make_soup(ARCHIVE_URL, "latin-1")

    report_container = soup.find(id=year)
    reports = report_container.find_all("div")

    for report in reports:
        # Extract the tags with special information.
        landkreis = report.find("span", class_="small").extract().get_text()
        # Remove 'Landkreis' from the location.
        landkreis = landkreis.split(" ")[-1]
        landkreis = re.sub(r"[()]", "", landkreis)

        source = report.find("p").find("span", class_="small").extract().get_text()
        source = source.replace("Quelle: ", "").strip()

        # Now parse the remainders.
        report_body = report.get_text().split("\n")

        date_and_location = report_body[0].split("-")
        start_date = date_and_location[0].strip()
        description = report_body[1]

        city = date_and_location[1].strip()
        locations = landkreis + ", " + city

        # No unique identifier. Instead use a combination of the below.
        uri = city + "_" + start_date + "_" + "DE-MV"

        scraperwiki.sqlite.save(
            unique_keys=["uri"],
            data={"uri": uri,
                  "title": "",
                  "description": description,
                  "startDate": start_date,
                  "endDate": "",
                  "iso_3166_2": "DE-MV"},
            table_name="data"
        )

        scraperwiki.sqlite.save(
            unique_keys=["reportURI"],
            data={"reportURI": uri,
                  "subdivisons": locations},
            table_name="locations"
        )

        for s in source.split(","):
            source = re.sub("- ", "-", s)

            scraperwiki.sqlite.save(
                unique_keys=["reportURI"],
                data={"reportURI": uri,
                      "name": source.strip(),
                      "published_date": "",
                      "url": ""},
                table_name="sources"
            )
