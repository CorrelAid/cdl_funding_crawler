import random
import time
from pathlib import Path
import pickle

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class SeleniumScraper:
    @staticmethod
    def get_url(page_number: int):
        return (
            f"https://www.foerderdatenbank.de/"
            f"SiteGlobals/FDB/Forms/Suche/"
            f"Startseitensuche_Formular.html?"
            f"gtp=%2526816beae2-d57e-4bdc-b55d-392bc1e17027_list%253D{page_number}"
            f"&submit=Suchen"
            f"&filterCategories=FundingProgram"
        )

    @staticmethod
    def jitter_time_out(mean: int = 2):
        time.sleep(mean + random.random())

    def accept_cookies(self):
        cookie_button = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[text()='Auswahl bestätigen']")
            )
        )
        cookie_button.click()

        self.cookies_accepted = True

    def read_page(self, page_number: int):
        page_data = {}

        self.driver.get(self.get_url(page_number))

        if not self.cookies_accepted:
            self.accept_cookies()

        try:
            count = self.driver.find_element(By.ID, "hits--count").text
            page_data["count"] = count

            filter_data = {}
            accordion_openers = self.driver.find_elements(
                By.CLASS_NAME, "sidebar--accordion-opener"
            )
            filter_categories = self.driver.find_elements(By.CLASS_NAME, "sidebar--ul")
            for filter_idx, filter_category in enumerate(filter_categories):
                current_filter_name = (
                    accordion_openers[filter_idx]
                    .find_element(By.CLASS_NAME, "btn--label")
                    .text
                )

                filter_data[current_filter_name] = []
                filters = filter_category.find_elements(By.CLASS_NAME, "sidebar--li")
                for curr_filter in filters:
                    filter_data[current_filter_name].append(
                        (
                            curr_filter.find_element(
                                By.CLASS_NAME, "link--label"
                            ).get_attribute("innerHTML"),
                            curr_filter.find_element(
                                By.CLASS_NAME, "link--count"
                            ).get_attribute("innerHTML"),
                        )
                    )
            page_data["curr_filter"] = filter_data

            urls = []
            search_results = self.driver.find_elements(By.CLASS_NAME, "searchresult")
            for result in search_results:
                result.find_element(By.CLASS_NAME, "card--title").find_element(
                    By.TAG_NAME, "a"
                )
                urls.append(
                    search_results[0]
                    .find_element(By.CLASS_NAME, "card--title")
                    .find_element(By.TAG_NAME, "a")
                    .get_attribute("href")
                )
            page_data["urls"] = urls

            pagination = self.driver.find_element(By.CLASS_NAME, "pagination")
            final_page = (
                pagination.find_elements(By.TAG_NAME, "li")[-2]
                .find_element(By.TAG_NAME, "a")
                .text
            )
            page_data["final_page"] = final_page
        except (NoSuchElementException, TimeoutException):
            page_data = None

        return page_data

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)

        self.cookies_accepted = False


if __name__ == "__main__":
    chrome_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=chrome_service)

    scraper = SeleniumScraper(driver)

    results = {page: [] for page in range(1, 254)}

    for run_idx in range(5):
        pages = list(range(1, 254))
        random.shuffle(pages)
        for page_number in pages:
            results[page_number].append(scraper.read_page(page_number))
            scraper.jitter_time_out()

        with (Path(__file__).parent / f"data_{run_idx}.pkl").open("wb") as fp:
            pickle.dump(results, fp)

    with (Path(__file__).parent / "data.pkl").open("wb") as fp:
        pickle.dump(results, fp)
