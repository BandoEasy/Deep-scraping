import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Set up Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless (without opening a browser window)
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Set up Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# Function to get links from the main content of a page using user-provided CSS selector
def get_links_from_main_content(url, css_selector):
    driver.get(url)

    try:
        # Wait until the target section is fully loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))  # Wait for the user-defined CSS selector
        )
        time.sleep(3)  # Additional wait to ensure dynamic content loads

        # Parse the page source using BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Find the specific section using the user-defined CSS selector
        main_content = soup.select_one(css_selector)

        # Extract all links within the targeted section
        links = []
        if main_content:
            links = [a['href'] for a in main_content.find_all('a', href=True)]

        # Convert relative URLs to absolute URLs
        links = [urljoin(url, link) for link in links]

        return links

    except Exception as e:
        print(f"Error: {e}")
        return []


# Function to detect and click the "Next" button, handling text-based, SVG-based, and generic cases
def click_next_page_button():
    try:
        # A list of strategies to detect the "Next" button in various scenarios
        next_button_selectors = [
            "//a[contains(text(), 'Next')]",  # Generic "Next" text
            "//a[contains(text(), '>')]",  # Right arrow text
            "//a[contains(text(), '›')]",  # Larger right arrow text
            "//a[contains(@aria-label, 'Next')]",  # Aria label for accessibility
            "//a[@rel='next']",  # rel="next" attribute
            "//button[contains(text(), 'Next')]",  # Button element with "Next" text
            "//button[contains(@class, 'next')]",  # Button with class 'next'
            "//i[contains(@class, 'fa-chevron-right')]",  # FontAwesome Chevron Right Icon
            "//i[contains(@class, 'fa-arrow-right')]",  # FontAwesome Arrow Right Icon
            "//svg[@class='icon' and contains(@viewBox, '0 0 24 24')]",  # SVG icon by class and viewBox
            "//svg/path[contains(@d, 'M9.8 17.2')]"  # Specific SVG path for the arrow
        ]

        next_button = None
        for selector in next_button_selectors:
            try:
                if selector.startswith("//"):
                    # Handle XPath selector
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    # Handle CSS selector (though in this case we're using XPath)
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                if next_button:
                    break  # Stop if we've found the button
            except Exception as e:
                print(f"Attempt with selector {selector} failed: {e}")

        if not next_button:
            print("No 'Next' button detected.")
            return None

        print("Next button detected and clickable!")

        # Scroll to the "Next" button to ensure it's in view
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)

        # Use JavaScript to click the "Next" button
        driver.execute_script("arguments[0].click();", next_button)
        print("Clicked the 'Next' button via JavaScript.")

        # Wait for the new page content to load
        WebDriverWait(driver, 10).until(
            EC.staleness_of(next_button)  # Wait for the button to become stale (indicating page refresh)
        )

        # Verify if the URL has changed or content has refreshed
        current_url_after_click = driver.current_url
        print(f"New URL after clicking 'Next': {current_url_after_click}")

        return current_url_after_click

    except Exception as e:
        print(f"Attempt to find 'Next' button failed: {e}")
        return None


# Example usage in a scraping loop
def scrape_multiple_pages(start_url, main_content_css, num_pages=None):
    current_url = start_url
    all_links = []
    page = 1

    while True:
        print(f"Scraping page {page}...")
        links = get_links_from_main_content(current_url, main_content_css)

        # Add the links from this page to the total list
        all_links.extend(links)
        print(f"Page {page} links extracted: {len(links)} links found.")

        # If a fixed number of pages is set and we reach the limit, stop
        if num_pages and page >= num_pages:
            print(f"Reached the limit of {num_pages} pages. Stopping.")
            break

        # Try to navigate to the next page using the enhanced next button detection
        current_url = click_next_page_button()  # The function will handle all cases automatically
        if not current_url:
            print(f"Stopping at page {page}. No further 'Next' button found.")
            break

        page += 1
        time.sleep(2)  # Optional: Additional delay to avoid anti-scraping mechanisms

    return all_links


# Set the URL of the first page
start_url = "https://www.regione.sardegna.it/atti-bandi-archivi/atti-amministrativi/bandi?size=n_12_n&sort%5B0%5D%5Bfield%5D=dataPubblicazione&sort%5B0%5D%5Bdirection%5D=desc"

# CSS selector for the section containing the links
main_content_css = "#mainContent > div > div.min-vh-66 > div > div.search-body.row.mt-4 > div.results-container.col.mb-3 > div > div"

# Ask the user whether they want to scrape a limited number of pages or scrape until the last page
user_choice = input("Enter the number of pages to scrape or type 'all' to scrape until the last page: ")

# Determine the number of pages to scrape
if user_choice.lower() == 'all':
    num_pages = None  # Scrape until there are no more "Next" buttons
else:
    try:
        num_pages = int(user_choice)
    except ValueError:
        print("Invalid input. Defaulting to scraping all pages.")
        num_pages = None

# Start scraping
extracted_links = scrape_multiple_pages(start_url, main_content_css, num_pages)

# Output the extracted links
print("Extracted Links:")
for link in extracted_links:
    print(link)
print(f"Total links extracted: {len(extracted_links)}")

# Close the Selenium driver when done
driver.quit()
