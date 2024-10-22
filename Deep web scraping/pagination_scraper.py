from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from time import sleep


class PaginationScraper:
    def __init__(self, driver_path):
        # Set up ChromeDriver
        self.chrome_driver_path = driver_path
        service = Service(executable_path=self.chrome_driver_path)
        self.driver = webdriver.Chrome(service=service)

    def detect_pagination_pattern(self, driver):
        """
        Detects if the page uses Next Button, Page Numbers, or Infinite Scroll.
        """
        try:
            # Check for "Next" button
            next_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Next')]")
            if next_button:
                return "next_button"
        except Exception:
            pass

        try:
            # Check for page number links
            page_number_links = driver.find_elements(By.CSS_SELECTOR, "a.page-numbers")
            if page_number_links:
                return "page_numbers"
        except Exception:
            pass

        try:
            # Check for Infinite Scroll (by trying to scroll down and see if more content loads)
            initial_content = driver.page_source
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)  # Wait for content to load
            new_content = driver.page_source
            if new_content != initial_content:
                return "infinite_scroll"
        except Exception:
            pass

        return "unknown"

    def scrape_with_next_button(self, url, content_selector):
        """
        Scrape pages using a Next Button until it no longer exists.
        """
        self.driver.get(url)

        while True:
            # Scrape content on the current page
            self._scrape_page_content(content_selector)

            try:
                # Find and click the "Next" button
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Next')]"))
                )
                next_button.click()
                sleep(2)  # Wait for the next page to load
            except TimeoutException:
                print("No more 'Next' buttons found. Scraping finished.")
                break

    def scrape_with_page_numbers(self, base_url, total_pages, content_selector):
        """
        Scrape pages by iterating over page numbers.
        """
        for page in range(1, total_pages + 1):
            page_url = f"{base_url}{page}"
            self.driver.get(page_url)
            print(f"Scraping page {page}...")

            # Scrape content on the current page
            self._scrape_page_content(content_selector)
            sleep(2)

    def scrape_infinite_scroll(self, url, content_selector):
        """
        Scrape pages with infinite scroll by scrolling until no new content is loaded.
        """
        self.driver.get(url)
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while True:
            print("Scrolling...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sleep(2)  # Wait for the new content to load

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("No more new content found.")
                break
            last_height = new_height

            # Scrape content on the current page
            self._scrape_page_content(content_selector)

    def _scrape_page_content(self, content_selector):
        """
        Helper function to scrape content based on a CSS selector.
        """
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        content_elements = soup.select(content_selector)

        for element in content_elements:
            print(element.text.strip())  # Replace this with your custom logic for handling content

    def quit(self):
        """
        Close the WebDriver instance.
        """
        self.driver.quit()


# Usage Example:
# --------------
# This can be saved as a module and imported into another script.

def run_scraper(base_url, content_selector, driver_path):
    scraper = PaginationScraper(driver_path)

    # Detect pagination pattern
    scraper.driver.get(base_url)
    pattern = scraper.detect_pagination_pattern(scraper.driver)

    if pattern == "next_button":
        print("Detected Next Button pattern.")
        scraper.scrape_with_next_button(base_url, content_selector)
    elif pattern == "page_numbers":
        print("Detected Page Numbers pattern.")
        # You would need to know the total number of pages in advance
        total_pages = 5  # Replace with logic to detect total number of pages
        scraper.scrape_with_page_numbers(base_url, total_pages, content_selector)
    elif pattern == "infinite_scroll":
        print("Detected Infinite Scroll pattern.")
        scraper.scrape_infinite_scroll(base_url, content_selector)
    else:
        print("No known pagination pattern detected.")

    scraper.quit()
