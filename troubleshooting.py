import os
import pdb
import re
from urllib.parse import parse_qs, urlparse

import polars as pl
from bs4 import BeautifulSoup
from requests import HTTPError, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.foerderdatenbank.de"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Sec-Ch-Ua": '"Not=A?Brand";v="24", "Chromium";v="',
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}


def get_session():
    session = Session()
    session.headers.update(HEADERS)

    retry_strategy = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        pool_connections=1, pool_maxsize=3, max_retries=retry_strategy, pool_block=False
    )
    session.mount("https://", adapter)
    return session


class FDBSearchClient:
    def __init__(self):
        self.base_url = BASE_URL
        self.endpoint_search = (
            "/SiteGlobals/FDB/Forms/Suche/Expertensuche_Formular.html"
        )
        self._fdb_resource_id = None
        self._fdb_input = None
        self.params = {}

    def init_session(self):
        self.params.update(
            {
                "filterCategories": "FundingProgram",
                "sortOrder": "title_text_sort asc",  # Note: the "+" in the visible URL in the browser would represent a space.
                "submit": "Suchen",
            }
        )
        self.session = get_session()

        # Fetch gtp part
        res = self.session.get(self.base_url + self.endpoint_search, params=self.params)
        res.raise_for_status()

        html = res.text
        if not html:
            raise ValueError("no html found")

        soup = BeautifulSoup(html, "lxml")

        link_obj = soup.find("a", class_="page")
        if not link_obj:
            raise ValueError("No page link found")

        link = link_obj["href"]
        gtp_part = parse_qs(urlparse(self.base_url + link).query)["gtp"][0]
        gtp_template = re.sub(r"(_list%\d+D)\d+", r"\g<1>{page}", gtp_part)
        self._fdb_gtp_template = gtp_template

    def get_overview_page(self, p: int):
        params = self.params.copy()

        cache_file = f"overview_cache/{p}.html"

        if os.path.isfile(cache_file):
            with open(cache_file, "r") as file:
                html = file.read()
        else:
            # append gtp param only for pages > 1 -> otherwise the server fails the request.
            if p > 1:
                gtp = self._fdb_gtp_template.format(page=str(p))
                params = params | {"gtp": gtp}

            res = self.session.get(self.base_url + self.endpoint_search, params=params)
            res.raise_for_status()
            html = res.text
            with open(f"overview_cache/{p}.html", "w") as file:
                file.write(html)

        rec = self._parse_overview_page(html)
        rec["page"] = p
        return rec

    def get_overview_pages(self) -> pl.DataFrame:
        p_cursor = 1
        records = []

        while True:
            print(f"Processing page {p_cursor}")
            rec = self.get_overview_page(p_cursor)

            if rec["records_on_page"] == 0:
                break

            records.append(rec)
            p_cursor += 1

        return pl.DataFrame(records)

    def _parse_overview_page(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        record = {
            "hits_count": 0,
            "records_on_page": 0,
            "entries": [],
        }
        # Extract some metadata
        hits_count_obj = soup.find("span", {"id": "hits--count"})

        if hits_count_obj:
            record["hits_count"] = int(hits_count_obj.text.replace(".", ""))

        entries_obj_list = soup.find_all(
            "div", class_="card card--horizontal card--fundingprogram"
        )
        if entries_obj_list:
            record["records_on_page"] = len(entries_obj_list)

            # extract some additional details from the entries
            entry_detail_list = []
            for entry_obj in entries_obj_list:
                erec = {}
                title_obj = entry_obj.find("p", class_="card--title")
                if not title_obj:
                    continue

                entry_url = title_obj.find("a").get("href")
                entry_title = title_obj.find("span", class_="link--label").text
                entry_title = entry_title.strip()

                entry_detail_list.append(
                    {"title": entry_title, "url": self.base_url + entry_url}
                )
            record["entries"] = entry_detail_list
        return record


if __name__ == "__main__":
    client = FDBSearchClient()
    client.init_session()
    data = client.get_overview_pages()
    data.write_parquet("troubleshooting.parquet")
    print(data)
