import json
import time
import os
import multiprocessing
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options  # Import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import pandas as pd
import logging
import queue
from scraping.domain_explorer import DomainExplorer
from scraping.email_output import EmailOutput

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def extract_number(text):
    """
  Extracts a floating-point number from a string, handling different decimal separators.

  Args:
    text: The input string containing the number.

  Returns:
    A float representing the extracted number, or None if no number is found.
  """
    if not isinstance(text, str):
        return None  # or raise TypeError("Input must be a string")

    # Replace commas with periods (European decimal style)
    text = text.replace(",", ".")

    # Use a regular expression to find a floating-point number
    match = re.search(r"[-+]?\d*\.?\d+", text)  # Matches integers or floats

    if match:
        try:
            return float(match.group(0))
        except ValueError:
            return None  # Handle cases where the matched string isn't a valid float
    else:
        return None


def clean_text(text):
    return re.sub(r'[^\x00-\x7F]+', '',
                  text).strip()  # Keep only ASCII characters


def is_open_24_hours(hours_text):
    # Define a pattern to match opening hours like "9 AM–10 PM" or "9AM-10PM"
    time_pattern = r"(\d{1,2}[:\.]?\d{0,2}\s?(AM|PM)?\s?[-–]\s?(\d{1,2}[:\.]?\d{0,2}\s?(AM|PM)?))"

    # Split the schedule into lines and loop over them
    lines = hours_text.splitlines()

    # Check for each line
    for line in lines:
        # If there is a specific time range for the day, check if it indicates non-24 hour operation
        if re.search(time_pattern, line):
            times = line.split("–")
            if len(times) == 2:
                start_time = times[0].strip()
                end_time = times[1].strip()

                # If start time and end time don't indicate a 24-hour period, return False
                if start_time != "12 AM" or end_time != "12 AM":
                    return False
    return True


def write_to_csv():
    # Load JSON file
    json_file = "results/google_maps_results.json"  # Change to your JSON file path
    df = pd.read_json(json_file)

    # Convert to CSV
    csv_file = "results/google_maps_results.csv"
    df.to_csv(csv_file, index=False)

    logger.info(f"CSV file saved as {csv_file}")


def write_to_json(data, filename):
    """Writes the scraped data to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:  # Specify encoding
            json.dump(data, f, indent=4, ensure_ascii=False
                      )  # Pretty print and handle non-ASCII characters
        logger.info(f"Data written to {filename}")
    except Exception as e:
        logger.error(f"Error writing to JSON file: {e}")


def scrape_google_maps_urls(driver):
    # Google maps and results are successfully loaded
    # Initialize the output list
    urls = []

    while True:
        try:
            # Find all the businesses in the search results
            businesses = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'hfpxzc')))
        except Exception as e:
            # If no businesses are found, break the loop
            logger.error(f"An error occurred: {e}")
            logger.error(f"An error occurred: {e.__traceback__.tb_lineno}")
            break

        time.sleep(5)

        # Store the URLs of the businesses
        for business in businesses:
            url = business.get_attribute('href')
            if url not in urls:
                urls.append(url)

        logger.info(f"Loaded URL number: {str(len(urls))}")

        ###COMMENT
        #break

        ###UNCOMMENT
        # Scroll down to load more businesses
        driver.execute_script("arguments[0].scrollIntoView();", businesses[-1])
        time.sleep(5)
        try:
            # Check if new businesses are loaded
            new_businesses = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'hfpxzc')))
            if len(new_businesses) == len(businesses):
                # If no new businesses are loaded, break the loop
                break
        except Exception as e:
            # If an exception occurs, break the loop
            logger.error(f"An error occurred: {e}")
            logger.error(f"An error occurred: {e.__traceback__.tb_lineno}")
            break

    logger.info(f"Final scrolled URL number: {str(len(urls))}")
    return urls

def scrape_url_data(google_url, chrome_options):
    """Scrapes data from a single business URL."""
    try:
        driver = webdriver.Chrome(
            options=chrome_options)  #Pass the chrome_options
        logger.info(f"Scraping URL: {google_url}")
        driver.get(google_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")))

        # name of property
        try:
            name = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, 'lfPIob'))).text)

            if not name:
                name = "N/A"
        except Exception as e:
            name = "N/A"
            logger.error(f"name: {e}")

        # link to the hotels website
        try:
            urlHtml = driver.page_source
            soup = BeautifulSoup(urlHtml, 'html.parser')
            a = soup.find("a", "CsEnBe")
            
            if not a['href']:
                url = "N/A"
            else:
                url = a['href']

        except Exception as e:
            url = "N/A"
            logger.error(f"url: {e}")

        # address
        try:
            address = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-item-id*='address']"))).text)

            if not address:
                address = "N/A"
        except Exception as e:
            address = "N/A"
            logger.error(f"address: {e}")

        # phone number
        try:
            phone = clean_text(
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "[data-item-id*='phone']"))).text)

            if not phone:
                phone = "N/A"
        except Exception as e:
            phone = "N/A"
            logger.error(f"phone: {e}")

        # working hours
        try:
            workingHoursHtml = driver.page_source
            soup = BeautifulSoup(workingHoursHtml, 'html.parser')
            table = soup.find("table", class_="eK4R0e fontBodyMedium")

            # Check if table is found
            if table:
                # Find all <ul> tags with class "G8aQO"
                ul_elements = table.find_all("ul", class_="G8aQO")

                # Iterate through the ul elements and check for "closed"
                for ul in ul_elements:
                    if is_open_24_hours(ul.get_text().lower()):
                        workingHours = "Open 24 hours"
                    else:
                        workingHours = "Not open 24 hours"
            else:
                workingHours = "Open 24 hours"

            if not workingHours:
                workingHours = "Open 24 hours"
        except Exception as e:
            workingHours = "N/A"
            logger.error(f"workingHours: {e}")

        # Number of reviews
        try:
            numberOfReviewsElement = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'rqjGif')))

            # Using Selenium's get_attribute('outerHTML')
            numberOfReviewsHtml = numberOfReviewsElement.get_attribute(
                'outerHTML')
            soup = BeautifulSoup(numberOfReviewsHtml, 'html.parser')

            # Find all span elements
            spans = soup.find_all('span')

            # Extract the text content from each span and create a comma-separated string
            numberOfReviews = [span.text for span in spans]
            numberOfReviews = ", ".join(numberOfReviews)
            numberOfReviews = str(extract_number(numberOfReviews)).replace(
                ".", "")

            if not numberOfReviews:
                numberOfReviews = "N/A"
        except Exception as e:
            numberOfReviews = "N/A"
            logger.error(f"numberOfReviews: {e}")

        # average review score
        try:
            averageReviewScoreHtml = driver.page_source
            soup = BeautifulSoup(averageReviewScoreHtml, 'html.parser')
            div = soup.find("div", "fontDisplayLarge")

            averageReviewScore = div.text

            if not averageReviewScore:
                averageReviewScore = "N/A"
                print("averageReviewScore: " + averageReviewScore)
        except Exception as e:
            averageReviewScore = "N/A"
            logger.error(f"averageReviewScoreHtml: {e}")

        # checkInOutTimes
        try:
            checkInOutTimesElement = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "[data-item-id*='place-info-links:']")))
            checkInOutTimesHtml = checkInOutTimesElement.get_attribute(
                'outerHTML')

            soup = BeautifulSoup(checkInOutTimesHtml, 'html.parser')

            # Extract the text content from each span and create a comma-separated string
            spans = soup.find_all('span')
            checkInOutTimes = [span.text for span in spans]
            checkInOutTimes = [
                clean_text(string) for string in checkInOutTimes
            ]
            checkInOutTimes = [s for s in checkInOutTimes if s.strip()]
            checkInOutTimes = " - ".join(checkInOutTimes)

            if not checkInOutTimes:
                checkInOutTimes = "N/A"
        except Exception as e:
            checkInOutTimes = "N/A"
            logger.error(f"checkInOutTimes: {e}")

        # amenities
        try:
            amenities_element = WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'WKLD0c')))

            # Using Selenium's get_attribute('outerHTML')
            amenities_html = amenities_element.get_attribute('outerHTML')

            soup = BeautifulSoup(amenities_html, 'html.parser')
            spans = soup.find_all('span')

            # Extract the text content from each span and create a comma-separated string
            amenities = [clean_text(span.text) for span in spans]
            amenities = [s for s in amenities if s.strip()]
            amenities = ", ".join(amenities)

            if not amenities:
                amenities = "N/A"
        except Exception as e:
            amenities = "N/A"
            logger.error(f"amenities: {e}")

        # Number of OTAs
        try:
            # Wait for the "Prices" tab and click it
            price_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@class='hh2c6 ']")))
            price_tab.click()
            # Allow time for prices to load
            time.sleep(3)

            numberOfOTAsHtml = driver.page_source
            soup = BeautifulSoup(numberOfOTAsHtml, 'html.parser')

            # Find all span elements
            spans = soup.find_all('span', class_='QVR4f fontTitleSmall')

            # Extract the text content from each span and create a comma-separated string
            numberOfOTAs = [span.text for span in spans]
            numberOfOTAs = str(len(numberOfOTAs))

            if not numberOfOTAs:
                numberOfOTAs = "N/A"
        except Exception as e:
            numberOfOTAs = "N/A"
            logger.error(f"numberOfOTAs: {e}")

        # OTA links
        try:
            numberOfOTAsLinksHtml = driver.page_source
            soup = BeautifulSoup(numberOfOTAsLinksHtml, 'html.parser')

            # Find all a elements
            atags = soup.find_all('a', class_='SlvSdc co54Ed')
            hrefs = [a['href'] for a in atags if 'href' in a.attrs]

            # Extract the text content from each span and create a comma-separated string
            otaLinks = ", ".join(hrefs)

            if not otaLinks:
                otaLinks = "N/A"
        except Exception as e:
            otaLinks = "N/A"
            logger.error(f"otaLinks: {e}")

        # Calculate average OTA price
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            # Find all div elements
            divs = soup.find_all('div', class_='fontLabelMedium pUBf3e oiQUX')

            # Extract the text content from each span and create a comma-separated string
            averageOtaPrice = [extract_number(div.text) for div in divs]
            if len(averageOtaPrice) > 0:
                averageOtaPrice = str(
                    round(sum(averageOtaPrice) / len(averageOtaPrice), 2))
            else:
                averageOtaPrice = "N/A"

        except Exception as e:
            averageOtaPrice = "N/A"
            logger.error(f"averageOtaPrice: {e}")
            logger.error(f"averageOtaPrice: {e.__traceback__.tb_lineno}")

        # Social media links
        if url != "N/A":
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body")))

                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                # Define regex pattern for social media domains
                social_media_pattern = re.compile(
                    r"(facebook\.com|linkedin\.com|instagram\.com|youtube\.com|twitter\.com)"
                )

                # Find all <a> tags with social media links
                links = soup.find_all("a", href=social_media_pattern)

                # Extracted links
                socialMediaLinks = [link["href"] for link in links]
                socialMediaLinks = ", ".join(socialMediaLinks)

                if not socialMediaLinks:
                    socialMediaLinks = "N/A"
            except Exception as e:
                socialMediaLinks = "N/A"
                logger.error(f"socialMediaLinks: {e}")
                logger.error(f"socialMediaLinks: {__file__}")
                logger.error(f"socialMediaLinks: {e.__traceback__.tb_lineno}")
        else:
            socialMediaLinks = "N/A"

        driver.quit()  #Quit driver after usage

        logger.info(f"Finished scraping URL: {google_url}")

        return {
            "name": name,
            "phone": phone,
            "url": url,
            "googleMapsUrl": google_url,
            "address": address,
            "numberOfReviews": numberOfReviews,
            "averageReviewScore": averageReviewScore,
            "checkInOutTimes": checkInOutTimes,
            "amenities": amenities,
            "numberOfOTAs": numberOfOTAs,
            "otaLinks": otaLinks,
            "averageOtaPrice": averageOtaPrice,
            "socialMediaLinks": socialMediaLinks,
            "workingHours": workingHours,
            "emails": ""
        }

    except Exception as e:
        logger.error(f"Error scraping : {e}")
        logger.error(f"Error scraping : {__file__}")
        logger.error(f"Error scraping : {e.__traceback__.tb_lineno}")
        return None

def perform_email_scraping(website_urls, json_data):
    # Define two queues to work with. Set maxsize for the main queue
    domainqueue = queue.Queue(maxsize=5000)
    emailsqueue = queue.Queue()

    # Start our threads
    for _i in range(20):
        t = DomainExplorer(domainqueue, emailsqueue)
        t.daemon = True
        t.start()

    logger.info(f"Started {20} Threads")

    # Start our collector thread
    results_thread = EmailOutput(emailsqueue, json_data)
    results_thread.daemon = True
    results_thread.start()

    # Add domains to the queue from a context manager to save memory
    
    for domain in website_urls:
        domainqueue.put(domain)

    # Gracefully join our queues so that our threads can exit
    domainqueue.join()
    logger.info("Domains finished processing")
    emailsqueue.join()
    logger.info("Collector finished processing")

    # Write the updated data to the CSV file
    write_to_csv()

def perform_scraping(url=None,
                    search_query=None,
                     location=None,
                     radius=5000,
                     max_results=20):
    
    """Main scraping function."""
    global progress, scraped_data
    progress = 0  # Reset progress
    scraped_data = []  # Reset scraped data

    # Set up Chrome options for headless mode# Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    # Optionally, disable GPU if you encounter issues in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--log-level=1")
    chrome_options.add_argument("--lang=en-US")
    chrome_options.add_experimental_option(
        'prefs', {'intl.accept_languages': 'en,en_US'})
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    try:
        driver = webdriver.Chrome(
            options=chrome_options)  #Pass the chrome_options
    except Exception as e:
        logger.error(f"Error setting chrome: {e}")
        exit()

    # Build the Google Maps URL
    if location:
        # If location coordinates are provided, use them in the URL
        lat, lng = location
        maps_url = f"https://www.google.com/maps/search/{search_query}/@{lat},{lng},14z"
    elif search_query:
        # Otherwise just use the search query
        maps_url = f"https://www.google.com/maps/search/{search_query}"
    elif url:
        # Otherwise just use the search query
        maps_url = url
        
    logger.info(f"Opening Google Maps with URL: {maps_url}")
    driver.get(maps_url)

    try:
        urls = scrape_google_maps_urls(driver)
        write_to_json(urls, "results/google_maps_results_urls.json")

        num_processes = multiprocessing.cpu_count()
        logger.info(
            f"Processing {len(urls)} URLs with {num_processes} processes")

        with multiprocessing.Pool(processes=num_processes) as pool:
            # Map the scraping function to the URLs
            results = pool.starmap(
                scrape_url_data,
                [(google_url, chrome_options) for google_url in urls])  #Pass chrome_install one time

        # Filter out None results and format the output
        scraped_data = [result for result in results if result is not None]

        # Write the data to the JSON file
        write_to_json(scraped_data, "results/google_maps_results.json")

        # Read the JSON file
        with open("results/google_maps_results.json", 'r') as file:
            json_data = json.load(file)

        website_urls = []
        # Process each object in the array
        for record in json_data:
            if record['url'] != "N/A":
                website_urls.append(record['url'])
                
        perform_email_scraping(website_urls, json_data)

        return True
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        logger.error(f"An error occurred: {e.__traceback__.tb_lineno}")
        return False
    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    perform_scraping("https://www.google.com/maps/search/Hotels/@30.3739107,-86.5128753,12z/data=!3m1!4b1!4m4!2m3!5m2!5m1!1s2025-05-17?authuser=0&entry=ttu&g_ep=EgoyMDI1MDMwOC4wIKXMDSoASAFQAw%3D%3D")
