import time
from pathlib import Path
import pickle
import random

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
            f"https://www.foerderdatenbank.de/SiteGlobals/FDB/Forms/Suche/Foederprogrammsuche_Formular.html?"
            f"input_=23adddb0-dcf7-4e32-96f5-93aec5db2716&gtp=%2526816beae2-d57e-4bdc-b55d-392bc1e17027_list%253D{page_number}"
            f"&submit=Suchen"
            f"&resourceId=0065e6ec-5c0a-4678-b503-b7e7ec435dfd"
            f"&filterCategories=FundingProgram"
            f"&pageLocale=de"
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

        # Just to load the page count (very dynamic)
        time.sleep(3)

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
            titles = []
            search_result_container = self.driver.find_element(
                By.CLASS_NAME, "searchresult"
            )
            search_results = search_result_container.find_elements(
                By.CLASS_NAME, "card"
            )
            for result in search_results:
                card_title = result.find_element(By.CLASS_NAME, "card--title")
                urls.append(
                    card_title.find_element(By.TAG_NAME, "a").get_attribute("href")
                )
                titles.append(
                    card_title.find_element(By.CLASS_NAME, "link--label").text
                )
            page_data["urls"] = urls
            page_data["titles"] = titles

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
    results = {}
    num_runs = 10
    num_pages = 254
    for browser, browser_manager in [(webdriver.Chrome, ChromeDriverManager)]:
        browser_text = str(browser)
        browser_service = Service(browser_manager().install())
        driver = browser(service=browser_service)

        scraper = SeleniumScraper(driver)

        results[browser_text] = {page: [] for page in range(1, num_pages)}
        results[browser_text]["page_orders"] = []

        for run_idx in range(num_runs):
            pages = list(range(1, num_pages))
            if run_idx != num_runs - 1:
                random.shuffle(pages)
            results[browser_text]["page_orders"].append(pages)

            for page_number in pages:
                results[browser_text][page_number].append(
                    scraper.read_page(page_number)
                )
                scraper.jitter_time_out()

            with (Path(__file__).parent / f"data_{run_idx}.pkl").open("wb") as fp:
                pickle.dump(results, fp)

    with (Path(__file__).parent / "data.pkl").open("wb") as fp:
        pickle.dump(results, fp)
