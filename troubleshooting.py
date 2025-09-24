import re
from typing import Optional
from tqdm import tqdm

import polars as pl
from bs4 import BeautifulSoup
from requests import Session, HTTPError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://www.foerderdatenbank.de/"
ENTRY_URL = "SiteGlobals/FDB/Forms/Suche/Expertensuche_Formular.html?filterCategories=FundingProgram"
HEADERS = {}


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


def get_enumeratable_url_template(session: Session) -> str:
    """
    Creates an URL template for iterating over the overview pagination
    The returned template will contain:
    - the filters set with the entrypoint url
    - some query param for session stuff (yielded from their backend)
    - and a `{page}` tag that can be interpolated subsequently
    """
    resp = session.get(BASE_URL + ENTRY_URL)
    resp.raise_for_status()

    html = resp.text
    if not html:
        raise ValueError("No html found")

    soup = BeautifulSoup(html, "html.parser")
    link_obj = soup.find("a", class_="page")
    if not link_obj:
        raise ValueError("No page link found")

    link = link_obj["href"]
    link_template = re.sub(r"(_list%\d+D)\d+", r"\g<1>{page}", link)
    return BASE_URL + link_template


def fetch_page_meta(session: Session, url_template: str, p: int) -> dict:
    url = url_template.format(page=str(p))
    print(f"Fetching data for '{url}'")

    resp = session.get(url)
    resp.raise_for_status()
    html = resp.text
    if not html:
        raise ValueError(f"No html found for page {p}")

    soup = BeautifulSoup(html, "html.parser")
    record = {
        "page": p,
        "hits_count": 0,
        "records_on_page": 0,
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

    return record


if __name__ == "__main__":
    sess = get_session()
    url_template = get_enumeratable_url_template(sess)

    records = []
    p_cursor = 1
    while True:
        try:
            rec = fetch_page_meta(sess, url_template=url_template, p=p_cursor)
            records.append(rec)
            p_cursor += 1
            if rec["records_on_page"] == 0:
                break
        except HTTPError as e:
            print(f"got error: {e}")
            break

    data = pl.DataFrame(records)
    data.write_csv("troubleshooting.csv")
